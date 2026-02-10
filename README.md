# Whistleblower

**Whistleblower** is a read-only watchdog for building automation systems.

It logs into existing BAS web interfaces (Niagara, Metasys, Tracer, Honeywell, Siemens, Distech, etc), captures what the operator sees, and preserves evidence when the graphics don’t line up with reality.

No write-backs.  
No drivers.  
No vendor SDKs.  
No cloud.  
No subscriptions.  

Just screenshots, DOM snapshots, and receipts.

---

## What Whistleblower does (right now)

- Automates login to a BAS web UI  
- Navigates to configured dashboard / graphics pages  
- Captures:
  - full-page screenshots  
  - visible DOM text and stateful elements  
- Stores everything locally for later comparison and analysis  

This is intentionally **read-only** and **vendor-agnostic**.

---

## What it deliberately does NOT do

- ❌ No setpoint changes  
- ❌ No BACnet / Modbus / Lon stacks  
- ❌ No Niagara SDKs or vendor APIs  
- ❌ No cloud services or telemetry  
- ❌ No phoning home  

If your BAS UI lies, Whistleblower documents it.  
What you do with that information is up to you.

---

## Requirements

- Docker (Linux, macOS, or Windows)  
- Access credentials to the BAS web interface you want to observe  
- Internet access during image build (to pull base image + Python deps)  

That’s it.

---

## Repository layout

```
whistleblower/
- Dockerfile
- requirements.txt
- whistleblower.py
- sites/
  - example.json
- data/
  - .gitkeep
- README.md
- LICENSE
```
	•	sites/ → site-specific configs (URLs, selectors, credentials)
	•	data/ → screenshots + DOM snapshots written at runtime

⸻

Quick start

1. Clone the repo

```
git clone https://github.com/makeitworkok/Whistleblower.git
cd Whistleblower
```

2. Create output directory

```
mkdir -p data
```
3. Build the container
```
docker build -t whistleblower .
```
The first build can take a while because it pulls browser dependencies.

4. Create a private local config (not committed)

```
cp sites/example.json sites/local.json
```
Then edit `sites/local.json` with your real URL, credentials, and selectors.

5. Run against your local config

Linux / macOS
```
docker run --rm \
  -v "$(pwd)/sites:/app/sites" \
  -v "$(pwd)/data:/app/data" \
  whistleblower --config /app/sites/local.json
```
Windows PowerShell
```
docker run --rm `
  -v "${PWD}\sites:/app/sites" `
  -v "${PWD}\data:/app/data" `
  whistleblower --config /app/sites/local.json
```

⸻

Output

After a run, you’ll see something like:
```
data/
└── testsite/
    └── 20260209-134512/
        └── main_dashboard/
            ├── screenshot.png
            ├── dom.json
            └── meta.json
```
Each run is timestamped. Nothing is overwritten.

⸻

Configuration

Site configs live in sites/*.json.

You will need to provide:
	•	login URL
	•	username / password
	•	CSS selectors for login fields
	•	one or more pages to capture

This is intentional. BAS UIs are inconsistent, and pretending otherwise is a lie.

See sites/example.json for the minimal required structure.

⸻

Status

This project is early and intentionally simple.

Current focus:
	•	reliable navigation
	•	reliable capture
	•	clean, inspectable artifacts

Future work (not yet implemented):
	•	change detection between runs
	•	rule-based detection of “graphics lying”
	•	optional local AI narration (still read-only)

No timelines. No promises. Just steady progress.

⸻

License

MIT.
Use it, fork it, break it, fix it.
