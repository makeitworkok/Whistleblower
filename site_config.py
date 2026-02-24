#!/usr/bin/env python3
"""Site configuration management for Tkinter UI."""

import json
import os
from pathlib import Path
from typing import Any


SITES_DIR = Path("sites")
CONFIG_SUFFIX = ".config.json"


def ensure_sites_dir() -> None:
    """Ensure sites directory exists."""
    SITES_DIR.mkdir(parents=True, exist_ok=True)


def get_site_setup_path(site_name: str) -> Path:
    """Get path to site setup config file."""
    ensure_sites_dir()
    safe_name = site_name.replace(" ", "_").replace("/", "_").lower()
    return SITES_DIR / f"{safe_name}{CONFIG_SUFFIX}"


def list_sites() -> list[str]:
    """List all configured sites."""
    ensure_sites_dir()
    sites = []
    for file in SITES_DIR.glob(f"*{CONFIG_SUFFIX}"):
        # Extract site name from filename (remove .config.json)
        # file.name = "tk3_setup.config.json"
        # Remove the suffix to get "tk3_setup", then convert underscores to spaces to get "tk3 setup"
        name_without_suffix = file.name.replace(CONFIG_SUFFIX, "")
        site_name = name_without_suffix.replace("_", " ")
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
        print(f"DEBUG: Config file not found at {path}")
        print(f"DEBUG: Current directory: {Path.cwd()}")
        print(f"DEBUG: Looking for site config for: {site_name}")
        # List what files DO exist in sites directory
        if Path("sites").exists():
            files = list(Path("sites").glob("*_setup.json"))
            print(f"DEBUG: Found {len(files)} site config files: {[f.name for f in files]}")
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
    safe_name = site_name.replace(" ", "_").replace("/", "_").lower()
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
