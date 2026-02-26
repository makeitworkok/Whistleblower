# Whistleblower Roadmap

Last updated: 2026-02-26

## Milestones

- `M1` Done: read-only capture foundation (`whistleblower.py`)
- `M2` Done: operator workflow layer (`bootstrap_recorder.py`, `ui_app.py`, `analyze_capture.py`)
- `M3` In Progress: deterministic diff artifacts between runs
- `M4` Planned: deterministic rules engine for mismatch detection
- `M5` Planned: packaging + operator-ready deployment (Windows track)
- `M6` Planned: optional local narration over deterministic findings

## Dependency Flow

- `M1 -> M2 -> M3 -> M4 -> M6`
- `M5` runs in parallel, with hardening tied to `M3` capture reliability

## Exit Criteria

### `M1` Done Criteria

- Repeatable login + navigation on representative configs.
- Per-target artifacts written each run: `screenshot.png`, `dom.json`, `meta.json`.
- Failures produce actionable error output.

### `M2` Done Criteria

- Bootstrap recorder generates starter config + step suggestions.
- Local UI supports:
  - Bootstrap recording
  - One-off capture runs
  - Scheduled capture runs
  - Run analysis (combined or per-page)
- Analysis supports OpenAI and xAI/Grok providers with run summary output.

### `M3` In Progress Criteria

- For two runs of the same site/target, produce deterministic diff output.
- Add per-target `change_report.json` with:
  - DOM/text/value delta summary
  - visual delta signal (hash or image diff summary)
  - confidence/quality flags for partial captures
- Diff behavior is stable across at least 2 representative configs.

### `M4` Planned Criteria

- Rules consume capture/diff artifacts without mutating source data.
- Initial deterministic rule pack implemented (small, high-value set).
- Rule output includes `rule_id`, `severity`, `finding`, `evidence`.

### `M5` Planned Criteria

- CLI smoke-tested on clean Windows machine.
- Minimal operator workflow packaging validated (config in, artifacts out).
- Installer/runtime docs kept in sync with shipped behavior.

### `M6` Planned Criteria

- Local narration is optional and off by default.
- Narration only summarizes deterministic findings/evidence from rules/diffs.
- Core capture/diff/rule path remains cloud-optional.

## Workstreams

- Capture reliability hardening remains highest priority.
- Diff/rules stream (`M3`/`M4`) is the main product-development path.
- Packaging stream follows `docs/windows-packaging-plan.md` in constrained spikes.

## Now / Next / Later

### Now

- Land thin `M3` vertical slice for one target with deterministic outputs.
- Keep capture artifact schema stable while diff format is introduced.
- Continue reliability fixes for hash-routed/loading-prone BAS views.
- Packaging status: Tkinter desktop UI and macOS build path live on `windows-exe` branch; Windows build/testing still pending before merge to `main`.

### Next

- Expand diff coverage from one target to full run/site coverage.
- Stand up initial deterministic rules on top of diff outputs.
- Run Windows packaging Phase 1 CLI smoke test on a clean machine.

### Later

- Expand rule library from field feedback and real failure patterns.
- Harden operator packaging path (UI + installer quality).
- Add optional local narration over deterministic findings.
