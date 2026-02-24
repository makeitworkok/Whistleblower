#!/usr/bin/env python3
"""Refactored Tkinter UI for Whistleblower - Optimized for casual BAS users."""

from __future__ import annotations

import json
import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Any

import analyze_capture
import bootstrap_recorder
import whistleblower
from site_config import (
    create_default_config,
    delete_site_config,
    get_site_setup_path,
    list_sites,
    load_site_config,
    save_site_config,
)


class WhistleblowerUIRefactored:
    """Refactored UI optimized for casual BAS users with multi-site support."""

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the UI."""
        self.root = root
        self.root.title("Whistleblower")
        self.root.geometry("1000x800")

        # Threading
        self.bootstrap_thread: threading.Thread | None = None
        self.capture_thread: threading.Thread | None = None
        self.schedule_thread: threading.Thread | None = None
        self.analysis_thread: threading.Thread | None = None
        self.schedule_running = False

        # Log queue system
        self.log_queue: queue.Queue[str] = queue.Queue()
        self.root.after(100, self._process_log_queue)

        # Current site configuration
        self.current_site: str | None = None
        self.current_config: dict[str, Any] | None = None

        # Browser selection
        self.browser_var = tk.StringVar(value="chromium")

        # Create UI
        self._create_ui()
        self._check_api_keys()

    def _create_ui(self) -> None:
        """Create main UI structure."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame, text="Whistleblower", font=("TkDefaultFont", 16, "bold")
        )
        title_label.pack(pady=10)

        # API Key Warning Banner
        self.api_warning_frame = ttk.Frame(main_frame)
        self.api_warning_frame.pack(fill=tk.X, pady=10)

        # Browser selection frame
        browser_frame = ttk.Frame(main_frame)
        browser_frame.pack(fill=tk.X, pady=5)
        ttk.Label(browser_frame, text="Browser:").pack(side=tk.LEFT, padx=5)
        for browser in ["chromium", "firefox", "webkit"]:
            ttk.Radiobutton(
                browser_frame,
                text=browser.capitalize(),
                variable=self.browser_var,
                value=browser,
            ).pack(side=tk.LEFT, padx=10)

        # Notebook with tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # Setup tab
        self.setup_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.setup_tab, text="Setup")
        self._create_setup_tab()

        # Capture tab
        self.capture_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.capture_tab, text="Capture")
        self._create_capture_tab()

        # Analysis tab
        analysis_container = ttk.Frame(self.notebook)
        self.notebook.add(analysis_container, text="Analysis")
        
        # Create scrollable analysis tab
        analysis_canvas = tk.Canvas(analysis_container, bg="white", highlightthickness=0)
        analysis_scrollbar = ttk.Scrollbar(
            analysis_container, orient="vertical", command=analysis_canvas.yview
        )
        self.analysis_tab = ttk.Frame(analysis_canvas, padding="10")
        
        self.analysis_tab.bind(
            "<Configure>",
            lambda e: analysis_canvas.configure(scrollregion=analysis_canvas.bbox("all"))
        )
        
        analysis_canvas.create_window((0, 0), window=self.analysis_tab, anchor="nw")
        analysis_canvas.configure(yscrollcommand=analysis_scrollbar.set)
        
        analysis_canvas.pack(side="left", fill="both", expand=True)
        analysis_scrollbar.pack(side="right", fill="y")
        
        def _on_mousewheel(event):
            analysis_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        analysis_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        self._create_analysis_tab()

        # Log output frame
        log_frame = ttk.LabelFrame(main_frame, text="Output Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.log_output = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, height=10, bg="black", fg="white", font=("Courier", 9)
        )
        self.log_output.pack(fill=tk.BOTH, expand=True)

    def _create_setup_tab(self) -> None:
        """Create Setup tab for site management and configuration."""
        # Site selection / management
        site_frame = ttk.LabelFrame(self.setup_tab, text="Site Management", padding="10")
        site_frame.pack(fill=tk.X, pady=10)

        ttk.Label(site_frame, text="Select Site:").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        self.site_var = tk.StringVar(value="")
        self.site_dropdown = ttk.Combobox(
            site_frame,
            textvariable=self.site_var,
            values=list_sites(),
            width=40,
            state="readonly",
        )
        self.site_dropdown.grid(row=0, column=1, padx=5, sticky="ew")
        site_frame.columnconfigure(1, weight=1)
        
        self.site_dropdown.bind("<<ComboboxSelected>>", lambda e: self._load_site())

        # Buttons
        button_frame = ttk.Frame(site_frame)
        button_frame.grid(row=0, column=2, padx=5)
        
        ttk.Button(button_frame, text="New Site", command=self._start_setup_wizard).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(button_frame, text="Edit", command=self._edit_site).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Delete", command=self._delete_site).pack(
            side=tk.LEFT, padx=2
        )

        # Current site details (read-only display)
        self.site_details_frame = ttk.LabelFrame(
            self.setup_tab, text="Current Site Configuration", padding="10"
        )
        self.site_details_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Placeholder - will be populated when site is loaded
        self.site_details_text = tk.Text(
            self.site_details_frame, height=15, width=80, state="disabled", bg="lightgray"
        )
        self.site_details_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _create_capture_tab(self) -> None:
        """Create simplified Capture tab."""
        # Site selection
        ttk.Label(self.capture_tab, text="Site:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.capture_site_var = tk.StringVar(value="")
        ttk.Combobox(
            self.capture_tab,
            textvariable=self.capture_site_var,
            values=list_sites(),
            width=40,
            state="readonly",
        ).grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        self.capture_tab.columnconfigure(1, weight=1)

        # Capture mode selection
        ttk.Label(self.capture_tab, text="Capture Mode:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.capture_mode_var = tk.StringVar(value="now")
        
        mode_frame = ttk.Frame(self.capture_tab)
        mode_frame.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(
            mode_frame,
            text="Capture Now (Single)",
            variable=self.capture_mode_var,
            value="now",
            command=self._update_capture_ui,
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Radiobutton(
            mode_frame,
            text="Schedule Recurring",
            variable=self.capture_mode_var,
            value="schedule",
            command=self._update_capture_ui,
        ).pack(side=tk.LEFT, padx=10)

        # Interval frame (hidden by default)
        self.capture_interval_frame = ttk.Frame(self.capture_tab)
        self.capture_interval_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        
        ttk.Label(self.capture_interval_frame, text="Interval (minutes):").pack(side=tk.LEFT, padx=5)
        self.capture_interval_var = tk.IntVar(value=60)
        ttk.Spinbox(
            self.capture_interval_frame, from_=1, to=1440, textvariable=self.capture_interval_var, width=10
        ).pack(side=tk.LEFT, padx=5)
        
        self.capture_interval_frame.grid_remove()

        # Start/Stop buttons
        button_frame = ttk.Frame(self.capture_tab)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        self.capture_start_btn = ttk.Button(
            button_frame, text="Start Capture", command=self._start_capture, width=20
        )
        self.capture_start_btn.pack(side=tk.LEFT, padx=10)
        
        self.capture_stop_btn = ttk.Button(
            button_frame, text="Stop", command=self._stop_capture, width=20, state="disabled"
        )
        self.capture_stop_btn.pack(side=tk.LEFT, padx=10)

    def _create_analysis_tab(self) -> None:
        """Create simplified Analysis tab."""
        # Site selection
        ttk.Label(self.analysis_tab, text="Site:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.analysis_site_var = tk.StringVar(value="")
        ttk.Combobox(
            self.analysis_tab,
            textvariable=self.analysis_site_var,
            values=list_sites(),
            width=40,
            state="readonly",
        ).grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        self.analysis_tab.columnconfigure(1, weight=1)

        # Date range (optional)
        date_frame = ttk.LabelFrame(self.analysis_tab, text="Date Range Filter (Optional)", padding="5")
        date_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=10)
        date_frame.columnconfigure(1, weight=1)
        date_frame.columnconfigure(3, weight=1)
        
        ttk.Label(date_frame, text="Start (YYYY-MM-DD HH:MM):").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.analysis_start_utc = tk.StringVar(value="")
        ttk.Entry(date_frame, textvariable=self.analysis_start_utc, width=25).grid(
            row=0, column=1, padx=5, sticky="ew"
        )
        
        ttk.Label(date_frame, text="End (YYYY-MM-DD HH:MM):").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.analysis_end_utc = tk.StringVar(value="")
        ttk.Entry(date_frame, textvariable=self.analysis_end_utc, width=25).grid(
            row=0, column=3, padx=5, sticky="ew"
        )

        # Advanced options toggle
        self.analysis_advanced_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.analysis_tab,
            text="Show Advanced Options",
            variable=self.analysis_advanced_var,
            command=self._toggle_analysis_advanced,
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Advanced options (hidden by default)
        self.analysis_advanced_frame = ttk.LabelFrame(
            self.analysis_tab, text="Advanced Options", padding="5"
        )
        self.analysis_advanced_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)
        self.analysis_advanced_frame.grid_remove()
        
        ttk.Label(self.analysis_advanced_frame, text="Max DOM chars:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.analysis_max_dom = tk.IntVar(value=12000)
        ttk.Spinbox(
            self.analysis_advanced_frame, from_=1000, to=50000, increment=1000, textvariable=self.analysis_max_dom, width=10
        ).grid(row=0, column=1, padx=5)
        
        self.analysis_combine = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.analysis_advanced_frame,
            text="Combine run (single analysis)",
            variable=self.analysis_combine,
        ).grid(row=0, column=2, sticky=tk.W, padx=5)

        # Start button
        self.analysis_btn = ttk.Button(
            self.analysis_tab, text="Start Analysis", command=self._start_analysis, width=20
        )
        self.analysis_btn.grid(row=4, column=0, columnspan=2, pady=20)

    def _update_capture_ui(self) -> None:
        """Update capture UI based on selected mode."""
        if self.capture_mode_var.get() == "schedule":
            self.capture_interval_frame.grid()
        else:
            self.capture_interval_frame.grid_remove()

    def _toggle_analysis_advanced(self) -> None:
        """Toggle advanced analysis options visibility."""
        if self.analysis_advanced_var.get():
            self.analysis_advanced_frame.grid()
        else:
            self.analysis_advanced_frame.grid_remove()

    def _load_site(self) -> None:
        """Load selected site configuration."""
        site_name = self.site_var.get()
        if not site_name:
            return

        config = load_site_config(site_name)
        if config:
            self.current_site = site_name
            self.current_config = config
            self._display_site_details(config)
            # Also update capture and analysis dropdowns
            self.capture_site_var.set(site_name)
            self.analysis_site_var.set(site_name)
            self._show_initialize_button()

    def _show_initialize_button(self) -> None:
        """Show Initialize Site button if site is loaded."""
        # Clear old button if exists
        for widget in self.setup_tab.winfo_children():
            if isinstance(widget, ttk.Button) and widget.cget("text") == "Initialize Site":
                widget.destroy()
        
        # Add button to initialize site
        init_button = ttk.Button(
            self.setup_tab,
            text="Initialize Site",
            command=self._initialize_site,
        )
        init_button.pack(pady=10)

    def _display_site_details(self, config: dict[str, Any]) -> None:
        """Display site configuration in read-only text area."""
        self.site_details_text.config(state="normal")
        self.site_details_text.delete(1.0, tk.END)
        
        details = f"""Site Name: {config.get('site_name')}
Bootstrap URL: {config.get('bootstrap_url')}

Viewport: {config['viewport']['width']} x {config['viewport']['height']}
Ignore HTTPS Errors: {config.get('ignore_https_errors')}
Browser: {config.get('browser')}

Directories:
  Bootstrap: {config['directories']['bootstrap_artifacts']}
  Capture: {config['directories']['capture_data']}
  Analysis: {config['directories']['analysis_output']}

Capture Settings:
  Timeout: {config['capture_settings']['timeout_ms']}ms
  Settle: {config['capture_settings']['settle_ms']}ms
  Video: {config['capture_settings']['record_video']}

Analysis Settings:
  Provider: {config['analysis_settings']['provider']}
  Max DOM: {config['analysis_settings']['max_dom_chars']}
  Combine: {config['analysis_settings']['combine_run']}
"""
        self.site_details_text.insert(1.0, details)
        self.site_details_text.config(state="disabled")

    def _start_setup_wizard(self) -> None:
        """Launch setup wizard for new site."""
        wizard_window = tk.Toplevel(self.root)
        wizard_window.title("Setup New Site")
        wizard_window.geometry("600x400")
        wizard_window.grab_set()

        # Step 1: Site Name and URL
        ttk.Label(wizard_window, text="Site Name:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=10)
        site_name_var = tk.StringVar(value="")
        ttk.Entry(wizard_window, textvariable=site_name_var, width=40).grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(wizard_window, text="Bootstrap URL:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        url_var = tk.StringVar(value="https://")
        ttk.Entry(wizard_window, textvariable=url_var, width=40).grid(row=1, column=1, padx=10, pady=10)

        # Step 2: Viewport
        ttk.Label(wizard_window, text="Viewport Width:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=10)
        width_var = tk.IntVar(value=1920)
        ttk.Spinbox(wizard_window, from_=640, to=3840, increment=160, textvariable=width_var, width=10).grid(
            row=2, column=1, sticky=tk.W, padx=10
        )

        ttk.Label(wizard_window, text="Viewport Height:").grid(row=3, column=0, sticky=tk.W, padx=10, pady=10)
        height_var = tk.IntVar(value=1080)
        ttk.Spinbox(wizard_window, from_=480, to=2160, increment=108, textvariable=height_var, width=10).grid(
            row=3, column=1, sticky=tk.W, padx=10
        )

        # Step 3: Options
        ttk.Label(wizard_window, text="Ignore HTTPS Errors:").grid(row=4, column=0, sticky=tk.W, padx=10, pady=10)
        ignore_https_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(wizard_window, variable=ignore_https_var).grid(row=4, column=1, sticky=tk.W, padx=10)

        # Buttons
        button_frame = ttk.Frame(wizard_window)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)

        def _save_site():
            site_name = site_name_var.get().strip()
            url = url_var.get().strip()
            
            if not site_name or not url:
                messagebox.showerror("Error", "Site name and URL are required")
                return
            
            config = create_default_config(
                site_name=site_name,
                bootstrap_url=url,
                viewport_width=width_var.get(),
                viewport_height=height_var.get(),
                ignore_https_errors=ignore_https_var.get(),
            )
            
            save_site_config(site_name, config)
            self._log(f"✓ Site '{site_name}' created successfully")
            
            # Refresh dropdown
            self.site_dropdown["values"] = list_sites()
            self.capture_site_var.set(site_name)
            self.analysis_site_var.set(site_name)
            self.site_var.set(site_name)
            self._load_site()
            
            wizard_window.destroy()

        ttk.Button(button_frame, text="Create Site", command=_save_site, width=20).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=wizard_window.destroy, width=20).pack(side=tk.LEFT, padx=10)

    def _edit_site(self) -> None:
        """Edit current site configuration."""
        if not self.current_site:
            messagebox.showwarning("Warning", "Please select a site first")
            return
        
        # For now, show a message that editing is available via setup wizard
        messagebox.showinfo("Info", f"To edit '{self.current_site}', create a new site or delete and recreate.")

    def _delete_site(self) -> None:
        """Delete selected site."""
        site_name = self.site_var.get()
        if not site_name:
            messagebox.showwarning("Warning", "Please select a site first")
            return
        
        if messagebox.askyesno("Confirm", f"Delete site '{site_name}'?"):
            delete_site_config(site_name)
            self._log(f"✓ Site '{site_name}' deleted")
            
            self.site_dropdown["values"] = list_sites()
            self.site_var.set("")
            self.current_site = None
            self.current_config = None
            self.site_details_text.config(state="normal")
            self.site_details_text.delete(1.0, tk.END)
            self.site_details_text.config(state="disabled")

    def _initialize_site(self) -> None:
        """Initialize site by running bootstrap."""
        if not self.current_site or not self.current_config:
            messagebox.showerror("Error", "No site selected")
            return
        
        if self.bootstrap_thread and self.bootstrap_thread.is_alive():
            messagebox.showwarning("Warning", "Bootstrap is already running")
            return
        
        self._log(f"=== Initializing Site: {self.current_site} ===")
        
        self.bootstrap_thread = threading.Thread(
            target=self._run_bootstrap_thread,
            args=(self.current_site, self.current_config),
            daemon=True,
        )
        self.bootstrap_thread.start()

    def _run_bootstrap_thread(self, site_name: str, config: dict[str, Any]) -> None:
        """Run bootstrap in background thread."""
        try:
            self._log(f"Initializing {site_name} with URL: {config['bootstrap_url']}")
            self._log("This may take a few minutes...")
            
            result = bootstrap_recorder.run_bootstrap(
                url=config["bootstrap_url"],
                site_name=site_name,
                output_dir=config["directories"]["bootstrap_artifacts"],
                viewport_width=config["viewport"]["width"],
                viewport_height=config["viewport"]["height"],
                ignore_https_errors=config["ignore_https_errors"],
                record_video=False,
                browser_type=self.browser_var.get(),
            )
            
            self._log(f"✓ Site initialized successfully!")
            self._log(f"Configuration: {result['config_out']}")
            self._log(f"Steps: {result['steps_out']}")
            messagebox.showinfo("Success", f"Site '{site_name}' initialized. Ready to capture.")
        except Exception as exc:
            self._log(f"ERROR: {exc}")
            messagebox.showerror("Error", f"Bootstrap failed: {exc}")

    def _start_capture(self) -> None:
        """Start capture (now or schedule)."""
        site_name = self.capture_site_var.get()
        if not site_name:
            messagebox.showerror("Error", "Please select a site")
            return
        
        config = load_site_config(site_name)
        if not config:
            messagebox.showerror("Error", f"Could not load config for '{site_name}'")
            return
        
        if self.capture_mode_var.get() == "now":
            self._do_single_capture(site_name, config)
        else:
            self._start_schedule(site_name, config)

    def _do_single_capture(self, site_name: str, config: dict[str, Any]) -> None:
        """Execute single capture."""
        if self.capture_thread and self.capture_thread.is_alive():
            messagebox.showwarning("Warning", "Capture is already running")
            return
        
        self.capture_start_btn.config(state="disabled")
        self._log(f"=== Starting Capture for {site_name} ===")
        
        self.capture_thread = threading.Thread(
            target=self._run_capture_thread,
            args=(site_name, config),
            daemon=True,
        )
        self.capture_thread.start()

    def _run_capture_thread(self, site_name: str, config: dict[str, Any]) -> None:
        """Run capture in background thread."""
        try:
            capture_settings = config["capture_settings"]
            bootstrap_file = Path(config["directories"]["bootstrap_artifacts"]) / f"{site_name}.bootstrap.json"
            
            if not bootstrap_file.exists():
                self._log(f"ERROR: Bootstrap file not found: {bootstrap_file}")
                messagebox.showerror("Error", f"Bootstrap file not found. Initialize site first.")
                return
            
            self._log(f"Running capture for {site_name}...")
            result = whistleblower.run_capture(
                config_path=str(bootstrap_file),
                data_dir=config["directories"]["capture_data"],
                timeout_ms=capture_settings["timeout_ms"],
                settle_ms=capture_settings["settle_ms"],
                post_login_wait_ms=capture_settings["post_login_wait_ms"],
                headed=capture_settings["headed"],
                record_video=capture_settings["record_video"],
                video_width=capture_settings["video_width"],
                video_height=capture_settings["video_height"],
            )
            
            self._log(f"✓ Capture complete!")
            self._log(f"Targets captured: {result['targets_captured']}")
            self._log(f"Run directory: {result['run_dir']}")
            messagebox.showinfo("Success", "Capture completed successfully")
        except Exception as exc:
            self._log(f"ERROR: {exc}")
            messagebox.showerror("Error", f"Capture failed: {exc}")
        finally:
            self.root.after(0, lambda: self.capture_start_btn.config(state="normal"))

    def _start_schedule(self, site_name: str, config: dict[str, Any]) -> None:
        """Start scheduled recurring captures."""
        if self.schedule_thread and self.schedule_thread.is_alive():
            messagebox.showwarning("Warning", "Schedule is already running")
            return
        
        self.schedule_running = True
        self.capture_start_btn.config(state="disabled")
        self.capture_stop_btn.config(state="normal")
        interval_minutes = self.capture_interval_var.get()
        
        self._log(f"=== Starting Schedule for {site_name} ===")
        self._log(f"Interval: {interval_minutes} minutes")
        
        self.schedule_thread = threading.Thread(
            target=self._run_schedule_thread,
            args=(site_name, config, interval_minutes),
            daemon=True,
        )
        self.schedule_thread.start()

    def _run_schedule_thread(self, site_name: str, config: dict[str, Any], interval_minutes: int) -> None:
        """Run scheduled captures in background."""
        import time
        
        interval_seconds = interval_minutes * 60
        counter = interval_seconds
        
        while self.schedule_running:
            remaining_min = counter // 60
            remaining_sec = counter % 60
            status = f"Next capture in {remaining_min}m {remaining_sec}s"
            self.root.after(0, lambda: self._log(status, replace_last=True))
            
            if counter <= 0:
                try:
                    self._log(f"Running scheduled capture for {site_name}...")
                    capture_settings = config["capture_settings"]
                    bootstrap_file = Path(config["directories"]["bootstrap_artifacts"]) / f"{site_name}.bootstrap.json"
                    
                    if bootstrap_file.exists():
                        result = whistleblower.run_capture(
                            config_path=str(bootstrap_file),
                            data_dir=config["directories"]["capture_data"],
                            timeout_ms=capture_settings["timeout_ms"],
                            settle_ms=capture_settings["settle_ms"],
                            post_login_wait_ms=capture_settings["post_login_wait_ms"],
                            headed=capture_settings["headed"],
                            record_video=capture_settings["record_video"],
                            video_width=capture_settings["video_width"],
                            video_height=capture_settings["video_height"],
                        )
                        self._log(f"✓ Scheduled capture complete: {result['targets_captured']} targets")
                    else:
                        self._log(f"WARNING: Bootstrap file not found, skipping capture")
                    
                    counter = interval_seconds
                except Exception as exc:
                    self._log(f"ERROR in scheduled capture: {exc}")
            
            time.sleep(1)
            counter -= 1

    def _stop_capture(self) -> None:
        """Stop scheduled captures."""
        self.schedule_running = False
        self.capture_stop_btn.config(state="disabled")
        self.capture_start_btn.config(state="normal")
        self._log("Schedule stopped")

    def _start_analysis(self) -> None:
        """Start analysis."""
        site_name = self.analysis_site_var.get()
        if not site_name:
            messagebox.showerror("Error", "Please select a site")
            return
        
        config = load_site_config(site_name)
        if not config:
            messagebox.showerror("Error", f"Could not load config for '{site_name}'")
            return
        
        # Check API key
        provider = config["analysis_settings"]["provider"]
        api_key = config["api_keys"].get(f"{provider}_key", "").strip()
        api_key = api_key or os.getenv(
            "OPENAI_API_KEY" if provider == "openai" else "XAI_API_KEY"
        )
        
        if not api_key:
            messagebox.showerror(
                "Error",
                f"{provider.upper()} API key required. Configure in Setup tab or set environment variable.",
            )
            return
        
        if self.analysis_thread and self.analysis_thread.is_alive():
            messagebox.showwarning("Warning", "Analysis is already running")
            return
        
        self.analysis_btn.config(state="disabled")
        self._log("=== Starting Analysis ===")
        self._log(f"Site: {site_name}, Provider: {provider}")
        
        self.analysis_thread = threading.Thread(
            target=self._run_analysis_thread,
            args=(site_name, config, provider, api_key),
            daemon=True,
        )
        self.analysis_thread.start()

    def _run_analysis_thread(
        self, site_name: str, config: dict[str, Any], provider: str, api_key: str
    ) -> None:
        """Run analysis in background thread."""
        try:
            self._log("Running LLM analysis...")
            result = analyze_capture.run_analysis(
                site=site_name,
                data_dir=config["directories"]["analysis_output"],
                start_utc=self.analysis_start_utc.get().strip() or None,
                end_utc=self.analysis_end_utc.get().strip() or None,
                provider=provider,
                api_key=api_key,
                max_dom_chars=self.analysis_max_dom.get(),
                combine_run=self.analysis_combine.get(),
            )
            self._log(f"✓ Analysis complete!")
            self._log(f"Runs analyzed: {result['runs_analyzed']}")
            self._log(result["message"])
            messagebox.showinfo("Success", "Analysis completed successfully")
        except Exception as exc:
            self._log(f"ERROR: {exc}")
            messagebox.showerror("Error", f"Analysis failed: {exc}")
        finally:
            self.root.after(0, lambda: self.analysis_btn.config(state="normal"))

    def _check_api_keys(self) -> None:
        """Check and display API key status."""
        openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        xai_key = os.getenv("XAI_API_KEY", "").strip()
        
        if not openai_key and not xai_key:
            # Show warning banner
            warning_frame = ttk.Frame(self.api_warning_frame, relief=tk.RIDGE, borderwidth=2)
            warning_frame.pack(fill=tk.X)
            
            warning_text = ttk.Label(
                warning_frame,
                text="⚠ WARNING: No API key detected. Analysis won't work.",
                foreground="red",
                font=("TkDefaultFont", 10, "bold"),
            )
            warning_text.pack(pady=10, padx=10)
            
            help_text = ttk.Label(
                warning_frame,
                text="See README.md 'API Keys for Analysis' section for setup instructions",
                foreground="darkred",
            )
            help_text.pack(pady=5, padx=10)
        else:
            keys_found = []
            if openai_key:
                keys_found.append("OpenAI")
            if xai_key:
                keys_found.append("xAI")
            
            ok_frame = ttk.Frame(self.api_warning_frame)
            ok_frame.pack(fill=tk.X)
            
            ok_text = ttk.Label(
                ok_frame,
                text=f"✓ API Keys found: {', '.join(keys_found)}",
                foreground="green",
            )
            ok_text.pack(pady=5, padx=10)

    def _log(self, message: str, replace_last: bool = False) -> None:
        """Add message to log (thread-safe)."""
        self.log_queue.put(("append", message, replace_last))

    def _process_log_queue(self) -> None:
        """Process log messages from queue."""
        try:
            while True:
                action, message, replace_last = self.log_queue.get_nowait()
                
                if action == "append":
                    self.log_output.config(state="normal")
                    if replace_last:
                        # Remove last line
                        last_line_start = self.log_output.index("end-2l linestart")
                        self.log_output.delete(last_line_start, tk.END)
                    
                    self.log_output.insert(tk.END, message + "\n")
                    self.log_output.see(tk.END)
                    self.log_output.config(state="disabled")
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._process_log_queue)


def main() -> None:
    """Main entry point."""
    root = tk.Tk()
    app = WhistleblowerUIRefactored(root)
    root.mainloop()


if __name__ == "__main__":
    main()
