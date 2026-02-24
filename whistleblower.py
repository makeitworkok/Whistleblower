#!/usr/bin/env python3
# Copyright (c) 2025-2026 Chris Favre - MIT License
# See LICENSE file for full terms
"""Whistleblower: read-only BAS web UI capture tool."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.sync_api import BrowserContext, ElementHandle, Error, Page, TimeoutError, sync_playwright


@dataclass(frozen=True)
class WatchTarget:
    name: str
    url: str
    root_selector: str = "body"
    settle_ms: int | None = None
    pre_click_selector: str | None = None
    pre_click_wait_ms: int = 2000
    pre_click_steps: list[dict[str, Any]] | None = None
    screenshot_selector: str | None = None
    screenshot_full_page: bool = True


@dataclass(frozen=True)
class LoginConfig:
    username: str
    password: str
    user_selector: str
    pass_selector: str
    submit_selector: str
    success_selector: str


@dataclass(frozen=True)
class SiteConfig:
    name: str
    base_url: str
    ignore_https_errors: bool
    login_attempts: int
    viewport_width: int
    viewport_height: int
    login: LoginConfig
    watch: list[WatchTarget]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only BAS UI watchdog. Captures screenshots and DOM snapshots."
    )
    parser.add_argument("--config", required=True, help="Path to site config JSON file.")
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Output root for captured artifacts. Default: ./data",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=30000,
        help="Navigation/action timeout in milliseconds. Default: 30000",
    )
    parser.add_argument(
        "--settle-ms",
        type=int,
        default=5000,
        help="Additional wait time before capture after page/root selector is ready. Default: 5000",
    )
    parser.add_argument(
        "--post-login-wait-ms",
        type=int,
        default=10000,
        help="Additional wait after login before capture navigation. Default: 10000",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run browser in headed mode (useful for debugging).",
    )
    parser.add_argument(
        "--record-video",
        action="store_true",
        help="Record a video of the browser session and save it in the run output folder.",
    )
    parser.add_argument(
        "--video-width",
        type=int,
        default=None,
        help="Video width in pixels. Defaults to viewport width.",
    )
    parser.add_argument(
        "--video-height",
        type=int,
        default=None,
        help="Video height in pixels. Defaults to viewport height.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return resolve_env_placeholders(raw)
    except FileNotFoundError as exc:
        raise ValueError(f"Config file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in config {path}: {exc}") from exc


def require_keys(data: dict[str, Any], keys: list[str], context: str) -> None:
    missing = [key for key in keys if key not in data]
    if missing:
        raise ValueError(f"Missing keys in {context}: {', '.join(missing)}")


def resolve_env_placeholders(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: resolve_env_placeholders(v) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve_env_placeholders(v) for v in value]
    if isinstance(value, str):
        match = re.fullmatch(r"\$\{([A-Z0-9_]+)\}", value.strip())
        if match is None:
            return value
        env_key = match.group(1)
        env_value = os.getenv(env_key)
        if env_value is None:
            raise ValueError(f"Missing required environment variable: {env_key}")
        return env_value
    return value


def parse_site_config(raw: dict[str, Any]) -> SiteConfig:
    require_keys(raw, ["name", "base_url", "login", "watch"], "root config")
    login_raw = raw["login"]
    if not isinstance(login_raw, dict):
        raise ValueError("Config key `login` must be an object.")
    require_keys(
        login_raw,
        [
            "username",
            "password",
            "user_selector",
            "pass_selector",
            "submit_selector",
            "success_selector",
        ],
        "login config",
    )

    watch_raw = raw["watch"]
    if not isinstance(watch_raw, list) or len(watch_raw) == 0:
        raise ValueError("Config key `watch` must be a non-empty array.")

    watch: list[WatchTarget] = []
    for index, item in enumerate(watch_raw):
        if not isinstance(item, dict):
            raise ValueError(f"watch[{index}] must be an object.")
        require_keys(item, ["name", "url"], f"watch[{index}]")
        pre_click_wait_ms = int(item.get("pre_click_wait_ms", 2000))
        if pre_click_wait_ms < 0:
            raise ValueError(f"watch[{index}].pre_click_wait_ms must be >= 0.")
        target_settle_ms: int | None = None
        if "settle_ms" in item and item["settle_ms"] is not None:
            target_settle_ms = int(item["settle_ms"])
            if target_settle_ms < 0:
                raise ValueError(f"watch[{index}].settle_ms must be >= 0.")
        raw_steps = item.get("pre_click_steps")
        pre_click_steps: list[dict[str, Any]] | None = None
        if raw_steps is not None:
            if not isinstance(raw_steps, list):
                raise ValueError(f"watch[{index}].pre_click_steps must be an array.")
            pre_click_steps = []
            for step_index, step in enumerate(raw_steps):
                if not isinstance(step, dict):
                    raise ValueError(
                        f"watch[{index}].pre_click_steps[{step_index}] must be an object."
                    )
                require_keys(
                    step,
                    ["selector"],
                    f"watch[{index}].pre_click_steps[{step_index}]",
                )
                wait_ms = int(step.get("wait_ms", 2000))
                if wait_ms < 0:
                    raise ValueError(
                        f"watch[{index}].pre_click_steps[{step_index}].wait_ms must be >= 0."
                    )
                nth = int(step.get("nth", 0))
                if nth < 0:
                    raise ValueError(
                        f"watch[{index}].pre_click_steps[{step_index}].nth must be >= 0."
                    )
                action = str(step.get("action", "click")).lower()
                if action not in {"click", "dblclick"}:
                    raise ValueError(
                        f"watch[{index}].pre_click_steps[{step_index}].action must be "
                        "either `click` or `dblclick`."
                    )
                pre_click_steps.append(
                    {
                        "selector": str(step["selector"]),
                        "wait_ms": wait_ms,
                        "nth": nth,
                        "action": action,
                    }
                )
        watch.append(
            WatchTarget(
                name=str(item["name"]),
                url=str(item["url"]),
                root_selector=str(item.get("root_selector", "body")),
                settle_ms=target_settle_ms,
                pre_click_selector=(
                    str(item["pre_click_selector"])
                    if "pre_click_selector" in item and item["pre_click_selector"] is not None
                    else None
                ),
                pre_click_wait_ms=pre_click_wait_ms,
                pre_click_steps=pre_click_steps,
                screenshot_selector=(
                    str(item["screenshot_selector"])
                    if "screenshot_selector" in item and item["screenshot_selector"] is not None
                    else None
                ),
                screenshot_full_page=bool(item.get("screenshot_full_page", True)),
            )
        )

    login_attempts = int(raw.get("login_attempts", 1))
    if login_attempts < 1:
        raise ValueError("Config key `login_attempts` must be >= 1.")
    viewport_raw = raw.get("viewport", {})
    if viewport_raw is None:
        viewport_raw = {}
    if not isinstance(viewport_raw, dict):
        raise ValueError("Config key `viewport` must be an object when provided.")
    viewport_width = int(viewport_raw.get("width", 1280))
    viewport_height = int(viewport_raw.get("height", 720))
    if viewport_width < 1 or viewport_height < 1:
        raise ValueError("Config key `viewport.width` and `viewport.height` must be >= 1.")

    return SiteConfig(
        name=str(raw["name"]),
        base_url=str(raw["base_url"]),
        ignore_https_errors=bool(raw.get("ignore_https_errors", False)),
        login_attempts=login_attempts,
        viewport_width=viewport_width,
        viewport_height=viewport_height,
        login=LoginConfig(
            username=str(login_raw["username"]),
            password=str(login_raw["password"]),
            user_selector=str(login_raw["user_selector"]),
            pass_selector=str(login_raw["pass_selector"]),
            submit_selector=str(login_raw["submit_selector"]),
            success_selector=str(login_raw["success_selector"]),
        ),
        watch=watch,
    )


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def sanitize_name(value: str) -> str:
    safe = []
    for char in value.strip():
        if char.isalnum() or char in ("-", "_", "."):
            safe.append(char)
        else:
            safe.append("_")
    return "".join(safe) or "unnamed"


def make_run_dir(data_dir: Path, site_name: str) -> Path:
    run_dir = data_dir / sanitize_name(site_name) / utc_timestamp()
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def login(page: Page, cfg: SiteConfig, timeout_ms: int) -> None:
    page.goto(cfg.base_url, wait_until="domcontentloaded", timeout=timeout_ms)
    # Wait for any redirects to complete
    page.wait_for_load_state("networkidle", timeout=min(timeout_ms, 10000))

    def login_succeeded() -> bool:
        if page.locator(cfg.login.success_selector).first.is_visible():
            return True
        user_visible = page.locator(cfg.login.user_selector).first.is_visible()
        pass_visible = page.locator(cfg.login.pass_selector).first.is_visible()
        return (not user_visible and not pass_visible) and (page.url != cfg.base_url)

    def login_form_ready() -> bool:
        user = page.locator(cfg.login.user_selector).first
        password = page.locator(cfg.login.pass_selector).first
        return (
            user.is_visible()
            and user.is_enabled()
            and password.is_visible()
            and password.is_enabled()
        )

    def user_field_ready() -> bool:
        user = page.locator(cfg.login.user_selector).first
        try:
            is_vis = user.is_visible(timeout=2000)  # Short timeout for visibility check
        except TimeoutError:
            is_vis = False
        if is_vis:
            print(f"DEBUG: user_selector '{cfg.login.user_selector}' is visible, will attempt fill")
            return True
        return False

    def pass_field_ready() -> bool:
        password = page.locator(cfg.login.pass_selector).first
        try:
            return password.is_visible(timeout=2000)
        except TimeoutError:
            return False

    last_error: TimeoutError | None = None
    for attempt in range(1, cfg.login_attempts + 1):
        ready_deadline = time.monotonic() + (timeout_ms / 1000)
        while time.monotonic() < ready_deadline:
            if login_succeeded():
                return
            # Support multi-step or single-step login
            if login_form_ready() or user_field_ready() or pass_field_ready():
                break
            page.wait_for_timeout(500)
        else:
            last_error = TimeoutError(
                f"Login attempt {attempt}/{cfg.login_attempts} could not find an enabled login form."
            )
            if attempt < cfg.login_attempts:
                continue
            break

        form_timeout_ms = min(timeout_ms, 10000)
        
        # Fill username if available
        if user_field_ready():
            user = page.locator(cfg.login.user_selector).first
            user.fill(cfg.login.username, timeout=form_timeout_ms)
            
            # If password not available yet, try submitting username first
            if not pass_field_ready():
                try:
                    submit = page.locator(cfg.login.submit_selector).first
                    if submit.is_visible():
                        submit.click(timeout=form_timeout_ms)
                except (TimeoutError, Error):
                    user.press("Enter", timeout=form_timeout_ms)
                
                # Wait for password field to appear (multi-step login)
                pass_deadline = time.monotonic() + (timeout_ms / 1000)
                while time.monotonic() < pass_deadline:
                    if login_succeeded():
                        return
                    if pass_field_ready():
                        break
                    page.wait_for_timeout(500)
        
        # Fill password if available
        if pass_field_ready():
            password = page.locator(cfg.login.pass_selector).first
            try:
                password.fill(cfg.login.password, timeout=form_timeout_ms)
            except TimeoutError:
                # Try force-filling if it's disabled
                password.fill(cfg.login.password, timeout=form_timeout_ms, force=True)
            try:
                submit = page.locator(cfg.login.submit_selector).first
                if submit.is_visible(timeout=2000):
                    submit.click(timeout=form_timeout_ms)
            except (TimeoutError, Error):
                password.press("Enter", timeout=form_timeout_ms)

        attempt_deadline = time.monotonic() + (timeout_ms / 1000)
        while time.monotonic() < attempt_deadline:
            if login_succeeded():
                return
            page.wait_for_timeout(500)

        last_error = TimeoutError(
            f"Login attempt {attempt}/{cfg.login_attempts} did not reach "
            f"`{cfg.login.success_selector}`."
        )
        if attempt < cfg.login_attempts:
            page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
    if last_error is not None:
        raise last_error
    raise TimeoutError("Login failed before success selector check.")


def login_form_ready(page: Page, cfg: SiteConfig) -> bool:
    controls = find_login_controls(page, cfg)
    return controls is not None


def login_form_present(page: Page, cfg: SiteConfig) -> bool:
    selectors = [
        cfg.login.user_selector,
        cfg.login.pass_selector,
        "input[type='password']",
    ]
    for selector in selectors:
        for element in page.query_selector_all(selector):
            if element.is_visible():
                return True
    return False


def submit_login(page: Page, cfg: SiteConfig, timeout_ms: int) -> None:
    controls = find_login_controls(page, cfg)
    if controls is None:
        raise TimeoutError("Enabled login controls are not available on the page.")

    user, password, submit = controls
    form_timeout_ms = min(timeout_ms, 10000)
    user.fill(cfg.login.username, timeout=form_timeout_ms)
    password.fill(cfg.login.password, timeout=form_timeout_ms)
    try:
        submit.click(timeout=form_timeout_ms)
    except (TimeoutError, Error):
        # Some BAS login forms submit on Enter and may not expose a stable submit control.
        password.press("Enter", timeout=form_timeout_ms)


def first_visible_enabled(
    page: Page, selector: str
) -> ElementHandle | None:
    for element in page.query_selector_all(selector):
        if element.is_visible() and element.is_enabled():
            return element
    return None


def button_text(element: ElementHandle) -> str:
    text = (element.inner_text() or "").strip()
    if text:
        return text
    value = element.get_attribute("value")
    return (value or "").strip()


def find_login_controls(
    page: Page, cfg: SiteConfig
) -> tuple[ElementHandle, ElementHandle, ElementHandle] | None:
    user = first_visible_enabled(page, cfg.login.user_selector)
    if user is None:
        user = first_visible_enabled(page, "input[type='text'],input[type='email']")

    password = first_visible_enabled(page, cfg.login.pass_selector)
    if password is None:
        password = first_visible_enabled(page, "input[type='password']")

    submit = first_visible_enabled(page, cfg.login.submit_selector)
    if submit is None:
        for selector in ("button", "input[type='button']", "input[type='submit']"):
            for element in page.query_selector_all(selector):
                if not element.is_visible() or not element.is_enabled():
                    continue
                if re.search(r"log\\s*in", button_text(element), re.IGNORECASE):
                    submit = element
                    break
            if submit is not None:
                break

    if user is None or password is None:
        return None
    if submit is None:
        # Some BAS login pages submit via Enter key and expose no stable submit control.
        submit = password
    return (user, password, submit)


def ensure_authenticated(page: Page, cfg: SiteConfig, timeout_ms: int) -> None:
    if not login_form_present(page, cfg):
        return

    last_error: TimeoutError | None = None
    for attempt in range(1, cfg.login_attempts + 1):
        ready_deadline = time.monotonic() + (timeout_ms / 1000)
        while time.monotonic() < ready_deadline:
            controls = find_login_controls(page, cfg)
            if controls is not None:
                break
            if not login_form_present(page, cfg):
                return
            page.wait_for_timeout(500)
        else:
            last_error = TimeoutError(
                f"In-app login attempt {attempt}/{cfg.login_attempts} could not find enabled login controls."
            )
            continue

        submit_login(page, cfg, timeout_ms)
        deadline = time.monotonic() + (timeout_ms / 1000)
        while time.monotonic() < deadline:
            if page.locator(cfg.login.success_selector).first.is_visible():
                return
            if not login_form_present(page, cfg):
                return
            page.wait_for_timeout(500)

        last_error = TimeoutError(
            f"In-app login attempt {attempt}/{cfg.login_attempts} did not complete."
        )

    if last_error is not None:
        raise last_error


def wait_for_selector_with_auth_checks(
    page: Page,
    cfg: SiteConfig,
    selector: str,
    timeout_ms: int,
    poll_ms: int = 2000,
) -> None:
    deadline = time.monotonic() + (timeout_ms / 1000)
    while True:
        remaining_ms = int((deadline - time.monotonic()) * 1000)
        if remaining_ms <= 0:
            page.wait_for_selector(selector, timeout=1)
            return
        try:
            page.wait_for_selector(selector, timeout=min(poll_ms, remaining_ms))
            return
        except TimeoutError:
            ensure_authenticated(page, cfg, timeout_ms)


def extract_dom_snapshot(page: Page, root_selector: str) -> dict[str, Any]:
    payload = page.evaluate(
        """(rootSelector) => {
            const root = document.querySelector(rootSelector) || document.body;
            const text = root.innerText || "";
            const valueElements = Array.from(
              root.querySelectorAll("input,select,textarea,[aria-checked],[aria-valuenow],[data-state]")
            );
            const states = valueElements.slice(0, 3000).map((el) => ({
              tag: el.tagName,
              id: el.id || null,
              name: el.getAttribute("name"),
              type: el.getAttribute("type"),
              class: el.className || null,
              text: (el.innerText || "").slice(0, 1000),
              value: ("value" in el) ? el.value : null,
              checked: ("checked" in el) ? !!el.checked : null,
              ariaChecked: el.getAttribute("aria-checked"),
              ariaValueNow: el.getAttribute("aria-valuenow"),
              dataState: el.getAttribute("data-state")
            }));
            return {
              title: document.title || "",
              url: window.location.href,
              rootSelector,
              rootTag: root.tagName,
              text,
              states
            };
        }""",
        root_selector,
    )
    return payload


def wait_for_target_ready(page: Page, cfg: SiteConfig, root_selector: str, timeout_ms: int) -> None:
    deadline = time.monotonic() + (timeout_ms / 1000)
    last_state: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        ensure_authenticated(page, cfg, timeout_ms)
        state = page.evaluate(
            """(selector) => {
                const root = document.querySelector(selector);
                const title = (document.title || "").trim().toLowerCase();
                const readyState = document.readyState || "";
                if (!root) {
                  return {
                    ready: false,
                    reason: "root_missing",
                    readyState,
                    title
                  };
                }
                const style = window.getComputedStyle(root);
                const rect = root.getBoundingClientRect();
                const text = (root.innerText || "").trim();
                const hasVisual = !!root.querySelector("canvas,svg,img,video,iframe,object,embed");
                const titleReady = title !== "loading" && title !== "loading...";
                const rootVisible = style.display !== "none" && style.visibility !== "hidden";
                const rootSized = rect.width > 200 && rect.height > 120;
                const contentReady = text.length > 20 || hasVisual;
                const domReady = readyState === "complete" || readyState === "interactive";
                return {
                  ready: titleReady && rootVisible && rootSized && contentReady && domReady,
                  reason: "pending",
                  readyState,
                  title,
                  textLength: text.length,
                  hasVisual,
                  width: rect.width,
                  height: rect.height
                };
            }""",
            root_selector,
        )
        if state.get("ready"):
            return
        last_state = state
        page.wait_for_timeout(500)
    raise TimeoutError(f"Timed out waiting for rendered target content: {last_state}")


def sleep_with_auth_checks(
    page: Page,
    cfg: SiteConfig,
    total_ms: int,
    timeout_ms: int,
    chunk_ms: int = 3000,
) -> None:
    remaining_ms = max(0, total_ms)
    while remaining_ms > 0:
        this_chunk = min(chunk_ms, remaining_ms)
        page.wait_for_timeout(this_chunk)
        ensure_authenticated(page, cfg, timeout_ms)
        remaining_ms -= this_chunk


def goto_with_hash_abort_tolerance(page: Page, url: str, timeout_ms: int) -> None:
    attempts = 2 if "#" in url else 1
    for _ in range(attempts):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        except Error as exc:
            message = str(exc)
            if "net::ERR_ABORTED" not in message:
                raise
        if page.url == url:
            return
        page.wait_for_timeout(500)


def write_capture_artifacts(
    page: Page,
    target: WatchTarget,
    output_dir: Path,
    started_at_utc: str,
    readiness_error: str | None = None,
) -> None:
    page_dir = output_dir / sanitize_name(target.name)
    page_dir.mkdir(parents=True, exist_ok=True)

    screenshot_path = page_dir / "screenshot.png"
    dom_path = page_dir / "dom.json"
    meta_path = page_dir / "meta.json"

    if target.screenshot_selector:
        page.wait_for_selector(target.screenshot_selector, timeout=10000)
        page.locator(target.screenshot_selector).first.screenshot(path=str(screenshot_path))
    else:
        page.screenshot(path=str(screenshot_path), full_page=target.screenshot_full_page)
    dom_snapshot = extract_dom_snapshot(page, target.root_selector)
    dom_path.write_text(json.dumps(dom_snapshot, indent=2), encoding="utf-8")

    meta = {
        "captured_at_utc": started_at_utc,
        "target_name": target.name,
        "target_url": target.url,
        "root_selector": target.root_selector,
        "title": dom_snapshot.get("title", ""),
        "url_after_navigation": dom_snapshot.get("url", ""),
        "artifacts": {
            "screenshot": screenshot_path.name,
            "dom": dom_path.name,
            "meta": meta_path.name,
        },
        "readiness_error": readiness_error,
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def capture_target(
    page: Page,
    cfg: SiteConfig,
    target: WatchTarget,
    run_dir: Path,
    timeout_ms: int,
    settle_ms: int,
    started_at_utc: str,
) -> None:
    if page.url != target.url:
        goto_with_hash_abort_tolerance(page, target.url, timeout_ms)
    ensure_authenticated(page, cfg, timeout_ms)

    if target.pre_click_steps:
        for step in target.pre_click_steps:
            step_selector = str(step["selector"])
            step_wait_ms = int(step.get("wait_ms", 2000))
            step_nth = int(step.get("nth", 0))
            step_action = str(step.get("action", "click")).lower()
            wait_for_selector_with_auth_checks(page, cfg, step_selector, timeout_ms)
            target_locator = page.locator(step_selector).nth(step_nth)
            if step_action == "dblclick":
                target_locator.dblclick(timeout=timeout_ms)
            else:
                target_locator.click(timeout=timeout_ms)
            if step_wait_ms > 0:
                sleep_with_auth_checks(page, cfg, step_wait_ms, timeout_ms)
            ensure_authenticated(page, cfg, timeout_ms)
    elif target.pre_click_selector:
        wait_for_selector_with_auth_checks(page, cfg, target.pre_click_selector, timeout_ms)
        page.locator(target.pre_click_selector).first.click(timeout=timeout_ms)
        if target.pre_click_wait_ms > 0:
            sleep_with_auth_checks(page, cfg, target.pre_click_wait_ms, timeout_ms)
        ensure_authenticated(page, cfg, timeout_ms)

    wait_for_selector_with_auth_checks(page, cfg, target.root_selector, timeout_ms)
    target_settle_ms = target.settle_ms if target.settle_ms is not None else settle_ms
    if target_settle_ms > 0:
        sleep_with_auth_checks(page, cfg, target_settle_ms, timeout_ms)
    ensure_authenticated(page, cfg, timeout_ms)
    wait_for_selector_with_auth_checks(page, cfg, target.root_selector, timeout_ms)
    readiness_error: str | None = None
    try:
        wait_for_target_ready(page, cfg, target.root_selector, timeout_ms)
    except TimeoutError as first_error:
        # Some hash-routed BAS UIs get stuck on "loading..." on the first attempt.
        # Reload once and re-open the target URL before failing.
        goto_with_hash_abort_tolerance(page, cfg.base_url, timeout_ms)
        ensure_authenticated(page, cfg, timeout_ms)
        goto_with_hash_abort_tolerance(page, target.url, timeout_ms)
        wait_for_selector_with_auth_checks(page, cfg, target.root_selector, timeout_ms)
        if target_settle_ms > 0:
            sleep_with_auth_checks(page, cfg, target_settle_ms, timeout_ms)
        ensure_authenticated(page, cfg, timeout_ms)
        wait_for_selector_with_auth_checks(page, cfg, target.root_selector, timeout_ms)
        try:
            wait_for_target_ready(page, cfg, target.root_selector, timeout_ms)
        except TimeoutError as retry_error:
            readiness_error = f"{first_error} | retry_failed: {retry_error}"
    write_capture_artifacts(
        page=page,
        target=target,
        output_dir=run_dir,
        started_at_utc=started_at_utc,
        readiness_error=readiness_error,
    )


def run(
    cfg: SiteConfig,
    data_dir: Path,
    timeout_ms: int,
    settle_ms: int,
    post_login_wait_ms: int,
    headed: bool,
    record_video: bool,
    video_width: int | None,
    video_height: int | None,
) -> Path:
    run_dir = make_run_dir(data_dir=data_dir, site_name=cfg.name)
    started_at_utc = datetime.now(timezone.utc).isoformat()
    with sync_playwright() as p:
        launch_args: dict[str, Any] = {"headless": not headed}
        if not headed:
            # Use full Chromium in headless mode; some BAS graphics fail on headless-shell.
            launch_args["channel"] = "chromium"
        browser = p.chromium.launch(**launch_args)
        context_options: dict[str, Any] = {
            "ignore_https_errors": cfg.ignore_https_errors,
            "viewport": {"width": cfg.viewport_width, "height": cfg.viewport_height},
        }
        if record_video:
            resolved_video_width = video_width if video_width is not None else cfg.viewport_width
            resolved_video_height = video_height if video_height is not None else cfg.viewport_height
            video_dir = run_dir / "video"
            video_dir.mkdir(parents=True, exist_ok=True)
            context_options["record_video_dir"] = str(video_dir)
            context_options["record_video_size"] = {
                "width": resolved_video_width,
                "height": resolved_video_height,
            }
        context = browser.new_context(**context_options)
        try:
            active_page: Page | None = context.new_page()
            try:
                login(active_page, cfg, timeout_ms=timeout_ms)
                if post_login_wait_ms > 0:
                    sleep_with_auth_checks(active_page, cfg, post_login_wait_ms, timeout_ms)
                    ensure_authenticated(active_page, cfg, timeout_ms)

                for target in cfg.watch:
                    capture_target(
                        page=active_page,
                        cfg=cfg,
                        target=target,
                        run_dir=run_dir,
                        timeout_ms=timeout_ms,
                        settle_ms=settle_ms,
                        started_at_utc=started_at_utc,
                    )
            finally:
                if active_page is not None:
                    page_video = active_page.video if record_video else None
                    active_page.close()
                    if page_video is not None:
                        page_video.save_as(str(run_dir / "video" / "session.mp4"))
        finally:
            context.close()
            browser.close()
    return run_dir


def run_capture(
    config_path: str | Path,
    data_dir: str | Path = "data",
    timeout_ms: int = 30000,
    settle_ms: int = 5000,
    post_login_wait_ms: int = 10000,
    headed: bool = False,
    record_video: bool = False,
    video_width: int | None = None,
    video_height: int | None = None,
) -> dict[str, Any]:
    """
    Run a capture session on a configured site.
    
    Args:
        config_path: Path to site config JSON file
        data_dir: Output root for captured artifacts
        timeout_ms: Navigation/action timeout in milliseconds
        settle_ms: Additional wait time before capture after page is ready
        post_login_wait_ms: Additional wait after login before capture navigation
        headed: Run browser in headed mode (visible)
        record_video: Record a video of the browser session
        video_width: Video width in pixels (defaults to viewport width)
        video_height: Video height in pixels (defaults to viewport height)
    
    Returns:
        Dictionary with run_dir path and capture summary
    """
    config_path = Path(config_path)
    data_dir = Path(data_dir)

    if video_width is not None and video_width < 1:
        raise ValueError("`video_width` must be >= 1.")
    if video_height is not None and video_height < 1:
        raise ValueError("`video_height` must be >= 1.")

    cfg = parse_site_config(load_json(config_path))
    run_dir = run(
        cfg=cfg,
        data_dir=data_dir,
        timeout_ms=timeout_ms,
        settle_ms=settle_ms,
        post_login_wait_ms=post_login_wait_ms,
        headed=headed,
        record_video=record_video,
        video_width=video_width,
        video_height=video_height,
    )
    
    return {
        "run_dir": str(run_dir),
        "site_name": cfg.name,
        "targets_captured": len(cfg.watch),
    }


def main() -> int:
    """CLI entry point for whistleblower capture."""
    args = parse_args()
    try:
        result = run_capture(
            config_path=args.config,
            data_dir=args.data_dir,
            timeout_ms=args.timeout_ms,
            settle_ms=args.settle_ms,
            post_login_wait_ms=args.post_login_wait_ms,
            headed=args.headed,
            record_video=args.record_video,
            video_width=args.video_width,
            video_height=args.video_height,
        )
        print(f"Capture completed: {result['run_dir']}")
        return 0
    except (ValueError, TimeoutError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"UNHANDLED ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
