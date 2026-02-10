#!/usr/bin/env python3
"""Whistleblower: read-only BAS web UI capture tool."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.sync_api import BrowserContext, Page, TimeoutError, sync_playwright


@dataclass(frozen=True)
class WatchTarget:
    name: str
    url: str
    root_selector: str = "body"


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
        "--headed",
        action="store_true",
        help="Run browser in headed mode (useful for debugging).",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Config file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in config {path}: {exc}") from exc


def require_keys(data: dict[str, Any], keys: list[str], context: str) -> None:
    missing = [key for key in keys if key not in data]
    if missing:
        raise ValueError(f"Missing keys in {context}: {', '.join(missing)}")


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
        watch.append(
            WatchTarget(
                name=str(item["name"]),
                url=str(item["url"]),
                root_selector=str(item.get("root_selector", "body")),
            )
        )

    return SiteConfig(
        name=str(raw["name"]),
        base_url=str(raw["base_url"]),
        ignore_https_errors=bool(raw.get("ignore_https_errors", False)),
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
    page.locator(cfg.login.user_selector).fill(cfg.login.username, timeout=timeout_ms)
    page.locator(cfg.login.pass_selector).fill(cfg.login.password, timeout=timeout_ms)
    page.locator(cfg.login.submit_selector).click(timeout=timeout_ms)
    page.locator(cfg.login.success_selector).wait_for(timeout=timeout_ms)


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


def write_capture_artifacts(
    page: Page, target: WatchTarget, output_dir: Path, started_at_utc: str
) -> None:
    page_dir = output_dir / sanitize_name(target.name)
    page_dir.mkdir(parents=True, exist_ok=True)

    screenshot_path = page_dir / "screenshot.png"
    dom_path = page_dir / "dom.json"
    meta_path = page_dir / "meta.json"

    page.screenshot(path=str(screenshot_path), full_page=True)
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
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def capture_target(
    context: BrowserContext,
    target: WatchTarget,
    run_dir: Path,
    timeout_ms: int,
    settle_ms: int,
    started_at_utc: str,
) -> None:
    page = context.new_page()
    try:
        page.goto(target.url, wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_selector(target.root_selector, timeout=timeout_ms)
        if settle_ms > 0:
            page.wait_for_timeout(settle_ms)
        write_capture_artifacts(
            page=page,
            target=target,
            output_dir=run_dir,
            started_at_utc=started_at_utc,
        )
    finally:
        page.close()


def run(
    cfg: SiteConfig,
    data_dir: Path,
    timeout_ms: int,
    settle_ms: int,
    headed: bool,
) -> Path:
    run_dir = make_run_dir(data_dir=data_dir, site_name=cfg.name)
    started_at_utc = datetime.now(timezone.utc).isoformat()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headed)
        context = browser.new_context(ignore_https_errors=cfg.ignore_https_errors)
        try:
            login_page = context.new_page()
            try:
                login(login_page, cfg, timeout_ms=timeout_ms)
            finally:
                login_page.close()

            for target in cfg.watch:
                capture_target(
                    context=context,
                    target=target,
                    run_dir=run_dir,
                    timeout_ms=timeout_ms,
                    settle_ms=settle_ms,
                    started_at_utc=started_at_utc,
                )
        finally:
            context.close()
            browser.close()
    return run_dir


def main() -> int:
    args = parse_args()
    config_path = Path(args.config)
    data_dir = Path(args.data_dir)

    try:
        cfg = parse_site_config(load_json(config_path))
        run_dir = run(
            cfg=cfg,
            data_dir=data_dir,
            timeout_ms=args.timeout_ms,
            settle_ms=args.settle_ms,
            headed=args.headed,
        )
    except (ValueError, TimeoutError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"UNHANDLED ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Capture completed: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
