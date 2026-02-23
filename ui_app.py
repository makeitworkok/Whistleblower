#!/usr/bin/env python3
"""Local web UI for Whistleblower runs (bootstrap + capture)."""

from __future__ import annotations

import html
import json
import os
import threading
import time
import urllib.parse
import webbrowser
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import subprocess
import sys
from typing import Any

HOST = "127.0.0.1"
PORT = 8787

SERVER: HTTPServer | None = None
STATE_LOCK = threading.Lock()
BOOTSTRAP_PROCESS: subprocess.Popen[str] | None = None
BOOTSTRAP_LOG: list[str] = []
BOOTSTRAP_THREAD: threading.Thread | None = None
LAST_BOOTSTRAP_OUTPUT = ""
LAST_CAPTURE_OUTPUT = ""
LAST_SCHEDULE_OUTPUT = ""
LAST_ANALYSIS_OUTPUT = ""

CAPTURE_THREAD: threading.Thread | None = None
CAPTURE_STATUS: dict[str, Any] = {
  "running": False,
  "last_started_utc": "",
  "last_finished_utc": "",
  "last_result": "",
}

SCHEDULE_THREAD: threading.Thread | None = None
SCHEDULE_STOP = threading.Event()
SCHEDULE_STATUS: dict[str, Any] = {
  "running": False,
  "interval_min": None,
  "next_run_utc": None,
  "last_run_utc": None,
  "last_result": "",
  "last_error": "",
}


def list_site_configs() -> list[str]:
    sites_dir = Path("sites")
    if not sites_dir.exists():
        return []
    configs = []
    for path in sites_dir.glob("*.json"):
        if path.name.endswith(".steps.json"):
            continue
        configs.append(path.name)
    return sorted(configs)


def list_data_sites(data_dir: Path | None = None) -> list[str]:
  root = data_dir or Path("data")
  if not root.exists():
    return []
  return sorted([p.name for p in root.iterdir() if p.is_dir() and p.name != "bootstrap"])


def list_run_dirs(data_dir: Path | None = None, site: str | None = None) -> list[str]:
  root = data_dir or Path("data")
  if not root.exists():
    return []
  run_dirs: list[str] = []
  site_dirs = [root / site] if site else [p for p in root.iterdir() if p.is_dir()]
  for site_dir in site_dirs:
    if not site_dir.exists() or site_dir.name == "bootstrap":
      continue
    for run_dir in site_dir.iterdir():
      if run_dir.is_dir():
        run_dirs.append(str(site_dir / run_dir.name))
  return sorted(run_dirs)


def list_analysis_entries(data_dir: Path | None = None, site: str | None = None) -> list[tuple[str, str]]:
  root = data_dir or Path("data")
  entries: list[tuple[str, str]] = []
  if not root.exists():
    return entries

  run_dirs = list_run_dirs(root, site)
  for run_dir_str in run_dirs:
    run_dir = Path(run_dir_str)
    run_label = run_dir.name
    try:
      parsed = datetime.strptime(run_dir.name, "%Y%m%d-%H%M%S")
      run_label = parsed.strftime("%Y-%m-%d %H:%M:%S UTC")
    except ValueError:
      run_label = run_dir.name
    site_label = run_dir.parent.name
    summary_path = run_dir / "analysis_summary.json"
    if not summary_path.exists():
      continue
    try:
      summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
      continue
    targets = summary.get("targets", [])
    if not isinstance(targets, list):
      targets = []
    combined = summary.get("combined") is True
    combined_info = summary.get("combined_analysis") if combined else None
    combined_md = None
    if isinstance(combined_info, dict):
      combined_md = combined_info.get("analysis_md")
    if combined and combined_md:
      label = f"{site_label} / {run_label} / combined"
      entries.append((label, str(Path(combined_md))))
    for target in targets:
      if not isinstance(target, dict):
        continue
      analysis_md = target.get("analysis_md")
      target_name = target.get("target_name", "page")
      if not analysis_md:
        continue
      label = f"{site_label} / {run_label} / page {target_name}"
      entries.append((label, str(Path(analysis_md))))
  return entries


def load_analysis_text(path: str) -> str | None:
  try:
    resolved = Path(path)
    if not resolved.exists() or not resolved.is_file():
      return None
    return resolved.read_text(encoding="utf-8")
  except OSError:
    return None


def load_env_file_key(path: Path, keys: tuple[str, ...]) -> str | None:
  if not path.exists():
    return None
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
    if key in keys and value:
      return value
  return None


def has_api_key_for_provider(provider: str) -> bool:
  env_key = "OPENAI_API_KEY" if provider == "openai" else "XAI_API_KEY"
  if os.getenv(env_key):
    return True
  env_file_key = load_env_file_key(Path(".private/openai.env"), (env_key,))
  return bool(env_file_key)


def has_any_api_key() -> bool:
  return has_api_key_for_provider("openai") or has_api_key_for_provider("xai")


def parse_local_datetime(value: str) -> str | None:
  raw = value.strip()
  if not raw:
    return None
  try:
    parsed = datetime.fromisoformat(raw)
  except ValueError:
    return None
  if parsed.tzinfo is None:
    parsed = parsed.replace(tzinfo=timezone.utc)
  return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def build_capture_command(data: dict[str, list[str]], prefix: str = "") -> tuple[list[str] | None, str | None]:
  def field(name: str, default: str = "") -> str:
    return (data.get(f"{prefix}{name}") or [default])[0].strip()

  config_custom = field("config_custom")
  config_file = field("config_file")
  config_path = config_custom or (f"sites/{config_file}" if config_file else "")
  if not config_path:
    return None, "Please choose a config file or enter a custom path."

  cmd = [sys.executable, "whistleblower.py", "--config", config_path]

  data_dir = field("data_dir")
  if data_dir:
    cmd.extend(["--data-dir", data_dir])

  timeout_ms = field("timeout_ms")
  if timeout_ms:
    cmd.extend(["--timeout-ms", timeout_ms])

  settle_ms = field("settle_ms")
  if settle_ms:
    cmd.extend(["--settle-ms", settle_ms])

  post_login_wait_ms = field("post_login_wait_ms")
  if post_login_wait_ms:
    cmd.extend(["--post-login-wait-ms", post_login_wait_ms])

  if f"{prefix}headed" in data:
    cmd.append("--headed")
  if f"{prefix}record_video" in data:
    cmd.append("--record-video")

  video_width = field("video_width")
  if video_width:
    cmd.extend(["--video-width", video_width])

  video_height = field("video_height")
  if video_height:
    cmd.extend(["--video-height", video_height])

  return cmd, None


def run_capture_command(cmd: list[str], env: dict[str, str] | None = None) -> tuple[int, str]:
  result = subprocess.run(cmd, capture_output=True, text=True, env=env)
  output = (result.stdout or "") + (result.stderr or "")
  return result.returncode, output


def run_capture_streaming(cmd: list[str], env: dict[str, str] | None = None) -> tuple[int, str]:
  proc = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
    env=env,
  )
  output_lines: list[str] = []
  if proc.stdout is not None:
    for line in proc.stdout:
      output_lines.append(line)
      with STATE_LOCK:
        # Keep the UI log responsive without growing unbounded.
        LAST_CAPTURE_OUTPUT = "".join(output_lines[-400:])
  return_code = proc.wait()
  output = "".join(output_lines)
  return return_code, output


def capture_worker(cmd: list[str]) -> None:
  global LAST_CAPTURE_OUTPUT
  started = datetime.now(timezone.utc)
  with STATE_LOCK:
    CAPTURE_STATUS["running"] = True
    CAPTURE_STATUS["last_started_utc"] = started.isoformat()
    CAPTURE_STATUS["last_result"] = ""
    LAST_CAPTURE_OUTPUT = "Capture running..."

  return_code, output = run_capture_streaming(cmd)
  finished = datetime.now(timezone.utc)

  with STATE_LOCK:
    LAST_CAPTURE_OUTPUT = output or "(no output)"
    CAPTURE_STATUS["running"] = False
    CAPTURE_STATUS["last_finished_utc"] = finished.isoformat()
    CAPTURE_STATUS["last_result"] = "ok" if return_code == 0 else "error"


def schedule_loop(cmd: list[str], interval_minutes: int) -> None:
  global LAST_SCHEDULE_OUTPUT
  interval_seconds = max(1, interval_minutes) * 60
  with STATE_LOCK:
    SCHEDULE_STATUS["running"] = True
    SCHEDULE_STATUS["interval_min"] = interval_minutes
    SCHEDULE_STATUS["last_error"] = ""

  while not SCHEDULE_STOP.is_set():
    start = datetime.now(timezone.utc)
    with STATE_LOCK:
      SCHEDULE_STATUS["next_run_utc"] = start.isoformat()

    return_code, output = run_capture_command(cmd)
    finished = datetime.now(timezone.utc)

    with STATE_LOCK:
      LAST_SCHEDULE_OUTPUT = output
      SCHEDULE_STATUS["last_run_utc"] = finished.isoformat()
      SCHEDULE_STATUS["last_result"] = "ok" if return_code == 0 else "error"
      SCHEDULE_STATUS["last_error"] = "" if return_code == 0 else "Capture failed."

    next_run = finished + timedelta(seconds=interval_seconds)
    with STATE_LOCK:
      SCHEDULE_STATUS["next_run_utc"] = next_run.isoformat()

    while not SCHEDULE_STOP.is_set():
      now = datetime.now(timezone.utc)
      if now >= next_run:
        break
      time.sleep(min(1, (next_run - now).total_seconds()))

  with STATE_LOCK:
    SCHEDULE_STATUS["running"] = False


def start_log_thread(proc: subprocess.Popen[str]) -> threading.Thread:
    def reader() -> None:
        if proc.stdout is None:
            return
        for line in proc.stdout:
            with STATE_LOCK:
                BOOTSTRAP_LOG.append(line)

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    return thread


def render_page(message: str | None = None) -> str:
    with STATE_LOCK:
        is_bootstrap_running = BOOTSTRAP_PROCESS is not None and BOOTSTRAP_PROCESS.poll() is None
        bootstrap_log = "".join(BOOTSTRAP_LOG[-200:])
        last_bootstrap_output = LAST_BOOTSTRAP_OUTPUT
        last_capture_output = LAST_CAPTURE_OUTPUT
    capture_status = CAPTURE_STATUS.copy()
    last_schedule_output = LAST_SCHEDULE_OUTPUT
    last_analysis_output = LAST_ANALYSIS_OUTPUT
    schedule_status = SCHEDULE_STATUS.copy()

    config_options = list_site_configs()
    config_select = "\n".join(
        [f"<option value='{html.escape(name)}'>{html.escape(name)}</option>" for name in config_options]
    )

    data_sites = list_data_sites()
    data_site_select = "\n".join(
      [f"<option value='{html.escape(name)}'>{html.escape(name)}</option>" for name in data_sites]
    )
    run_options = list_run_dirs()
    run_select = "\n".join(
      [f"<option value='{html.escape(name)}'>{html.escape(name)}</option>" for name in run_options]
    )

    analysis_entries = list_analysis_entries()
    analysis_select = "\n".join(
      [
        f"<option value='{html.escape(path)}'>{html.escape(label)}</option>"
        for label, path in analysis_entries
      ]
    )

    message_html = ""
    if message:
        message_html = f"<div class='notice'>{html.escape(message)}</div>"

    bootstrap_status = "Running" if is_bootstrap_running else "Idle"
    bootstrap_action = (
        "<form method='POST' action='/stop_bootstrap'><button class='danger' type='submit'>Stop Recording</button></form>"
        if is_bootstrap_running
        else ""
    )

    schedule_status_text = "Running" if schedule_status.get("running") else "Idle"
    capture_status_text = "Running" if capture_status.get("running") else "Idle"
    capture_started = capture_status.get("last_started_utc") or "(none)"
    capture_finished = capture_status.get("last_finished_utc") or "(none)"
    capture_result = capture_status.get("last_result") or "(none)"
    schedule_action = (
      "<form method='POST' action='/stop_schedule'><button class='danger' type='submit'>Stop Schedule</button></form>"
      if schedule_status.get("running")
      else ""
    )
    schedule_interval = schedule_status.get("interval_min") or ""
    schedule_next = schedule_status.get("next_run_utc") or ""
    schedule_last = schedule_status.get("last_run_utc") or ""
    schedule_result = schedule_status.get("last_result") or ""
    analysis_openai_available = has_api_key_for_provider("openai")
    analysis_xai_available = has_api_key_for_provider("xai")
    analysis_any_available = analysis_openai_available or analysis_xai_available

    return f"""<!doctype html>
<html lang='en'>
<head>
  <meta charset='utf-8' />
  <meta name='viewport' content='width=device-width, initial-scale=1' />
  <title>Whistleblower Control Room</title>
  <style>
    :root {{
      --ink: #111216;
      --paper: #f5f1ea;
      --accent: #0b6d6b;
      --accent-2: #b24a2b;
      --shadow: rgba(12, 13, 16, 0.12);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "IBM Plex Sans", "Avenir Next", "Segoe UI", sans-serif;
      color: var(--ink);
      background: radial-gradient(circle at 10% 15%, #ffe7c7 0%, transparent 40%),
                  radial-gradient(circle at 85% 20%, #d3f6f2 0%, transparent 45%),
                  linear-gradient(145deg, #f2efe8 0%, #e7ece9 100%);
      min-height: 100vh;
    }}
    .wrap {{
      max-width: 1080px;
      margin: 0 auto;
      padding: 28px 20px 40px;
      animation: fadeIn 0.6s ease-out;
    }}
    header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 20px;
    }}
    h1 {{
      margin: 0;
      font-size: clamp(26px, 4vw, 38px);
      letter-spacing: 0.5px;
    }}
    .badge {{
      background: #111216;
      color: #f6f2ea;
      padding: 6px 12px;
      border-radius: 999px;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 1px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 18px;
    }}
    .card {{
      background: #ffffffcc;
      backdrop-filter: blur(4px);
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 12px 24px var(--shadow);
      border: 1px solid #e3ded5;
    }}
    h2 {{
      margin: 0 0 12px;
      font-size: 20px;
    }}
    label {{
      display: block;
      font-weight: 600;
      margin-top: 12px;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.8px;
    }}
    input, select, textarea {{
      width: 100%;
      margin-top: 6px;
      padding: 10px 12px;
      border-radius: 10px;
      border: 1px solid #cfc7bb;
      font-size: 14px;
      background: #fbfaf7;
    }}
    .row {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 10px;
    }}
    .checks {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 8px;
      margin-top: 8px;
    }}
    .checks label {{
      font-weight: 500;
      text-transform: none;
      letter-spacing: 0;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    button {{
      margin-top: 16px;
      background: var(--accent);
      color: #f2f1ed;
      border: none;
      padding: 10px 16px;
      border-radius: 999px;
      font-weight: 600;
      cursor: pointer;
    }}
    button.danger {{
      background: var(--accent-2);
    }}
    .notice {{
      background: #fff4da;
      border: 1px solid #f2c78a;
      padding: 10px 14px;
      border-radius: 12px;
      margin-bottom: 14px;
    }}
    .status {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
      color: #323232;
    }}
    .status span {{
      display: inline-flex;
      padding: 4px 10px;
      border-radius: 999px;
      background: #e4f2ef;
      border: 1px solid #c9e2dd;
    }}
    .hint {{
      margin-top: 6px;
      font-size: 12px;
      color: #5b5b5b;
    }}
    pre {{
      background: #0f1217;
      color: #e8ecef;
      padding: 12px;
      border-radius: 10px;
      overflow-x: auto;
      font-size: 12px;
      min-height: 120px;
    }}
    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(6px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
  </style>
</head>
<body>
  <div class='wrap'>
    <header>
      <h1>Whistleblower Control Room</h1>
      <div style='display: flex; gap: 12px; align-items: center;'>
        <div class='badge'>Local UI</div>
        <button id='stop_server_btn' class='danger' style='margin: 0; padding: 6px 12px; font-size: 12px;'>Stop Server</button>
      </div>
    </header>
    {message_html}

    <div class='grid'>
      <section class='card'>
        <h2>Bootstrap Recorder</h2>
        <div class='status'>Status: <span>{bootstrap_status}</span></div>
        {bootstrap_action}
        <form method='POST' action='/run_bootstrap'>
          <label for='boot_url'>Login URL</label>
          <input id='boot_url' name='url' type='text' placeholder='https://your-site/login' required />

          <label for='boot_site'>Site name</label>
          <input id='boot_site' name='site_name' type='text' placeholder='my_site' required />

          <div class='row'>
            <div>
              <label for='boot_width'>Viewport width</label>
              <input id='boot_width' name='viewport_width' type='number' value='1920' min='1' />
            </div>
            <div>
              <label for='boot_height'>Viewport height</label>
              <input id='boot_height' name='viewport_height' type='number' value='1080' min='1' />
            </div>
          </div>

          <label>Options</label>
          <div class='checks'>
            <label><input type='checkbox' name='ignore_https_errors' /> Ignore HTTPS errors</label>
            <label><input type='checkbox' name='record_video' /> Record video</label>
          </div>

          <label for='boot_output'>Output dir</label>
          <input id='boot_output' name='output_dir' type='text' placeholder='data/bootstrap' />

          <label for='boot_config_out'>Config output path (optional)</label>
          <input id='boot_config_out' name='config_out' type='text' placeholder='sites/my_site.bootstrap.json' />

          <label for='boot_steps_out'>Steps output path (optional)</label>
          <input id='boot_steps_out' name='steps_out' type='text' placeholder='sites/my_site.steps.json' />

          <button type='submit'>Start Recording</button>
        </form>
      </section>

      <section class='card'>
        <h2>Main Capture</h2>
        <form method='POST' action='/run_capture'>
          <label>Config source</label>
          <div class='checks'>
            <label><input type='radio' name='cap_config_mode' value='list' checked /> Pick a saved config</label>
            <label><input type='radio' name='cap_config_mode' value='custom' /> Use a custom file path (advanced)</label>
          </div>

          <div id='cap_config_list'>
            <label for='cap_config'>Saved configs</label>
            <select id='cap_config' name='config_file'>
              <option value=''>-- choose --</option>
              {config_select}
            </select>
            <div class='hint'>Configs are loaded from the sites/ folder.</div>
          </div>

          <div id='cap_config_custom_block' style='display: none;'>
            <label for='cap_config_custom'>Custom config path</label>
            <input id='cap_config_custom' name='config_custom' type='text' placeholder='sites/my_site.local.json' />
            <div class='hint'>Example: sites/my_site.local.json</div>
          </div>

          <label for='cap_data_dir'>Data dir</label>
          <input id='cap_data_dir' name='data_dir' type='text' placeholder='data' />

          <div class='row'>
            <div>
              <label for='cap_timeout'>Timeout ms</label>
              <input id='cap_timeout' name='timeout_ms' type='number' placeholder='30000' min='0' />
            </div>
            <div>
              <label for='cap_settle'>Settle ms</label>
              <input id='cap_settle' name='settle_ms' type='number' placeholder='5000' min='0' />
            </div>
            <div>
              <label for='cap_post_login'>Post-login ms</label>
              <input id='cap_post_login' name='post_login_wait_ms' type='number' placeholder='10000' min='0' />
            </div>
          </div>

          <label>Options</label>
          <div class='checks'>
            <label><input type='checkbox' name='headed' /> Headed browser</label>
            <label><input type='checkbox' name='record_video' /> Record video</label>
          </div>

          <div class='row'>
            <div>
              <label for='cap_video_width'>Video width (optional)</label>
              <input id='cap_video_width' name='video_width' type='number' min='1' />
            </div>
            <div>
              <label for='cap_video_height'>Video height (optional)</label>
              <input id='cap_video_height' name='video_height' type='number' min='1' />
            </div>
          </div>

          <button type='submit'>Run Capture</button>
        </form>
      </section>

      <section class='card'>
        <h2>Scheduled Capture</h2>
        <div class='status'>Status: <span>{schedule_status_text}</span></div>
        {schedule_action}
        <div class='status'>
          <span>Every: {html.escape(str(schedule_interval))} min</span>
          <span>Next: {html.escape(str(schedule_next))}</span>
          <span>Last: {html.escape(str(schedule_last))}</span>
          <span>Result: {html.escape(str(schedule_result))}</span>
        </div>
        <form method='POST' action='/start_schedule'>
          <label for='sched_config'>Config file</label>
          <select id='sched_config' name='sched_config_file'>
            <option value=''>-- choose --</option>
            {config_select}
          </select>

          <label for='sched_config_custom'>Or custom config path</label>
          <input id='sched_config_custom' name='sched_config_custom' type='text' placeholder='sites/my_site.local.json' />

          <label for='sched_interval'>Interval minutes</label>
          <input id='sched_interval' name='sched_interval_min' type='number' placeholder='30' min='1' required />

          <label for='sched_data_dir'>Data dir</label>
          <input id='sched_data_dir' name='sched_data_dir' type='text' placeholder='data' />

          <div class='row'>
            <div>
              <label for='sched_timeout'>Timeout ms</label>
              <input id='sched_timeout' name='sched_timeout_ms' type='number' placeholder='30000' min='0' />
            </div>
            <div>
              <label for='sched_settle'>Settle ms</label>
              <input id='sched_settle' name='sched_settle_ms' type='number' placeholder='5000' min='0' />
            </div>
            <div>
              <label for='sched_post_login'>Post-login ms</label>
              <input id='sched_post_login' name='sched_post_login_wait_ms' type='number' placeholder='10000' min='0' />
            </div>
          </div>

          <label>Options</label>
          <div class='checks'>
            <label><input type='checkbox' name='sched_headed' /> Headed browser</label>
            <label><input type='checkbox' name='sched_record_video' /> Record video</label>
          </div>

          <div class='row'>
            <div>
              <label for='sched_video_width'>Video width (optional)</label>
              <input id='sched_video_width' name='sched_video_width' type='number' min='1' />
            </div>
            <div>
              <label for='sched_video_height'>Video height (optional)</label>
              <input id='sched_video_height' name='sched_video_height' type='number' min='1' />
            </div>
          </div>

          <button type='submit'>Start Schedule</button>
        </form>
      </section>

      <section class='card'>
        <h2>Analysis</h2>
        <form method='POST' action='/run_analysis'>
          <label for='analysis_data_dir'>Data dir</label>
          <input id='analysis_data_dir' name='analysis_data_dir' type='text' placeholder='data' />

          <label for='analysis_site'>Site (optional)</label>
          <select id='analysis_site' name='analysis_site'>
            <option value=''>-- choose --</option>
            {data_site_select}
          </select>

          <label for='analysis_run_dir'>Run dir (optional)</label>
          <select id='analysis_run_dir' name='analysis_run_dir'>
            <option value=''>-- choose --</option>
            {run_select}
          </select>

          <label for='analysis_run_custom'>Or custom run dir</label>
          <input id='analysis_run_custom' name='analysis_run_custom' type='text' placeholder='data/my_site/20260217-172223' />

          <div class='row'>
            <div>
              <label for='analysis_start'>Start UTC (optional)</label>
              <input id='analysis_start' name='analysis_start_local' type='datetime-local' />
            </div>
            <div>
              <label for='analysis_end'>End UTC (optional)</label>
              <input id='analysis_end' name='analysis_end_local' type='datetime-local' />
            </div>
          </div>

          <label for='analysis_dom'>Max DOM chars</label>
          <input id='analysis_dom' name='analysis_max_dom_chars' type='number' placeholder='12000' min='1' />

          <label for='analysis_prompt'>Custom prompt (optional)</label>
          <textarea id='analysis_prompt' name='analysis_prompt' rows='4' placeholder='Optional analysis prompt'></textarea>

          <label for='analysis_provider'>Provider</label>
          <select id='analysis_provider' name='analysis_provider'>
            <option value='openai' selected>OpenAI</option>
            <option value='xai'>XAI</option>
          </select>

          <label for='analysis_openai_key'>OpenAI API key (optional)</label>
          <input id='analysis_openai_key' name='analysis_openai_key' type='password' placeholder='Paste OpenAI key to run analysis' />

          <label for='analysis_xai_key'>XAI API key (optional)</label>
          <input id='analysis_xai_key' name='analysis_xai_key' type='password' placeholder='Paste XAI key to run analysis' />

          <div class='status'>
            <span>{"API key found" if analysis_any_available else "No API key detected"}</span>
          </div>

          <label>Options</label>
          <div class='checks'>
            <label><input type='checkbox' name='analysis_combine_run' checked /> Combine all pages into one analysis</label>
          </div>

          <button type='submit' id='analysis_submit' data-openai-available='{str(analysis_openai_available).lower()}' data-xai-available='{str(analysis_xai_available).lower()}' disabled>Run Analysis</button>
        </form>
      </section>

      <section class='card'>
        <h2>Analysis Viewer</h2>
        <form method='GET' action='/analysis'>
          <label for='analysis_pick'>Pick analysis result</label>
          <select id='analysis_pick' name='path'>
            <option value=''>-- choose --</option>
            {analysis_select}
          </select>
          <button type='button' id='analysis_refresh'>Refresh List</button>
          <button type='submit'>View Analysis</button>
        </form>
      </section>

      <section class='card'>
        <h2>Bootstrap Logs</h2>
        <pre>{html.escape(bootstrap_log or last_bootstrap_output or "(no output yet)")}</pre>
      </section>

      <section class='card'>
        <h2>Manual Capture Logs</h2>
        <div class='status'>Status: <span id='cap_status'>{capture_status_text}</span></div>
        <div class='status'>
          <span>Started: <span id='cap_started'>{html.escape(str(capture_started))}</span></span>
          <span>Finished: <span id='cap_finished'>{html.escape(str(capture_finished))}</span></span>
          <span>Result: <span id='cap_result'>{html.escape(str(capture_result))}</span></span>
        </div>
        <pre id='cap_log'>{html.escape(last_capture_output or "(no output yet)")}</pre>
      </section>

      <section class='card'>
        <h2>Scheduled Capture Logs</h2>
        <pre>{html.escape(last_schedule_output or "(no output yet)")}</pre>
      </section>

      <section class='card'>
        <h2>Analysis Logs</h2>
        <pre>{html.escape(last_analysis_output or "(no output yet)")}</pre>
      </section>
    </div>
  </div>
  <script>
  const refreshButton = document.getElementById('analysis_refresh');
  const analysisSelect = document.getElementById('analysis_pick');
  if (refreshButton && analysisSelect) {{
    refreshButton.addEventListener('click', async () => {{
      try {{
        const response = await fetch('/analysis-list');
        if (!response.ok) {{
          return;
        }}
        const entries = await response.json();
        const current = analysisSelect.value;
        analysisSelect.innerHTML = "<option value=''>-- choose --</option>";
        entries.forEach((entry) => {{
          const option = document.createElement('option');
          option.value = entry.path;
          option.textContent = entry.label;
          analysisSelect.appendChild(option);
        }});
        analysisSelect.value = current;
      }} catch (err) {{
        console.error('Failed to refresh analysis list', err);
      }}
    }});
  }}
  const analysisProvider = document.getElementById('analysis_provider');
  const analysisOpenAIKey = document.getElementById('analysis_openai_key');
  const analysisXAIKey = document.getElementById('analysis_xai_key');
  const analysisSubmit = document.getElementById('analysis_submit');
  if (analysisProvider && analysisOpenAIKey && analysisXAIKey && analysisSubmit) {{
    const toggleSubmit = () => {{
      const provider = analysisProvider.value;
      const openaiAvailable = analysisSubmit.dataset.openaiAvailable === 'true';
      const xaiAvailable = analysisSubmit.dataset.xaiAvailable === 'true';
      const openaiKey = analysisOpenAIKey.value.trim();
      const xaiKey = analysisXAIKey.value.trim();
      if (provider === 'openai') {{
        if (openaiKey.length > 0 || openaiAvailable) {{
          analysisSubmit.removeAttribute('disabled');
          return;
        }}
      }} else if (provider === 'xai') {{
        if (xaiKey.length > 0 || xaiAvailable) {{
          analysisSubmit.removeAttribute('disabled');
          return;
        }}
      }}
      analysisSubmit.setAttribute('disabled', 'disabled');
    }};
    analysisProvider.addEventListener('change', toggleSubmit);
    analysisOpenAIKey.addEventListener('input', toggleSubmit);
    analysisXAIKey.addEventListener('input', toggleSubmit);
    toggleSubmit();
  }}
  const capListBlock = document.getElementById('cap_config_list');
  const capCustomBlock = document.getElementById('cap_config_custom_block');
  const capConfigSelect = document.getElementById('cap_config');
  const capConfigCustom = document.getElementById('cap_config_custom');
  const capModeRadios = document.querySelectorAll("input[name='cap_config_mode']");
  const toggleCapMode = () => {{
    const selected = Array.from(capModeRadios).find((el) => el.checked)?.value || 'list';
    if (selected === 'custom') {{
      capCustomBlock.style.display = 'block';
      capListBlock.style.display = 'none';
      if (capConfigSelect) {{
        capConfigSelect.value = '';
      }}
    }} else {{
      capCustomBlock.style.display = 'none';
      capListBlock.style.display = 'block';
      if (capConfigCustom) {{
        capConfigCustom.value = '';
      }}
    }}
  }};
  capModeRadios.forEach((radio) => radio.addEventListener('change', toggleCapMode));
  toggleCapMode();

  const refreshCaptureStatus = async () => {{
    try {{
      const response = await fetch('/capture-status');
      if (!response.ok) {{
        return;
      }}
      const data = await response.json();
      const status = document.getElementById('cap_status');
      const started = document.getElementById('cap_started');
      const finished = document.getElementById('cap_finished');
      const result = document.getElementById('cap_result');
      const log = document.getElementById('cap_log');
      if (status) status.textContent = data.running ? 'Running' : 'Idle';
      if (started) started.textContent = data.last_started_utc || '(none)';
      if (finished) finished.textContent = data.last_finished_utc || '(none)';
      if (result) result.textContent = data.last_result || '(none)';
      if (log) log.textContent = data.output || '(no output yet)';
    }} catch (err) {{
      console.error('Failed to refresh capture status', err);
    }}
  }};
  setInterval(refreshCaptureStatus, 2000);
  
  const stopButton = document.getElementById('stop_server_btn');
  if (stopButton) {{
    stopButton.addEventListener('click', async () => {{
      if (confirm('Stop Whistleblower server?')) {{
        try {{
          await fetch('/stop');
          setTimeout(() => {{
            window.location.href = 'about:blank';
          }}, 1000);
        }} catch (err) {{
          console.error('Failed to stop server', err);
        }}
      }}
    }});
  }}
  </script>
</body>
</html>"""


def render_analysis_page(path: str, content: str | None) -> str:
    safe_path = html.escape(path)
    body = html.escape(content) if content is not None else "(analysis file not found)"
    return f"""<!doctype html>
<html lang='en'>
<head>
  <meta charset='utf-8' />
  <meta name='viewport' content='width=device-width, initial-scale=1' />
  <title>Whistleblower Analysis</title>
  <style>
    body {{
      margin: 0;
      font-family: "IBM Plex Sans", "Avenir Next", "Segoe UI", sans-serif;
      background: #f2efe8;
      color: #111216;
      padding: 24px;
    }}
    a {{ color: #0b6d6b; text-decoration: none; }}
    pre {{
      background: #0f1217;
      color: #e8ecef;
      padding: 16px;
      border-radius: 12px;
      overflow-x: auto;
      white-space: pre-wrap;
    }}
    .path {{
      font-size: 13px;
      color: #4d4d4d;
      margin-bottom: 12px;
    }}
  </style>
</head>
<body>
  <p><a href='/'>Back to Control Room</a></p>
  <div class='path'>File: {safe_path}</div>
  <pre>{body}</pre>
</body>
</html>"""


class UIHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/":
            content = render_page()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
            return

        if self.path == "/analysis-list":
            entries = [
                {"label": label, "path": path}
                for label, path in list_analysis_entries()
            ]
            payload = json.dumps(entries)
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(payload.encode("utf-8"))
            return

        if self.path == "/capture-status":
          with STATE_LOCK:
            payload = json.dumps(
              {
                "running": CAPTURE_STATUS.get("running", False),
                "last_started_utc": CAPTURE_STATUS.get("last_started_utc", ""),
                "last_finished_utc": CAPTURE_STATUS.get("last_finished_utc", ""),
                "last_result": CAPTURE_STATUS.get("last_result", ""),
                "output": LAST_CAPTURE_OUTPUT,
              }
            )
          self.send_response(HTTPStatus.OK)
          self.send_header("Content-Type", "application/json; charset=utf-8")
          self.end_headers()
          self.wfile.write(payload.encode("utf-8"))
          return

        if self.path.startswith("/analysis"):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            path = (params.get("path") or [""])[0]
            content = load_analysis_text(path) if path else None
            page = render_analysis_page(path or "(none)", content)
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(page.encode("utf-8"))
            return

        if self.path == "/stop":
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Whistleblower stopped.</h1></body></html>")
            # Gracefully shutdown the server in a separate thread
            def shutdown_server():
                time.sleep(0.5)
                if SERVER:
                    SERVER.shutdown()
            threading.Thread(target=shutdown_server, daemon=True).start()
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        data = urllib.parse.parse_qs(raw)

        if self.path == "/run_bootstrap":
            self.handle_run_bootstrap(data)
            return
        if self.path == "/stop_bootstrap":
            self.handle_stop_bootstrap()
            return
        if self.path == "/run_capture":
            self.handle_run_capture(data)
            return
        if self.path == "/start_schedule":
          self.handle_start_schedule(data)
          return
        if self.path == "/stop_schedule":
          self.handle_stop_schedule()
          return
        if self.path == "/run_analysis":
          self.handle_run_analysis(data)
          return

        self.send_error(HTTPStatus.NOT_FOUND)

    def handle_run_bootstrap(self, data: dict[str, list[str]]) -> None:
        global BOOTSTRAP_PROCESS, BOOTSTRAP_THREAD
        url = (data.get("url") or [""])[0].strip()
        site_name = (data.get("site_name") or [""])[0].strip()
        if not url or not site_name:
            self.render_with_message("URL and site name are required.")
            return

        with STATE_LOCK:
            if BOOTSTRAP_PROCESS is not None and BOOTSTRAP_PROCESS.poll() is None:
                self.render_with_message("Bootstrap recorder is already running.")
                return
            BOOTSTRAP_LOG.clear()

        cmd = [
            sys.executable,
            "bootstrap_recorder.py",
            "--url",
            url,
            "--site-name",
            site_name,
            "--viewport-width",
            (data.get("viewport_width") or ["1920"])[0] or "1920",
            "--viewport-height",
            (data.get("viewport_height") or ["1080"])[0] or "1080",
        ]

        if "ignore_https_errors" in data:
            cmd.append("--ignore-https-errors")
        if "record_video" in data:
            cmd.append("--record-video")

        output_dir = (data.get("output_dir") or [""])[0].strip()
        if output_dir:
            cmd.extend(["--output-dir", output_dir])

        config_out = (data.get("config_out") or [""])[0].strip()
        if config_out:
            cmd.extend(["--config-out", config_out])

        steps_out = (data.get("steps_out") or [""])[0].strip()
        if steps_out:
            cmd.extend(["--steps-out", steps_out])

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        thread = start_log_thread(proc)

        with STATE_LOCK:
            BOOTSTRAP_PROCESS = proc
            BOOTSTRAP_THREAD = thread

        self.render_with_message("Bootstrap recorder started. Click stop when finished.")

    def handle_stop_bootstrap(self) -> None:
        global BOOTSTRAP_PROCESS, BOOTSTRAP_THREAD, LAST_BOOTSTRAP_OUTPUT
        with STATE_LOCK:
            proc = BOOTSTRAP_PROCESS
            thread = BOOTSTRAP_THREAD

        if proc is None or proc.poll() is not None:
            self.render_with_message("No bootstrap recorder is running.")
            return

        if proc.stdin is not None:
            try:
                proc.stdin.write("\n")
                proc.stdin.flush()
            except BrokenPipeError:
                pass

        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.terminate()
            proc.wait(timeout=10)

        if thread is not None:
            thread.join(timeout=2)

        with STATE_LOCK:
            BOOTSTRAP_PROCESS = None
            BOOTSTRAP_THREAD = None
            LAST_BOOTSTRAP_OUTPUT = "".join(BOOTSTRAP_LOG)

        self.render_with_message("Bootstrap recorder stopped.")

    def handle_run_capture(self, data: dict[str, list[str]]) -> None:
        global CAPTURE_THREAD, LAST_CAPTURE_OUTPUT
        cmd, error = build_capture_command(data)
        if cmd is None:
            self.render_with_message(error or "Unable to build capture command.")
            return
        with STATE_LOCK:
            if CAPTURE_THREAD is not None and CAPTURE_THREAD.is_alive():
                self.render_with_message("Capture already running.")
                return
            LAST_CAPTURE_OUTPUT = "Starting capture..."

        thread = threading.Thread(target=capture_worker, args=(cmd,), daemon=True)
        thread.start()

        with STATE_LOCK:
            CAPTURE_THREAD = thread

        self.render_with_message("Capture started. Check logs below for progress.")

    def handle_start_schedule(self, data: dict[str, list[str]]) -> None:
        global SCHEDULE_THREAD
        interval_raw = (data.get("sched_interval_min") or [""])[0].strip()
        if not interval_raw:
            self.render_with_message("Interval minutes is required.")
            return
        try:
            interval_minutes = int(interval_raw)
        except ValueError:
            self.render_with_message("Interval minutes must be a number.")
            return
        if interval_minutes < 1:
            self.render_with_message("Interval minutes must be >= 1.")
            return

        cmd, error = build_capture_command(data, prefix="sched_")
        if cmd is None:
            self.render_with_message(error or "Unable to build capture command.")
            return

        with STATE_LOCK:
            if SCHEDULE_THREAD is not None and SCHEDULE_THREAD.is_alive():
                self.render_with_message("Scheduled capture is already running.")
                return
            SCHEDULE_STOP.clear()

        thread = threading.Thread(target=schedule_loop, args=(cmd, interval_minutes), daemon=True)
        thread.start()

        with STATE_LOCK:
            SCHEDULE_THREAD = thread

        self.render_with_message("Scheduled capture started.")

    def handle_stop_schedule(self) -> None:
        global SCHEDULE_THREAD
        with STATE_LOCK:
            thread = SCHEDULE_THREAD
        if thread is None or not thread.is_alive():
            self.render_with_message("No scheduled capture is running.")
            return

        SCHEDULE_STOP.set()
        thread.join(timeout=5)
        with STATE_LOCK:
            SCHEDULE_THREAD = None
            SCHEDULE_STATUS["running"] = False
            SCHEDULE_STATUS["next_run_utc"] = None

        self.render_with_message("Scheduled capture stopped.")

    def handle_run_analysis(self, data: dict[str, list[str]]) -> None:
        global LAST_ANALYSIS_OUTPUT
        data_dir = (data.get("analysis_data_dir") or [""])[0].strip()
        site = (data.get("analysis_site") or [""])[0].strip()
        run_dir_custom = (data.get("analysis_run_custom") or [""])[0].strip()
        run_dir_pick = (data.get("analysis_run_dir") or [""])[0].strip()
        start_local = (data.get("analysis_start_local") or [""])[0].strip()
        end_local = (data.get("analysis_end_local") or [""])[0].strip()
        max_dom_chars = (data.get("analysis_max_dom_chars") or [""])[0].strip()
        prompt = (data.get("analysis_prompt") or [""])[0].strip()
        provider = (data.get("analysis_provider") or ["openai"])[0].strip().lower()
        if provider not in {"openai", "xai"}:
          provider = "openai"
        openai_key = (data.get("analysis_openai_key") or [""])[0].strip()
        xai_key = (data.get("analysis_xai_key") or [""])[0].strip()

        cmd = [sys.executable, "analyze_capture.py"]

        run_dir = run_dir_custom or run_dir_pick
        if run_dir:
            cmd.extend(["--run-dir", run_dir])
        if data_dir:
            cmd.extend(["--data-dir", data_dir])
        if site:
            cmd.extend(["--site", site])
        start_utc = parse_local_datetime(start_local)
        end_utc = parse_local_datetime(end_local)
        if start_local and not start_utc:
            self.render_with_message("Invalid start time.")
            return
        if end_local and not end_utc:
            self.render_with_message("Invalid end time.")
            return
        if start_utc:
            cmd.extend(["--start-utc", start_utc])
        if end_utc:
            cmd.extend(["--end-utc", end_utc])
        if max_dom_chars:
            cmd.extend(["--max-dom-chars", max_dom_chars])
        if prompt:
            cmd.extend(["--prompt", prompt])
        if "analysis_combine_run" in data:
          cmd.append("--combine-run")
        cmd.extend(["--provider", provider])

        if provider == "openai":
          provided_key = openai_key
          key_available = has_api_key_for_provider("openai")
        else:
          provided_key = xai_key
          key_available = has_api_key_for_provider("xai")

        if not provided_key and not key_available:
          self.render_with_message("API key required to run analysis.")
          return

        env = os.environ.copy()
        if provided_key:
          if provider == "openai":
            env["OPENAI_API_KEY"] = provided_key
          else:
            env["XAI_API_KEY"] = provided_key

        _, output = run_capture_command(cmd, env=env)

        with STATE_LOCK:
            LAST_ANALYSIS_OUTPUT = output

        self.render_with_message("Analysis complete.")

    def render_with_message(self, message: str) -> None:
        content = render_page(message)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))


def main() -> int:
    global SERVER
    server = HTTPServer((HOST, PORT), UIHandler)
    SERVER = server
    url = f"http://{HOST}:{PORT}"
    print(f"Whistleblower UI running at {url}")
    print("Press Ctrl+C to stop.")
    
    # Auto-launch browser in a separate thread to avoid blocking server startup
    def launch_browser():
        time.sleep(0.5)  # Give server a moment to be ready
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"Could not auto-launch browser: {e}")
    
    browser_thread = threading.Thread(target=launch_browser, daemon=True)
    browser_thread.start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        SERVER = None
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
