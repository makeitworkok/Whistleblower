#!/usr/bin/env python3
# Copyright (c) 2025-2026 Chris Favre - MIT License
# See LICENSE file for full terms
"""Tree spider: read-only auto-exploration of BAS web UIs."""

from __future__ import annotations

import argparse
import json
import sys
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright


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


def is_same_domain(url: str, base_url: str) -> bool:
    """Check if a URL belongs to the same domain as the base URL."""
    try:
        base_parsed = urlparse(base_url)
        url_parsed = urlparse(url)
        return (
            url_parsed.scheme in ("http", "https")
            and url_parsed.netloc == base_parsed.netloc
        )
    except Exception:
        return False


def normalize_url(url: str) -> str:
    """Normalize URL for deduplication."""
    try:
        parsed = urlparse(url)
        # Preserve fragment for SPA hash routing (common in BAS UIs)
        normalized = parsed._replace(
            scheme=parsed.scheme.lower(),
            netloc=parsed.netloc.lower(),
        ).geturl()
        return normalized
    except Exception:
        return url


def extract_links(page: Page, base_url: str, nav_selectors: list[str]) -> list[str]:
    """Extract navigation links from the current page."""
    links: list[str] = []
    seen: set[str] = set()

    for selector in nav_selectors:
        try:
            elements = page.query_selector_all(selector)
            for el in elements:
                try:
                    href = el.get_attribute("href")
                    if not href or href.startswith(("javascript:", "mailto:", "tel:")):
                        continue
                    full_url = urljoin(page.url, href)
                    normalized = normalize_url(full_url)
                    parsed = urlparse(normalized)
                    if parsed.scheme not in ("http", "https"):
                        continue
                    if normalized not in seen:
                        seen.add(normalized)
                        links.append(normalized)
                except Exception:
                    continue
        except Exception:
            continue

    return links


@dataclass
class PageResult:
    url: str
    title: str
    depth: int
    status: str  # "ok", "error", "timeout", "bad_link"
    error: str | None = None
    screenshot_path: str | None = None
    links_found: list[str] = field(default_factory=list)
    parent_url: str | None = None


def run_spider(
    url: str,
    output_dir: str = "data/spider",
    site_name: str = "spider",
    config_path: str | None = None,
    max_depth: int = 3,
    max_pages: int = 50,
    timeout_ms: int = 30000,
    viewport_width: int = 1920,
    viewport_height: int = 1080,
    ignore_https_errors: bool = False,
    take_screenshots: bool = True,
    browser_type: str = "chromium",
    same_domain_only: bool = True,
    nav_selectors: list[str] | None = None,
    stop_event: threading.Event | None = None,
    log_callback: Any = None,
) -> dict[str, Any]:
    """
    Auto-explore a BAS website by traversing navigation links.

    Args:
        url: Starting URL to explore
        output_dir: Root directory for spider output
        site_name: Friendly name for output directories
        config_path: Optional path to site config JSON (for authenticated sites)
        max_depth: Maximum link depth to traverse (default: 3)
        max_pages: Maximum total pages to visit (default: 50)
        timeout_ms: Navigation timeout in milliseconds (default: 30000)
        viewport_width: Browser viewport width
        viewport_height: Browser viewport height
        ignore_https_errors: Ignore HTTPS certificate errors
        take_screenshots: Take screenshots of each page
        browser_type: Browser to use (chromium, firefox, webkit)
        same_domain_only: Only follow links on the same domain
        nav_selectors: CSS selectors for navigation links (default: ["a[href]"])
        stop_event: Optional threading.Event to signal early stop
        log_callback: Optional callable(str) for progress messages

    Returns:
        Dictionary with spider results summary
    """
    def _log(msg: str) -> None:
        print(msg, flush=True)
        if log_callback is not None:
            log_callback(msg)

    if nav_selectors is None:
        nav_selectors = ["a[href]"]

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    site_name = sanitize_name(site_name)
    run_root = Path(output_dir) / site_name / utc_timestamp()
    run_root.mkdir(parents=True, exist_ok=True)
    screenshots_dir = run_root / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    results: list[PageResult] = []
    bad_links: list[dict[str, Any]] = []

    # Optionally load site config for authentication
    login_config = None
    if config_path:
        try:
            import whistleblower
            raw = whistleblower.load_json(Path(config_path))
            login_config = whistleblower.parse_site_config(raw)
        except Exception as exc:
            _log(f"Warning: Could not load config {config_path}: {exc}")

    with sync_playwright() as p:
        # Launch browser
        browser = None
        if browser_type == "firefox":
            browser = p.firefox.launch(headless=False)
        elif browser_type == "webkit":
            browser = p.webkit.launch(headless=False)
        else:  # chromium (default) - includes Edge on Windows
            if sys.platform == "win32":
                for channel in ["msedge", None]:
                    try:
                        if channel:
                            browser = p.chromium.launch(headless=False, channel=channel)
                        else:
                            browser = p.chromium.launch(headless=False)
                        break
                    except Exception:
                        continue
                if browser is None:
                    raise RuntimeError(
                        "Could not launch browser. Please install Edge or run: "
                        "py -m playwright install chromium"
                    )
            else:
                browser = p.chromium.launch(headless=False)

        context_options: dict[str, Any] = {
            "ignore_https_errors": bool(ignore_https_errors),
            "viewport": {"width": viewport_width, "height": viewport_height},
        }
        context = browser.new_context(**context_options)
        page: Page = context.new_page()

        try:
            # Perform login if site config was provided
            if login_config is not None:
                try:
                    import whistleblower
                    whistleblower.login(page, login_config, timeout_ms=timeout_ms)
                    _log("Login successful.")
                except Exception as exc:
                    _log(f"Warning: Login failed: {exc}")

            # BFS traversal
            queue: deque[tuple[str, int, str | None]] = deque()
            queue.append((url, 0, None))
            visited: set[str] = set()
            visited.add(normalize_url(url))

            while queue and len(results) < max_pages:
                if stop_event is not None and stop_event.is_set():
                    _log("Spider stopped by user.")
                    break

                current_url, depth, parent_url = queue.popleft()
                _log(
                    f"[{len(results) + 1}/{max_pages}] "
                    f"depth={depth}: {current_url}"
                )

                result = PageResult(
                    url=current_url,
                    title="",
                    depth=depth,
                    status="ok",
                    parent_url=parent_url,
                )

                try:
                    response = page.goto(
                        current_url,
                        wait_until="domcontentloaded",
                        timeout=timeout_ms,
                    )

                    # Check HTTP status for bad link detection
                    if response is not None and response.status >= 400:
                        result.status = "bad_link"
                        result.error = f"HTTP {response.status}"
                        bad_links.append(
                            {
                                "url": current_url,
                                "error": result.error,
                                "parent_url": parent_url,
                                "depth": depth,
                            }
                        )

                    # Let the page render briefly
                    page.wait_for_timeout(1000)

                    # Capture title
                    try:
                        result.title = page.title()
                    except Exception:
                        result.title = ""

                    # Screenshot
                    if take_screenshots and result.status != "bad_link":
                        safe_name = sanitize_name(current_url[:60])
                        screenshot_filename = f"{len(results):04d}_{safe_name}.png"
                        screenshot_path = screenshots_dir / screenshot_filename
                        try:
                            page.screenshot(
                                path=str(screenshot_path), full_page=False
                            )
                            result.screenshot_path = str(
                                screenshot_path.relative_to(run_root)
                            )
                        except Exception as exc:
                            _log(f"  Screenshot failed: {exc}")

                    # Discover links for further traversal
                    if depth < max_depth and result.status == "ok":
                        found_links = extract_links(page, url, nav_selectors)
                        result.links_found = found_links
                        for link in found_links:
                            norm = normalize_url(link)
                            if norm not in visited:
                                if not same_domain_only or is_same_domain(link, url):
                                    visited.add(norm)
                                    queue.append((link, depth + 1, current_url))

                except PlaywrightTimeoutError:
                    result.status = "timeout"
                    result.error = f"Navigation timeout ({timeout_ms}ms)"
                    bad_links.append(
                        {
                            "url": current_url,
                            "error": result.error,
                            "parent_url": parent_url,
                            "depth": depth,
                        }
                    )
                    _log(f"  Timeout: {current_url}")
                except Exception as exc:
                    result.status = "error"
                    result.error = str(exc)[:200]
                    bad_links.append(
                        {
                            "url": current_url,
                            "error": result.error,
                            "parent_url": parent_url,
                            "depth": depth,
                        }
                    )
                    _log(f"  Error: {exc}")

                results.append(result)

        finally:
            page.close()
            context.close()
            browser.close()

    # Build and save report
    ok_count = sum(1 for r in results if r.status == "ok")
    bad_count = len(bad_links)

    report: dict[str, Any] = {
        "site_name": site_name,
        "start_url": url,
        "crawled_at_utc": iso_utc_now(),
        "settings": {
            "max_depth": max_depth,
            "max_pages": max_pages,
            "same_domain_only": same_domain_only,
            "take_screenshots": take_screenshots,
        },
        "summary": {
            "total_pages": len(results),
            "ok_pages": ok_count,
            "bad_links": bad_count,
        },
        "pages": [
            {
                "url": r.url,
                "title": r.title,
                "depth": r.depth,
                "status": r.status,
                "error": r.error,
                "screenshot": r.screenshot_path,
                "links_found": len(r.links_found),
                "parent_url": r.parent_url,
            }
            for r in results
        ],
        "bad_links": bad_links,
    }

    report_path = run_root / "spider_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    _log("")
    _log("Spider exploration complete.")
    _log(f"- Pages visited : {len(results)}")
    _log(f"- OK pages      : {ok_count}")
    _log(f"- Bad links     : {bad_count}")
    _log(f"- Report        : {report_path}")

    return {
        "report_path": str(report_path),
        "artifacts_dir": str(run_root),
        "total_pages": len(results),
        "ok_pages": ok_count,
        "bad_links": bad_count,
        "bad_link_details": bad_links,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only auto-exploration spider for BAS web UIs."
    )
    parser.add_argument("--url", required=True, help="Starting URL to explore.")
    parser.add_argument(
        "--site-name",
        default="spider",
        help="Friendly site name for output directories. Default: spider",
    )
    parser.add_argument(
        "--output-dir",
        default="data/spider",
        help="Root directory for spider output. Default: data/spider",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Optional path to site config JSON for authenticated sites.",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=3,
        help="Maximum link depth to traverse. Default: 3",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=50,
        help="Maximum total pages to visit. Default: 50",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=30000,
        help="Navigation timeout in milliseconds. Default: 30000",
    )
    parser.add_argument("--viewport-width", type=int, default=1920)
    parser.add_argument("--viewport-height", type=int, default=1080)
    parser.add_argument(
        "--ignore-https-errors",
        action="store_true",
        help="Ignore HTTPS certificate errors.",
    )
    parser.add_argument(
        "--no-screenshots",
        action="store_true",
        help="Skip taking screenshots.",
    )
    parser.add_argument(
        "--browser",
        default="chromium",
        choices=["chromium", "firefox", "webkit"],
        help="Browser to use. Default: chromium",
    )
    parser.add_argument(
        "--allow-external",
        action="store_true",
        help="Follow links to external domains (not recommended for BAS UIs).",
    )
    return parser.parse_args()


def main() -> int:
    """CLI entry point for tree spider."""
    args = parse_args()
    try:
        run_spider(
            url=args.url,
            site_name=args.site_name,
            output_dir=args.output_dir,
            config_path=args.config,
            max_depth=args.max_depth,
            max_pages=args.max_pages,
            timeout_ms=args.timeout_ms,
            viewport_width=args.viewport_width,
            viewport_height=args.viewport_height,
            ignore_https_errors=args.ignore_https_errors,
            take_screenshots=not args.no_screenshots,
            browser_type=args.browser,
            same_domain_only=not args.allow_external,
        )
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
