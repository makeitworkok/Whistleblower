#!/usr/bin/env python3
"""Analyze Whistleblower capture artifacts using an LLM with image + DOM context."""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_ENDPOINT = "https://api.openai.com/v1/responses"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze capture screenshots/DOM and emit structured notes."
    )
    parser.add_argument("--run-dir", default=None, help="Explicit run directory to analyze.")
    parser.add_argument("--data-dir", default="data", help="Root data directory. Default: data")
    parser.add_argument("--site", default=None, help="Site folder name under data/")
    parser.add_argument(
        "--model",
        default=os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        help=f"Model for analysis. Default: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--endpoint",
        default=os.getenv("OPENAI_RESPONSES_ENDPOINT", DEFAULT_ENDPOINT),
        help=f"Responses API endpoint. Default: {DEFAULT_ENDPOINT}",
    )
    parser.add_argument(
        "--max-dom-chars",
        type=int,
        default=12000,
        help="Maximum DOM text characters sent per target. Default: 12000",
    )
    parser.add_argument(
        "--prompt",
        default=None,
        help="Optional custom analysis prompt. If omitted, a default BAS-oriented prompt is used.",
    )
    parser.add_argument(
        "--env-file",
        default=".private/openai.env",
        help="Env file to load when OPENAI_API_KEY is not already set. Default: .private/openai.env",
    )
    return parser.parse_args()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def find_latest_run(data_dir: Path, site: str | None) -> Path:
    if site is not None:
        site_dir = data_dir / site
        if not site_dir.exists():
            raise ValueError(f"Site directory not found: {site_dir}")
        runs = sorted([p for p in site_dir.iterdir() if p.is_dir()])
        if not runs:
            raise ValueError(f"No runs found under: {site_dir}")
        return runs[-1]

    candidates: list[Path] = []
    for site_dir in data_dir.iterdir():
        if not site_dir.is_dir():
            continue
        for run_dir in site_dir.iterdir():
            if run_dir.is_dir():
                candidates.append(run_dir)
    if not candidates:
        raise ValueError(f"No runs found under: {data_dir}")
    return sorted(candidates)[-1]


def b64_data_url(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def parse_response_text(payload: dict[str, Any]) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    chunks: list[str] = []
    for item in payload.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            text = content.get("text")
            if isinstance(text, str) and text.strip():
                chunks.append(text.strip())
    return "\n\n".join(chunks).strip()


def call_responses_api(
    *,
    endpoint: str,
    api_key: str,
    model: str,
    system_prompt: str,
    user_text: str,
    image_data_url: str,
) -> str:
    request_payload = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_prompt}],
            },
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": user_text},
                    {"type": "input_image", "image_url": image_data_url},
                ],
            },
        ],
    }
    body = json.dumps(request_payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            response_payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Responses API HTTP {exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Responses API request failed: {exc}") from exc

    text = parse_response_text(response_payload)
    if not text:
        raise RuntimeError("Responses API returned no text output.")
    return text


def default_system_prompt() -> str:
    return (
        "You analyze BAS/HMI dashboard evidence. Be concise, factual, and avoid guessing. "
        "If uncertain, say uncertain."
    )


def default_user_prompt(meta: dict[str, Any], dom: dict[str, Any], max_dom_chars: int) -> str:
    dom_text = str(dom.get("text") or "")
    dom_excerpt = dom_text[:max_dom_chars]
    lines = [
        "Analyze this dashboard capture for operational insight and anomalies.",
        "Return markdown with these sections:",
        "1. Snapshot",
        "2. Potential issues",
        "3. Evidence",
        "4. Suggested checks",
        "",
        "Capture metadata:",
        f"- target_name: {meta.get('target_name', '')}",
        f"- target_url: {meta.get('target_url', '')}",
        f"- title: {meta.get('title', '')}",
        f"- url_after_navigation: {meta.get('url_after_navigation', '')}",
        f"- readiness_error: {meta.get('readiness_error', '')}",
        "",
        f"DOM text excerpt (first {len(dom_excerpt)} chars):",
        dom_excerpt if dom_excerpt else "(no DOM text)",
    ]
    return "\n".join(lines)


def analyze_target(
    *,
    target_dir: Path,
    endpoint: str,
    api_key: str,
    model: str,
    max_dom_chars: int,
    custom_prompt: str | None,
) -> dict[str, Any]:
    screenshot_path = target_dir / "screenshot.png"
    dom_path = target_dir / "dom.json"
    meta_path = target_dir / "meta.json"
    if not screenshot_path.exists() or not dom_path.exists() or not meta_path.exists():
        raise ValueError(f"Missing required files in {target_dir}")

    dom = json.loads(dom_path.read_text(encoding="utf-8"))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    user_prompt = custom_prompt or default_user_prompt(meta, dom, max_dom_chars)
    analysis_text = call_responses_api(
        endpoint=endpoint,
        api_key=api_key,
        model=model,
        system_prompt=default_system_prompt(),
        user_text=user_prompt,
        image_data_url=b64_data_url(screenshot_path),
    )

    analysis_md = target_dir / "analysis.md"
    analysis_json = target_dir / "analysis.json"
    analysis_md.write_text(analysis_text + "\n", encoding="utf-8")
    analysis_json.write_text(
        json.dumps(
            {
                "analyzed_at_utc": utc_now_iso(),
                "model": model,
                "target_dir": str(target_dir),
                "target_name": meta.get("target_name", target_dir.name),
                "target_url": meta.get("target_url", ""),
                "analysis_md": analysis_md.name,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "target_dir": str(target_dir),
        "target_name": meta.get("target_name", target_dir.name),
        "analysis_md": str(analysis_md),
        "analysis_json": str(analysis_json),
    }


def discover_target_dirs(run_dir: Path) -> list[Path]:
    return sorted(
        [
            p
            for p in run_dir.iterdir()
            if p.is_dir() and (p / "screenshot.png").exists() and (p / "dom.json").exists()
        ]
    )


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def main() -> int:
    args = parse_args()
    load_env_file(Path(args.env_file))
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY is not set.", file=sys.stderr)
        return 1

    try:
        run_dir = Path(args.run_dir) if args.run_dir else find_latest_run(Path(args.data_dir), args.site)
        if not run_dir.exists():
            raise ValueError(f"Run directory not found: {run_dir}")
        target_dirs = discover_target_dirs(run_dir)
        if not target_dirs:
            raise ValueError(f"No target capture directories found in: {run_dir}")

        results = []
        for target_dir in target_dirs:
            result = analyze_target(
                target_dir=target_dir,
                endpoint=args.endpoint,
                api_key=api_key,
                model=args.model,
                max_dom_chars=args.max_dom_chars,
                custom_prompt=args.prompt,
            )
            results.append(result)

        run_analysis_path = run_dir / "analysis_summary.json"
        run_analysis_path.write_text(
            json.dumps(
                {
                    "analyzed_at_utc": utc_now_iso(),
                    "run_dir": str(run_dir),
                    "model": args.model,
                    "targets_analyzed": len(results),
                    "targets": results,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Analysis completed: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
