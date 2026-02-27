# Whistleblower User Manual

This guide walks you through exactly what to do after launching Whistleblower for the first time.

## What You Should Expect at Launch

When Whistleblower opens, you will see:

- A desktop window with tabs: Setup, Site Management, Capture, Analysis
- An output log panel at the bottom (this shows live progress and errors)
- Default settings already filled for browser and viewport

If the app takes 10-30 seconds to fully become responsive on first run, that is normal.

## 1) Setup Tab (Do This First)

The Setup tab controls API keys and base runtime settings.

### API Keys for Analysis (Optional)

If you want AI analysis reports:

1. Paste your OpenAI key into OpenAI API Key
2. (Optional) Paste your xAI key into xAI API Key
3. Click Save API Keys
4. Confirm status changes to Configured

If you do not add an API key, capture still works. You just will not get AI-generated analysis summaries.

### Basic Settings

Set these before your first capture:

- Default Browser: Choose Chromium for best compatibility
- Default Viewport: Keep 1920x1080 unless your site needs a different layout
- Ignore HTTPS errors: Keep enabled for internal BAS systems with self-signed certs

### Advanced Options (Optional)

Enable Show Advanced Options only if you know you need custom behavior. Most users can leave these at default.

## 2) Site Management Tab (Define What to Capture)

This is where you create or load site configurations.

### Option A: Use an Existing Template

1. Open Site Management
2. Load an existing template from the sites folder
3. Review base URL, login path, and capture targets

### Option B: Create a New Site

1. Click to create a new site config
2. Enter a clear site name (example: Building_A_HVAC)
3. Add login URL and credentials fields
4. Add one or more target pages to capture
5. Save the configuration

Tip: Start small with 1-2 critical pages. Expand after first successful run.

## 3) Capture Tab (Run Your First Evidence Capture)

The Capture tab executes browser automation and stores artifacts locally.

### First Capture Workflow

1. Select your site configuration
2. Confirm capture targets are correct
3. Click Start Capture
4. Watch the Output Log for progress:
   - Browser launch
   - Login step
   - Navigation to target pages
   - Screenshot and data extraction

### Stop Recording Correctly

When you are done recording, always stop from the Whistleblower app controls.

1. Click Stop Recording (or Stop Capture) in the app
2. Wait for the Output Log to show completion/finished messages
3. Confirm the timestamped output folder was created

Important: do not just close the browser window or browser tab and expect a valid result. Closing the browser directly can interrupt final save/flush steps and produce incomplete output.

A successful run creates timestamped folders in `data/site-name/timestamp/` with screenshots, metadata, and extracted DOM text.

## 4) Analysis Tab (Optional, But Powerful)

Use this tab after capture completes.

### Standard Analysis

1. Select a recent capture folder
2. Choose analysis provider (if API key is configured)
3. Run analysis
4. Review generated report output

### Personality-Based Analysis (Advanced)

You can enable one or more analysis personalities:

- BoilerBob: Mechanical issues and equipment behavior
- ConservationCasey: Energy waste and efficiency opportunities
- DirectorDave: ROI and payback framing
- GraphicalGary (experimental): UI consistency and standards checks

You can also enter a custom question to focus analysis on a specific concern.

## 5) Understand Output and Files

Whistleblower is local-first and evidence-focused.

Typical output contents include:

- screenshot.png: page evidence image
- dom.json: extracted visible text/data
- meta.json: run context, timing, page details
- analysis.md: AI-generated findings (if analysis was enabled)

All files remain on your machine unless you manually move them elsewhere.

## 6) Daily Operating Pattern (Recommended)

For reliable operations, use this routine:

1. Validate one manual capture after UI or config changes
2. Run scheduled captures on critical pages
3. Review analysis and exceptions daily or weekly
4. Archive old capture folders monthly

## 7) Common First-Run Issues

### App opens but capture fails to login

- Verify URL is correct and reachable
- Check username/password and account status
- Confirm MFA or SSO prompts are handled in your workflow

### Browser launches but pages never fully load

- Try Chromium first
- Increase waits/timeouts in advanced settings
- Validate internal network latency and DNS resolution

### I closed the browser and no result was saved

- Re-run the capture and stop it from the app controls, not the browser window
- Wait for completion in the Output Log before starting analysis
- Verify the newest timestamped folder exists before moving to Analysis

### No analysis generated

- Confirm API key is saved and marked configured
- Check provider availability and billing status
- Re-run analysis on a completed capture folder

## 8) Safety and Access Guidelines

- Use read-only BAS credentials only
- Never grant command/override permissions
- Treat captured evidence as sensitive operational data
- Limit access to output folders to authorized staff

## Quick Start Checklist

- [ ] Open Setup tab and save API key (optional)
- [ ] Confirm browser and viewport defaults
- [ ] Load or create one site configuration
- [ ] Run first capture on 1-2 pages
- [ ] Verify output folder and screenshots
- [ ] Run one analysis report

Once this checklist is complete, you are ready to scale captures across more systems.
