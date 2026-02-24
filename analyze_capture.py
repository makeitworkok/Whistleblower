#!/usr/bin/env python3
# Copyright (c) 2025-2026 Chris Favre - MIT License
# See LICENSE file for full terms
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
DEFAULT_XAI_MODEL = "grok-2-vision-latest"
DEFAULT_XAI_ENDPOINT = "https://api.x.ai/v1/responses"


def normalize_provider(provider: str) -> str:
    provider_normalized = provider.strip().lower()
    if provider_normalized == "grok":
        return "xai"
    if provider_normalized in {"openai", "xai"}:
        return provider_normalized
    raise ValueError(f"Unsupported provider: {provider}")


def default_model_for_provider(provider: str) -> str:
    if provider == "xai":
        return os.getenv("XAI_MODEL", DEFAULT_XAI_MODEL)
    return os.getenv("OPENAI_MODEL", DEFAULT_MODEL)


def default_endpoint_for_provider(provider: str) -> str:
    if provider == "xai":
        return os.getenv("XAI_RESPONSES_ENDPOINT", DEFAULT_XAI_ENDPOINT)
    return os.getenv("OPENAI_RESPONSES_ENDPOINT", DEFAULT_ENDPOINT)


def default_api_key_env_for_provider(provider: str) -> str:
    return "XAI_API_KEY" if provider == "xai" else "OPENAI_API_KEY"


def parse_args() -> argparse.Namespace:
    env_provider = os.getenv("ANALYSIS_PROVIDER", "openai").strip().lower()
    default_provider = "xai" if env_provider in {"xai", "grok"} else "openai"
    parser = argparse.ArgumentParser(
        description="Analyze capture screenshots/DOM and emit structured notes."
    )
    parser.add_argument("--run-dir", default=None, help="Explicit run directory to analyze.")
    parser.add_argument("--data-dir", default="data", help="Root data directory. Default: data")
    parser.add_argument("--site", default=None, help="Site folder name under data/")
    parser.add_argument(
        "--start-utc",
        default=None,
        help=("Analyze runs with timestamps >= this (ISO 8601 or YYYYMMDD-HHMMSS)."),
    )
    parser.add_argument(
        "--end-utc",
        default=None,
        help=("Analyze runs with timestamps <= this (ISO 8601 or YYYYMMDD-HHMMSS)."),
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "xai", "grok"],
        default=default_provider,
        help="LLM provider. `grok` is an alias for `xai`. Default: openai",
    )
    parser.add_argument(
        "--model",
        default=None,
        help=(
            "Model for analysis. Defaults by provider: "
            f"openai={DEFAULT_MODEL}, xai={DEFAULT_XAI_MODEL}"
        ),
    )
    parser.add_argument(
        "--endpoint",
        default=None,
        help=(
            "Responses API endpoint. Defaults by provider: "
            f"openai={DEFAULT_ENDPOINT}, xai={DEFAULT_XAI_ENDPOINT}"
        ),
    )
    parser.add_argument(
        "--api-key-env",
        default=None,
        help="Environment variable name containing the API key. Defaults by provider.",
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
        "--combine-run",
        action="store_true",
        help="Combine all targets in a run into a single analysis summary.",
    )
    parser.add_argument(
        "--per-page",
        action="store_true",
        help="Analyze each page separately instead of combining.",
    )
    parser.add_argument(
        "--env-file",
        default=".private/openai.env",
        help="Optional env file for API keys/models/endpoints. Default: .private/openai.env",
    )
    return parser.parse_args()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_iso_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = value.strip()
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        try:
            parsed = datetime.strptime(raw, "%Y%m%d-%H%M%S")
        except ValueError:
            return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_run_dir_timestamp(run_dir: Path) -> datetime | None:
    try:
        return datetime.strptime(run_dir.name, "%Y%m%d-%H%M%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


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


def find_runs_in_range(
    data_dir: Path,
    site: str | None,
    start: datetime | None,
    end: datetime | None,
) -> list[Path]:
    if not data_dir.exists():
        raise ValueError(f"Data directory not found: {data_dir}")
    if site is not None:
        site_dirs = [data_dir / site]
    else:
        site_dirs = [p for p in data_dir.iterdir() if p.is_dir()]

    runs: list[tuple[datetime, Path]] = []
    for site_dir in site_dirs:
        if not site_dir.exists():
            continue
        for run_dir in site_dir.iterdir():
            if not run_dir.is_dir():
                continue
            ts = parse_run_dir_timestamp(run_dir)
            if ts is None:
                continue
            if start is not None and ts < start:
                continue
            if end is not None and ts > end:
                continue
            runs.append((ts, run_dir))

    return [item[1] for item in sorted(runs, key=lambda item: item[0])]


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
    image_data_url: str | None,
    image_data_urls: list[str] | None = None,
) -> str:
    content: list[dict[str, Any]] = [{"type": "input_text", "text": user_text}]
    if image_data_urls:
        content.extend([{"type": "input_image", "image_url": url} for url in image_data_urls])
    elif image_data_url:
        content.append({"type": "input_image", "image_url": image_data_url})

    request_payload = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system_prompt}],
            },
            {
                "role": "user",
                "content": content,
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
        "If uncertain, say uncertain. Follow the requested markdown section order exactly."
    )


def default_user_prompt(meta: dict[str, Any], dom: dict[str, Any], max_dom_chars: int) -> str:
    dom_text = str(dom.get("text") or "")
    dom_excerpt = dom_text[:max_dom_chars]
    lines = [
        "Analyze this dashboard capture for operational insight and anomalies.",
        "Return markdown with these sections:",
        "1. Summary (2-4 bullets, operator-facing, plain language)",
        "2. Snapshot",
        "3. Potential issues",
        "4. Evidence",
        "5. Suggested checks",
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


def default_combined_prompt(
    run_dir: Path,
    metas: list[dict[str, Any]],
    doms: list[dict[str, Any]],
    max_dom_chars: int,
) -> str:
    lines = [
        "Analyze this set of dashboard captures for operational insight and anomalies.",
        "Return markdown with these sections:",
        "1. Summary (3-6 bullets, operator-facing, plain language)",
        "2. Snapshot (per page)",
        "3. Potential issues",
        "4. Evidence",
        "5. Suggested checks",
        "",
        f"Run directory: {run_dir}",
        "",
    ]
    for index, meta in enumerate(metas):
        dom_text = str(doms[index].get("text") or "")
        dom_excerpt = dom_text[:max_dom_chars]
        lines.extend(
            [
                f"Page {index + 1}:",
                f"- target_name: {meta.get('target_name', '')}",
                f"- target_url: {meta.get('target_url', '')}",
                f"- title: {meta.get('title', '')}",
                f"- url_after_navigation: {meta.get('url_after_navigation', '')}",
                f"- readiness_error: {meta.get('readiness_error', '')}",
                f"- DOM text excerpt (first {len(dom_excerpt)} chars):",
                dom_excerpt if dom_excerpt else "(no DOM text)",
                "",
            ]
        )
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


def analyze_run_combined(
    *,
    run_dir: Path,
    endpoint: str,
    api_key: str,
    model: str,
    max_dom_chars: int,
    custom_prompt: str | None,
) -> dict[str, Any]:
    target_dirs = discover_target_dirs(run_dir)
    if not target_dirs:
        raise ValueError(f"No target capture directories found in: {run_dir}")

    metas: list[dict[str, Any]] = []
    doms: list[dict[str, Any]] = []
    images: list[str] = []

    for target_dir in target_dirs:
        screenshot_path = target_dir / "screenshot.png"
        dom_path = target_dir / "dom.json"
        meta_path = target_dir / "meta.json"
        if not screenshot_path.exists() or not dom_path.exists() or not meta_path.exists():
            continue
        doms.append(json.loads(dom_path.read_text(encoding="utf-8")))
        metas.append(json.loads(meta_path.read_text(encoding="utf-8")))
        images.append(b64_data_url(screenshot_path))

    if not metas:
        raise ValueError(f"No analyzable targets found in: {run_dir}")

    user_prompt = custom_prompt or default_combined_prompt(run_dir, metas, doms, max_dom_chars)
    analysis_text = call_responses_api(
        endpoint=endpoint,
        api_key=api_key,
        model=model,
        system_prompt=default_system_prompt(),
        user_text=user_prompt,
        image_data_url=None,
        image_data_urls=images,
    )

    combined_md = run_dir / "analysis_combined.md"
    combined_json = run_dir / "analysis_combined.json"
    combined_md.write_text(analysis_text + "\n", encoding="utf-8")
    combined_json.write_text(
        json.dumps(
            {
                "analyzed_at_utc": utc_now_iso(),
                "model": model,
                "run_dir": str(run_dir),
                "pages_analyzed": len(metas),
                "analysis_md": combined_md.name,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "run_dir": str(run_dir),
        "analysis_md": str(combined_md),
        "analysis_json": str(combined_json),
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


def run_analysis(
    run_dir: str | Path | None = None,
    data_dir: str | Path = "data",
    site: str | None = None,
    start_utc: str | None = None,
    end_utc: str | None = None,
    provider: str = "openai",
    model: str | None = None,
    endpoint: str | None = None,
    api_key: str | None = None,
    api_key_env: str | None = None,
    max_dom_chars: int = 12000,
    custom_prompt: str | None = None,
    combine_run: bool = True,
    env_file: str = ".env",
) -> dict[str, Any]:
    """
    Run analysis on capture artifacts using an LLM.
    
    Args:
        run_dir: Explicit run directory to analyze
        data_dir: Root data directory
        site: Site folder name under data/
        start_utc: Analyze runs with timestamps >= this (ISO 8601 or YYYYMMDD-HHMMSS)
        end_utc: Analyze runs with timestamps <= this (ISO 8601 or YYYYMMDD-HHMMSS)
        provider: LLM provider (openai, xai, grok)
        model: Model for analysis (defaults by provider)
        endpoint: Responses API endpoint (defaults by provider)
        api_key: API key directly (overrides env lookup)
        api_key_env: Environment variable name containing the API key
        max_dom_chars: Max DOM characters to include
        custom_prompt: Custom analysis prompt
        combine_run: Combine all targets into single analysis
        env_file: Path to .env file
    
    Returns:
        Dictionary with analysis summary and results
    """
    load_env_file(Path(env_file))
    provider = normalize_provider(provider)
    model = model or default_model_for_provider(provider)
    endpoint = endpoint or default_endpoint_for_provider(provider)
    
    # Get API key
    if not api_key:
        api_key_env_name = api_key_env or default_api_key_env_for_provider(provider)
        api_key = os.getenv(api_key_env_name)
        if not api_key:
            if provider == "xai":
                fallbacks = ["XAI_API_KEY", "GROK_API_KEY"]
                for fallback_key in fallbacks:
                    fallback_value = os.getenv(fallback_key)
                    if fallback_value:
                        api_key = fallback_value
                        break
            if not api_key:
                raise ValueError(f"API key not found. Set {api_key_env_name} environment variable.")

    start_dt = parse_iso_utc(start_utc)
    end_dt = parse_iso_utc(end_utc)
    if start_utc and start_dt is None:
        raise ValueError(f"Invalid start_utc value: {start_utc}")
    if end_utc and end_dt is None:
        raise ValueError(f"Invalid end_utc value: {end_utc}")
    if start_dt and end_dt and start_dt > end_dt:
        raise ValueError("start_utc must be <= end_utc")

    if run_dir:
        run_dirs = [Path(run_dir)]
    elif start_dt or end_dt:
        run_dirs = find_runs_in_range(Path(data_dir), site, start_dt, end_dt)
        if not run_dirs:
            raise ValueError("No runs found in the requested time range.")
    else:
        run_dirs = [find_latest_run(Path(data_dir), site)]

    all_run_summaries = []
    skipped_runs = []
    
    for run_dir_path in run_dirs:
        try:
            if not run_dir_path.exists():
                print(f"WARNING: Run directory not found, skipping: {run_dir_path}", file=sys.stderr)
                skipped_runs.append(str(run_dir_path))
                continue

            if combine_run:
                combined = analyze_run_combined(
                    run_dir=run_dir_path,
                    endpoint=endpoint,
                    api_key=api_key,
                        model=model,
                    max_dom_chars=max_dom_chars,
                    custom_prompt=custom_prompt,
                )
                run_summary = {
                    "analyzed_at_utc": utc_now_iso(),
                    "run_dir": str(run_dir_path),
                    "provider": provider,
                    "model": model,
                    "endpoint": endpoint,
                    "combined": True,
                    "combined_analysis": combined,
                }
            else:
                target_dirs = discover_target_dirs(run_dir_path)
                if not target_dirs:
                    print(f"WARNING: No target capture directories found, skipping: {run_dir_path}", file=sys.stderr)
                    skipped_runs.append(str(run_dir_path))
                    continue

                results = []
                for target_dir in target_dirs:
                    result = analyze_target(
                        target_dir=target_dir,
                        endpoint=endpoint,
                        api_key=api_key,
                        model=model,
                        max_dom_chars=max_dom_chars,
                        custom_prompt=custom_prompt,
                    )
                    results.append(result)

                run_summary = {
                    "analyzed_at_utc": utc_now_iso(),
                    "run_dir": str(run_dir_path),
                    "provider": provider,
                    "model": model,
                    "endpoint": endpoint,
                    "targets_analyzed": len(results),
                    "targets": results,
                }

            run_analysis_path = run_dir_path / "analysis_summary.json"
            run_analysis_path.write_text(json.dumps(run_summary, indent=2), encoding="utf-8")
            all_run_summaries.append(run_summary)
        
        except Exception as run_exc:
            print(f"WARNING: Error analyzing run {run_dir_path}, skipping: {run_exc}", file=sys.stderr)
            skipped_runs.append(str(run_dir_path))
            continue
    
    # If no runs were successfully analyzed, raise an error
    if not all_run_summaries:
        if skipped_runs:
            raise ValueError(f"Could not analyze any runs. Skipped {len(skipped_runs)} run(s) due to errors.")
        else:
            raise ValueError("No runs found to analyze.")

    if len(all_run_summaries) > 1 or start_dt or end_dt:
        range_root = Path(data_dir)
        if site:
            range_root = range_root / site
        range_summary_path = range_root / "analysis_range_summary.json"
        range_summary_path.write_text(
            json.dumps(
                {
                    "analyzed_at_utc": utc_now_iso(),
                    "provider": provider,
                    "model": model,
                    "endpoint": endpoint,
                    "start_utc": start_dt.isoformat() if start_dt else None,
                    "end_utc": end_dt.isoformat() if end_dt else None,
                    "runs_analyzed": len(all_run_summaries),
                    "runs": all_run_summaries,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    
    result = {
        "runs_analyzed": len(all_run_summaries),
        "run_summaries": all_run_summaries,
        "skipped_runs": len(skipped_runs),
    }
    
    if len(run_dirs) == 1:
        msg = f"Analysis completed: {run_dirs[0]}"
    else:
        msg = f"Analysis completed for {len(all_run_summaries)} of {len(run_dirs)} runs."
    
    if skipped_runs:
        msg += f" ({len(skipped_runs)} run(s) skipped due to errors)"
    
    result["message"] = msg
    
    return result


def main() -> int:
    """CLI entry point for analysis."""
    args = parse_args()
    try:
        result = run_analysis(
            run_dir=args.run_dir,
            data_dir=args.data_dir,
            site=args.site,
            start_utc=args.start_utc,
            end_utc=args.end_utc,
            provider=args.provider,
            model=args.model,
            endpoint=args.endpoint,
            api_key_env=args.api_key_env,
            max_dom_chars=args.max_dom_chars,
            custom_prompt=args.prompt,
            combine_run=args.combine_run or not args.per_page,
            env_file=args.env_file,
        )
        print(result["message"])
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
