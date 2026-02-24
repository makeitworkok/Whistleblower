#!/usr/bin/env python3
"""Site configuration management for Tkinter UI."""

import json
import os
from pathlib import Path
from typing import Any


SITES_DIR = Path("sites")
SETUP_SUFFIX = "_setup.json"


def ensure_sites_dir() -> None:
    """Ensure sites directory exists."""
    SITES_DIR.mkdir(exist_ok=True)


def get_site_setup_path(site_name: str) -> Path:
    """Get path to site setup config file."""
    ensure_sites_dir()
    safe_name = site_name.replace(" ", "_").replace("/", "_")
    return SITES_DIR / f"{safe_name}{SETUP_SUFFIX}"


def list_sites() -> list[str]:
    """List all configured sites."""
    ensure_sites_dir()
    sites = []
    for file in SITES_DIR.glob(f"*{SETUP_SUFFIX}"):
        site_name = file.stem.replace(SETUP_SUFFIX.strip("."), "").replace("_", " ")
        sites.append(site_name)
    return sorted(sites)


def save_site_config(site_name: str, config: dict[str, Any]) -> None:
    """Save site configuration to JSON file."""
    path = get_site_setup_path(site_name)
    path.write_text(json.dumps(config, indent=2))


def load_site_config(site_name: str) -> dict[str, Any] | None:
    """Load site configuration from JSON file."""
    path = get_site_setup_path(site_name)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def delete_site_config(site_name: str) -> None:
    """Delete site configuration."""
    path = get_site_setup_path(site_name)
    if path.exists():
        path.unlink()


def create_default_config(
    site_name: str,
    bootstrap_url: str,
    viewport_width: int = 1920,
    viewport_height: int = 1080,
    ignore_https_errors: bool = True,
) -> dict[str, Any]:
    """Create a default site configuration."""
    safe_name = site_name.replace(" ", "_").lower()
    return {
        "site_name": site_name,
        "bootstrap_url": bootstrap_url,
        "viewport": {
            "width": viewport_width,
            "height": viewport_height,
        },
        "ignore_https_errors": ignore_https_errors,
        "browser": "chromium",
        "directories": {
            "bootstrap_artifacts": f"data/{safe_name}",
            "capture_data": f"data/{safe_name}",
            "analysis_output": f"data/{safe_name}",
        },
        "capture_settings": {
            "timeout_ms": 30000,
            "settle_ms": 1000,
            "post_login_wait_ms": 0,
            "headed": False,
            "record_video": False,
            "video_width": 1920,
            "video_height": 1080,
        },
        "analysis_settings": {
            "provider": "openai",
            "max_dom_chars": 12000,
            "combine_run": True,
        },
        "api_keys": {
            "openai_key": "",
            "xai_key": "",
        },
    }
