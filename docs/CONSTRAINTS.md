# Whistleblower Constraints (Non-Negotiable)

- Read-only forever. No write-backs. No clicks that change state intentionally.
- No protocol stacks (BACnet/Modbus/Lon), no vendor SDKs, no Niagara APIs.
- Use only the existing web UI via Playwright.
- Runs fully local: no cloud, no telemetry, no phoning home.
- Works via minimal per-site config (URLs + selectors). Zero-config is not required.
- Outputs inspectable artifacts: screenshots + DOM snapshot + meta.
- Deterministic rules decide anomalies; AI (if added) only narrates findings.
- Must run in Docker.
