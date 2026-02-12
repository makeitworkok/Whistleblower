# 🗺️ Whistleblower Roadmap

## 🎯 Milestones

- ✅ `M1` (Done): login + capture artifacts
- 🔧 `M2` (In Progress): baseline + diff
- 📐 `M3` (Planned): deterministic rules engine for "graphics lying"
- 🧠 `M4` (Planned): optional local narration (Ollama/AnythingLLM)

## 🔗 Dependency Flow

- `M1 -> M2 -> M3 -> M4`
- Windows packaging track runs in parallel, but only hardens after `M2` reliability is stable.

## ✅ Exit Criteria

### ✅ M1 Exit Criteria (Complete)

- Repeatable login + navigation on representative configs.
- Per-target artifacts written each run: `screenshot.png`, `dom.json`, `meta.json`.
- Failures produce actionable error output.

### 🔧 M2 Exit Criteria (Current Focus)

- For two runs of the same site/target, produce deterministic diff output.
- Add per-target `change_report.json` with at least content changes (DOM/text/value deltas), a visual change signal (hash or image-diff summary), and confidence/quality flags for partial captures.
- Diff behavior is stable across at least 2 representative configs.

### 📐 M3 Exit Criteria

- Rules consume captured/diff artifacts without mutating source data.
- Initial deterministic rule pack implemented (small, high-value set).
- Rule output clearly separates `finding`, `evidence`, `severity`, and `rule_id`.

### 🧠 M4 Exit Criteria

- Local narration is optional and off by default.
- Narration only summarizes deterministic findings/evidence.
- No cloud dependency required for core operation.

## 🛠️ Workstreams (All Active, Different Intensity)

- Core reliability (`M2`) is default stream and highest priority.
- Rules stream (`M3`) starts thin, using current artifacts to validate rule shape early.
- Packaging stream runs as constrained spikes per `docs/windows-packaging-plan.md`.

## ⏱️ Now / Next / Later

### 🟢 Now

- Implement thin `M2` vertical slice: compare two runs for one target, output one `change_report.json`, and verify deterministic behavior on existing demo runs.
- Keep capture schema stable while this lands.

### 🟡 Next

- Expand `M2` from one target to full run/site coverage.
- Stand up `M3` thin rule set on top of diff outputs.
- Execute Windows packaging Phase 1 smoke test (CLI-only on clean Windows machine).

### 🔵 Later

- Grow deterministic rule library based on field feedback.
- Add optional local narration for findings (`M4`).
- Move packaging from smoke test to minimal GUI + installer hardening.
