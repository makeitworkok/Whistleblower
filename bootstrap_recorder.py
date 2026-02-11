#!/usr/bin/env python3
"""Interactive, read-only bootstrap recorder for Whistleblower configs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright


DEFAULT_LOGIN = {
    "user_selector": "#username",
    "pass_selector": "#password",
    "submit_selector": "button[type='submit']",
    "success_selector": "body",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Record login/navigation interactions and generate a starter sites/*.json config."
    )
    parser.add_argument("--url", required=True, help="Starting login URL.")
    parser.add_argument(
        "--site-name",
        required=True,
        help="Friendly site name used for output file names and config `name`.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/bootstrap",
        help="Root directory for raw recorder artifacts. Default: data/bootstrap",
    )
    parser.add_argument(
        "--config-out",
        default=None,
        help="Optional explicit output path for generated config JSON. Default: sites/<site-name>.bootstrap.json",
    )
    parser.add_argument(
        "--steps-out",
        default=None,
        help="Optional explicit output path for suggested pre-click steps. Default: sites/<site-name>.steps.json",
    )
    parser.add_argument("--viewport-width", type=int, default=1920)
    parser.add_argument("--viewport-height", type=int, default=1080)
    parser.add_argument(
        "--ignore-https-errors",
        action="store_true",
        help="Ignore HTTPS cert errors while recording.",
    )
    parser.add_argument(
        "--record-video",
        action="store_true",
        help="Record session video to bootstrap output folder.",
    )
    return parser.parse_args()


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sanitize_name(value: str) -> str:
    safe = []
    for char in value.strip():
        if char.isalnum() or char in ("-", "_", "."):
            safe.append(char)
        else:
            safe.append("_")
    return "".join(safe) or "unnamed"


def event_init_script() -> str:
    # Records only structural interaction details; never sends typed values.
    return r"""
(() => {
  if (window.__wbRecorderInstalled) return;
  window.__wbRecorderInstalled = true;

  function cssSelector(el) {
    if (!el || !el.nodeType || el.nodeType !== 1) return null;
    if (el.id) return `#${el.id}`;

    const tag = (el.tagName || '').toLowerCase();
    if (!tag) return null;

    const className = (el.className || '').trim();
    if (className) {
      const first = className.split(/\s+/).find(Boolean);
      if (first) return `${tag}.${first}`;
    }

    const parent = el.parentElement;
    if (!parent) return tag;

    const siblings = Array.from(parent.children).filter((n) => n.tagName === el.tagName);
    if (siblings.length > 1) {
      const ix = siblings.indexOf(el) + 1;
      return `${tag}:nth-of-type(${ix})`;
    }
    return tag;
  }

  function safeText(el) {
    const text = ((el && (el.innerText || el.textContent)) || '').trim().replace(/\s+/g, ' ');
    return text.slice(0, 120);
  }

  function emit(payload) {
    const withMeta = {
      ...payload,
      url: window.location.href,
      ts_utc: new Date().toISOString()
    };
    if (typeof window.wbRecordEvent === 'function') {
      window.wbRecordEvent(withMeta);
    }
  }

  document.addEventListener('click', (ev) => {
    const el = ev.target instanceof Element ? ev.target : null;
    emit({
      type: 'click',
      selector: cssSelector(el),
      tag: el ? el.tagName : null,
      text: safeText(el)
    });
  }, true);

  document.addEventListener('dblclick', (ev) => {
    const el = ev.target instanceof Element ? ev.target : null;
    emit({
      type: 'dblclick',
      selector: cssSelector(el),
      tag: el ? el.tagName : null,
      text: safeText(el)
    });
  }, true);

  document.addEventListener('change', (ev) => {
    const el = ev.target instanceof HTMLInputElement || ev.target instanceof HTMLTextAreaElement || ev.target instanceof HTMLSelectElement
      ? ev.target
      : null;
    if (!el) return;
    let inputType = null;
    let valueLength = null;
    if (el instanceof HTMLInputElement) {
      inputType = el.type || 'text';
      valueLength = (el.value || '').length;
    } else if (el instanceof HTMLTextAreaElement) {
      inputType = 'textarea';
      valueLength = (el.value || '').length;
    } else {
      inputType = 'select';
      valueLength = (el.value || '').length;
    }
    emit({
      type: 'change',
      selector: cssSelector(el),
      tag: el.tagName,
      input_type: inputType,
      value_length: valueLength
    });
  }, true);
})();
"""


def infer_login_selectors(events: list[dict[str, Any]]) -> dict[str, str]:
    user_selector = DEFAULT_LOGIN["user_selector"]
    pass_selector = DEFAULT_LOGIN["pass_selector"]
    submit_selector = DEFAULT_LOGIN["submit_selector"]

    password_ix: int | None = None
    for ix, event in enumerate(events):
        if event.get("type") != "change":
            continue
        input_type = str(event.get("input_type") or "").lower()
        if input_type == "password":
            pass_selector = str(event.get("selector") or pass_selector)
            password_ix = ix
            break

    if password_ix is not None:
        for prior in range(password_ix - 1, -1, -1):
            event = events[prior]
            if event.get("type") != "change":
                continue
            input_type = str(event.get("input_type") or "").lower()
            if input_type in {"text", "email", "search", "textarea"}:
                user_selector = str(event.get("selector") or user_selector)
                break
        for later in range(password_ix + 1, min(password_ix + 16, len(events))):
            event = events[later]
            if event.get("type") in {"click", "dblclick"}:
                submit_selector = str(event.get("selector") or submit_selector)
                break

    return {
        "user_selector": user_selector,
        "pass_selector": pass_selector,
        "submit_selector": submit_selector,
        "success_selector": DEFAULT_LOGIN["success_selector"],
    }


def infer_watch_urls(start_url: str, events: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for event in events:
        if event.get("type") != "navigation" or not event.get("main_frame"):
            continue
        url = str(event.get("url") or "").strip()
        if not url or url == "about:blank" or url in seen:
            continue
        seen.add(url)
        ordered.append(url)

    if not ordered:
        return [start_url]
    return ordered


def build_step_suggestions(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    suggestions: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for event in events:
        event_type = str(event.get("type") or "")
        if event_type not in {"click", "dblclick"}:
            continue
        selector = str(event.get("selector") or "").strip()
        if not selector:
            continue
        key = (event_type, selector)
        if key in seen:
            continue
        seen.add(key)
        suggestions.append(
            {
                "selector": selector,
                "action": "dblclick" if event_type == "dblclick" else "click",
                "nth": 0,
                "wait_ms": 2000,
            }
        )
    return suggestions


def main() -> int:
    args = parse_args()
    if args.viewport_width < 1 or args.viewport_height < 1:
        raise SystemExit("ERROR: --viewport-width and --viewport-height must be >= 1.")

    site_name = sanitize_name(args.site_name)
    run_root = Path(args.output_dir) / site_name / utc_timestamp()
    run_root.mkdir(parents=True, exist_ok=False)

    config_out = Path(args.config_out) if args.config_out else Path("sites") / f"{site_name}.bootstrap.json"
    steps_out = Path(args.steps_out) if args.steps_out else Path("sites") / f"{site_name}.steps.json"

    events: list[dict[str, Any]] = []
    final_screenshot_path = run_root / "final.png"
    raw_events_path = run_root / "events.json"
    summary_path = run_root / "summary.json"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context_options: dict[str, Any] = {
            "ignore_https_errors": bool(args.ignore_https_errors),
            "viewport": {"width": args.viewport_width, "height": args.viewport_height},
        }
        if args.record_video:
            video_dir = run_root / "video"
            video_dir.mkdir(parents=True, exist_ok=True)
            context_options["record_video_dir"] = str(video_dir)
            context_options["record_video_size"] = {
                "width": args.viewport_width,
                "height": args.viewport_height,
            }
        context = browser.new_context(**context_options)

        def record_event(source: Any, payload: dict[str, Any]) -> None:
            frame_url = None
            try:
                frame = source.get("frame")
                if frame is not None:
                    frame_url = frame.url
            except Exception:
                frame_url = None
            events.append(
                {
                    **payload,
                    "frame_url": frame_url,
                }
            )

        context.expose_binding("wbRecordEvent", record_event)
        context.add_init_script(event_init_script())

        page: Page | None = context.new_page()

        def on_frame_navigated(frame: Any) -> None:
            events.append(
                {
                    "type": "navigation",
                    "url": frame.url,
                    "main_frame": frame == page.main_frame if page is not None else False,
                    "ts_utc": iso_utc_now(),
                }
            )

        page.on("framenavigated", on_frame_navigated)
        page.goto(args.url, wait_until="domcontentloaded", timeout=120000)

        print("")
        print("Recorder is running in a real browser window.")
        print("1) Perform login and navigation exactly as an operator would.")
        print("2) Do not trigger control changes (read-only workflow only).")
        print("3) Return here and press Enter to finish and write outputs.")
        input("Press Enter when finished...")

        page.screenshot(path=str(final_screenshot_path), full_page=False)

        if args.record_video and page.video is not None:
            page.close()
            page.video.save_as(str(run_root / "video" / "session.mp4"))
        else:
            page.close()

        context.close()
        browser.close()

    raw_events_path.write_text(json.dumps(events, indent=2), encoding="utf-8")

    inferred_login = infer_login_selectors(events)
    watch_urls = infer_watch_urls(args.url, events)
    watch = []
    for ix, url in enumerate(watch_urls[:8]):
        watch.append(
            {
                "name": f"target_{ix + 1}",
                "url": url,
                "root_selector": "body",
                "settle_ms": 10000,
                "screenshot_full_page": False,
            }
        )

    generated_config = {
        "name": site_name,
        "base_url": args.url,
        "ignore_https_errors": bool(args.ignore_https_errors),
        "login_attempts": 2,
        "viewport": {
            "width": args.viewport_width,
            "height": args.viewport_height,
        },
        "login": {
            "username": "REPLACE_ME",
            "password": "REPLACE_ME",
            "user_selector": inferred_login["user_selector"],
            "pass_selector": inferred_login["pass_selector"],
            "submit_selector": inferred_login["submit_selector"],
            "success_selector": inferred_login["success_selector"],
        },
        "watch": watch,
    }

    step_suggestions = {
        "site_name": site_name,
        "captured_at_utc": iso_utc_now(),
        "base_url": args.url,
        "suggested_pre_click_steps": build_step_suggestions(events),
        "notes": [
            "Review selectors before use; dynamic classes may need refinement.",
            "Copy selected steps into a target under watch[].pre_click_steps.",
            "Credentials are placeholders in generated config by design.",
        ],
        "artifacts": {
            "raw_events": str(raw_events_path),
            "final_screenshot": str(final_screenshot_path),
        },
    }

    config_out.parent.mkdir(parents=True, exist_ok=True)
    steps_out.parent.mkdir(parents=True, exist_ok=True)
    config_out.write_text(json.dumps(generated_config, indent=2), encoding="utf-8")
    steps_out.write_text(json.dumps(step_suggestions, indent=2), encoding="utf-8")

    summary = {
        "site_name": site_name,
        "config_out": str(config_out),
        "steps_out": str(steps_out),
        "artifacts_dir": str(run_root),
        "events_recorded": len(events),
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("")
    print("Bootstrap capture complete.")
    print(f"- Config scaffold: {config_out}")
    print(f"- Step suggestions: {steps_out}")
    print(f"- Raw artifacts: {run_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
