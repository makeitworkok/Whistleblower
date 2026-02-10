# Whistleblower

Whistleblower is a read-only watchdog for building automation systems.

It logs into existing BAS web interfaces (Niagara, Metasys, Tracer, Honeywell, Siemens, Distech, etc), captures what the operator sees, and flags obvious inconsistencies that experienced techs spot instantly but software vendors pretend don’t exist.

No write-backs.  
No drivers.  
No SDKs.  
No cloud.  
No subscriptions.

Just screenshots, DOM snapshots, and the truth.

## What it does (right now)

- Automates login to a BAS web UI
- Navigates to configured graphics / dashboard pages
- Captures:
  - full-page screenshots
  - visible DOM text and stateful elements
- Stores artifacts locally for comparison and analysis

## What it deliberately does NOT do

- No setpoint changes
- No BACnet / Lon / Modbus stacks
- No vendor APIs
- No telemetry
- No phoning home

If your BAS UI lies to you, Whistleblower documents it.

## Quick start

### Build
```bash
docker build -t whistleblower .
