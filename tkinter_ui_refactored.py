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
        self.bootstrap_running = False

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

    def _create_ui(self) -> None:
        """Create main UI structure."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame, text="Whistleblower", font=("TkDefaultFont", 16, "bold")
        )
        title_label.pack(pady=10)

        # Notebook with tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # Setup tab (API keys and settings)
        self.settings_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.settings_tab, text="Setup")
        self._create_settings_tab()

        # Site Management tab (site creation and management)
        self.site_management_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.site_management_tab, text="Site Management")
        self._create_site_management_tab()

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

    def _create_settings_tab(self) -> None:
        """Create Settings tab for API keys and basic configuration."""
        # API Keys section
        api_frame = ttk.LabelFrame(self.settings_tab, text="API Keys for Analysis", padding="10")
        api_frame.pack(fill=tk.X, pady=10)

        # Load stored API keys (from .env file or environment)
        import os
        from pathlib import Path
        
        env_file = Path.home() / ".whistleblower_env"
        stored_keys = {}
        if env_file.exists():
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        stored_keys[key.strip()] = value.strip()
        
        # Get current keys from environment
        openai_key = os.getenv("OPENAI_API_KEY", stored_keys.get("OPENAI_API_KEY", "")).strip()
        xai_key = os.getenv("XAI_API_KEY", stored_keys.get("XAI_API_KEY", "")).strip()
        
        # OpenAI Key
        openai_frame = ttk.Frame(api_frame)
        openai_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(openai_frame, text="OpenAI API Key:", width=15).pack(side=tk.LEFT, padx=5)
        self.openai_key_var = tk.StringVar(value=openai_key if openai_key else "")
        openai_entry = ttk.Entry(openai_frame, textvariable=self.openai_key_var, width=50, show="*")
        openai_entry.pack(side=tk.LEFT, padx=5)
        
        self.openai_status_label = ttk.Label(openai_frame, text="")
        self.openai_status_label.pack(side=tk.LEFT, padx=5)
        
        # xAI Key
        xai_frame = ttk.Frame(api_frame)
        xai_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(xai_frame, text="xAI API Key:", width=15).pack(side=tk.LEFT, padx=5)
        self.xai_key_var = tk.StringVar(value=xai_key if xai_key else "")
        xai_entry = ttk.Entry(xai_frame, textvariable=self.xai_key_var, width=50, show="*")
        xai_entry.pack(side=tk.LEFT, padx=5)
        
        self.xai_status_label = ttk.Label(xai_frame, text="")
        self.xai_status_label.pack(side=tk.LEFT, padx=5)
        
        # Update status after both vars are created
        self._update_api_status()
        
        # Save button
        button_frame = ttk.Frame(api_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Save API Keys", command=self._save_api_keys, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Label(button_frame, text="Keys are securely stored in your home directory", 
                 foreground="gray", font=("TkDefaultFont", 9)).pack(side=tk.LEFT, padx=10)
        
        # Info text
        ttk.Label(api_frame, text="Get keys from: OpenAI (platform.openai.com) or xAI (console.x.ai)", 
                 foreground="darkblue", wraplength=600, font=("TkDefaultFont", 9)).pack(anchor=tk.W, padx=5, pady=5)

        # Basic Settings section
        basic_frame = ttk.LabelFrame(self.settings_tab, text="Basic Settings", padding="10")
        basic_frame.pack(fill=tk.X, pady=10)

        # Browser selection
        ttk.Label(basic_frame, text="Default Browser:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        browser_frame = ttk.Frame(basic_frame)
        browser_frame.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        for browser in ["chromium", "firefox", "webkit"]:
            ttk.Radiobutton(
                browser_frame,
                text=browser.capitalize(),
                variable=self.browser_var,
                value=browser,
            ).pack(side=tk.LEFT, padx=10)

        # Default viewport
        ttk.Label(basic_frame, text="Default Viewport:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        viewport_frame = ttk.Frame(basic_frame)
        viewport_frame.grid(row=1, column=1, sticky=tk.W, padx=5)
        
        self.default_viewport_width = tk.IntVar(value=1920)
        self.default_viewport_height = tk.IntVar(value=1080)
        
        ttk.Label(viewport_frame, text="Width:").pack(side=tk.LEFT)
        ttk.Spinbox(viewport_frame, from_=640, to=3840, textvariable=self.default_viewport_width, width=6).pack(side=tk.LEFT, padx=5)
        ttk.Label(viewport_frame, text="Height:").pack(side=tk.LEFT, padx=10)
        ttk.Spinbox(viewport_frame, from_=480, to=2160, textvariable=self.default_viewport_height, width=6).pack(side=tk.LEFT, padx=5)

        # HTTPS errors
        ttk.Label(basic_frame, text="HTTPS Settings:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.default_ignore_https = tk.BooleanVar(value=True)
        ttk.Checkbutton(basic_frame, text="Ignore HTTPS errors by default", 
                       variable=self.default_ignore_https).grid(row=2, column=1, sticky=tk.W, padx=5)

        # Advanced Options toggle
        self.advanced_options_var = tk.BooleanVar(value=False)
        ttk.Separator(self.settings_tab, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        advanced_header = ttk.Frame(self.settings_tab)
        advanced_header.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Checkbutton(advanced_header, text="Show Advanced Options", 
                       variable=self.advanced_options_var, 
                       command=self._toggle_advanced_options).pack(side=tk.LEFT)

        # Advanced Options section (hidden by default)
        self.advanced_frame = ttk.LabelFrame(self.settings_tab, text="Advanced Settings", padding="10")
        self.advanced_frame.pack(fill=tk.X, pady=10, padx=10)
        self.advanced_frame.pack_forget()  # Hide by default

        # Timeout settings
        ttk.Label(self.advanced_frame, text="Timeouts (milliseconds):", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=5)
        
        timeout_frame = ttk.Frame(self.advanced_frame)
        timeout_frame.pack(fill=tk.X, padx=20, pady=5)
        
        self.default_bootstrap_timeout = tk.IntVar(value=30000)
        ttk.Label(timeout_frame, text="Bootstrap page timeout:").pack(side=tk.LEFT)
        ttk.Spinbox(timeout_frame, from_=1000, to=300000, textvariable=self.default_bootstrap_timeout, width=10).pack(side=tk.LEFT, padx=5)

        self.default_capture_timeout = tk.IntVar(value=30000)
        ttk.Label(timeout_frame, text="Capture timeout:").pack(side=tk.LEFT, padx=20)
        ttk.Spinbox(timeout_frame, from_=1000, to=300000, textvariable=self.default_capture_timeout, width=10).pack(side=tk.LEFT, padx=5)

        # Capture settings
        capture_frame = ttk.Frame(self.advanced_frame)
        capture_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.default_record_video = tk.BooleanVar(value=False)
        ttk.Checkbutton(capture_frame, text="Record video by default", 
                       variable=self.default_record_video).pack(anchor=tk.W)

        # Analysis settings
        analysis_label = ttk.Label(self.advanced_frame, text="Analysis Settings:", font=("TkDefaultFont", 10, "bold"))
        analysis_label.pack(anchor=tk.W, padx=20, pady=10)
        
        self.default_max_dom = tk.IntVar(value=10000)
        analysis_frame = ttk.Frame(self.advanced_frame)
        analysis_frame.pack(fill=tk.X, padx=20, pady=5)
        
        ttk.Label(analysis_frame, text="Max DOM nodes:").pack(side=tk.LEFT)
        ttk.Spinbox(analysis_frame, from_=100, to=100000, textvariable=self.default_max_dom, width=10).pack(side=tk.LEFT, padx=5)

        self.default_combine_run = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.advanced_frame, text="Combine all runs in analysis", 
                       variable=self.default_combine_run).pack(anchor=tk.W, padx=20)

    def _toggle_advanced_options(self) -> None:
        """Toggle advanced options visibility."""
        if self.advanced_options_var.get():
            self.advanced_frame.pack(fill=tk.X, pady=10, padx=10)
        else:
            self.advanced_frame.pack_forget()

    def _update_api_status(self) -> None:
        """Update API key status indicators."""
        openai = self.openai_key_var.get().strip()
        xai = self.xai_key_var.get().strip()
        
        if openai:
            self.openai_status_label.config(text="✓ Configured", foreground="green")
        else:
            self.openai_status_label.config(text="✗ Not set", foreground="red")
        
        if xai:
            self.xai_status_label.config(text="✓ Configured", foreground="green")
        else:
            self.xai_status_label.config(text="✗ Not set", foreground="red")

    def _save_api_keys(self) -> None:
        """Save API keys to persistent storage."""
        openai = self.openai_key_var.get().strip()
        xai = self.xai_key_var.get().strip()
        
        # Save to user's home directory
        env_file = Path.home() / ".whistleblower_env"
        
        try:
            with open(env_file, "w") as f:
                f.write("# Whistleblower API Keys\n")
                f.write("# These keys are used for AI-powered analysis\n\n")
                if openai:
                    f.write(f"OPENAI_API_KEY={openai}\n")
                if xai:
                    f.write(f"XAI_API_KEY={xai}\n")
            
            # Set in current environment
            if openai:
                os.environ["OPENAI_API_KEY"] = openai
            if xai:
                os.environ["XAI_API_KEY"] = xai
            
            self._update_api_status()
            self._log("✓ API keys saved successfully")
            messagebox.showinfo("Success", f"API keys saved to:\n{env_file}\n\nKeys are now active for this session.")
        except Exception as e:
            self._log(f"ERROR saving API keys: {e}")
            messagebox.showerror("Error", f"Failed to save API keys: {e}")

    def _create_site_management_tab(self) -> None:
        """Create Site Management tab for site creation and management."""
        # Site selection / management
        site_frame = ttk.LabelFrame(self.site_management_tab, text="Site Management", padding="10")
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
            self.site_management_tab, text="Current Site Configuration", padding="10"
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
        self.capture_site_dropdown = ttk.Combobox(
            self.capture_tab,
            textvariable=self.capture_site_var,
            values=list_sites(),
            width=40,
            state="readonly",
        )
        self.capture_site_dropdown.grid(row=0, column=1, sticky="ew", pady=5, padx=5)
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
        self.analysis_site_dropdown = ttk.Combobox(
            self.analysis_tab,
            textvariable=self.analysis_site_var,
            values=list_sites(),
            width=40,
            state="readonly",
        )
        self.analysis_site_dropdown.grid(row=0, column=1, sticky="ew", pady=5, padx=5)
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

    def _refresh_site_dropdowns(self) -> None:
        """Refresh all site dropdown lists."""
        sites = list_sites()
        self.site_dropdown["values"] = sites
        self.capture_site_dropdown["values"] = sites
        self.analysis_site_dropdown["values"] = sites

    def _show_initialize_button(self) -> None:
        """Show Initialize Site button if site is loaded."""
        # Clear old buttons if exist
        for widget in self.site_management_tab.winfo_children():
            if isinstance(widget, ttk.Button) and widget.cget("text") in ["Initialize Site", "Stop Bootstrap"]:
                widget.destroy()
        
        # Add button to initialize site
        button_frame = ttk.Frame(self.site_management_tab)
        button_frame.pack(pady=10)
        
        self.init_btn = ttk.Button(
            button_frame,
            text="Initialize Site",
            command=self._initialize_site,
            width=20,
        )
        self.init_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_bootstrap_btn = ttk.Button(
            button_frame,
            text="Stop Bootstrap",
            command=self._stop_bootstrap,
            width=20,
            state="disabled",
        )
        self.stop_bootstrap_btn.pack(side=tk.LEFT, padx=5)

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
            
            # Refresh all dropdown lists
            self._refresh_site_dropdowns()
            
            # Set the new site as selected in all tabs
            self.site_var.set(site_name)
            self.capture_site_var.set(site_name)
            self.analysis_site_var.set(site_name)
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
            
            # Refresh all dropdowns
            self._refresh_site_dropdowns()
            
            self.site_var.set("")
            self.capture_site_var.set("")
            self.analysis_site_var.set("")
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
        
        self.bootstrap_running = True
        self.init_btn.config(state="disabled")
        self.stop_bootstrap_btn.config(state="normal")
        
        self._log(f"=== Initializing Site: {self.current_site} ===")
        
        self.bootstrap_thread = threading.Thread(
            target=self._run_bootstrap_thread,
            args=(self.current_site, self.current_config),
            daemon=True,
        )
        self.bootstrap_thread.start()

    def _stop_bootstrap(self) -> None:
        """Signal bootstrap to finalize and save JSON."""
        if not self.bootstrap_running:
            return
        
        # Signal bootstrap to finalize by creating the flag file
        if hasattr(self, 'bootstrap_flag_file') and self.bootstrap_flag_file:
            Path(self.bootstrap_flag_file).touch()
            self._log("Finalizing bootstrap... Please wait while JSON is compiled.")
        
        self.stop_bootstrap_btn.config(state="disabled")

    def _run_bootstrap_thread(self, site_name: str, config: dict[str, Any]) -> None:
        """Run bootstrap in background thread."""
        import tempfile
        import uuid
        
        try:
            # Create temp file PATH (but don't create the file yet)
            temp_dir = Path(tempfile.gettempdir())
            flag_filename = f"whistleblower_bootstrap_{uuid.uuid4().hex}.flag"
            self.bootstrap_flag_file = str(temp_dir / flag_filename)
            
            self._log(f"Initializing {site_name} with URL: {config['bootstrap_url']}")
            self._log("Browser window is opening... Please login and browse the site.")
            self._log("Click 'Stop Bootstrap' when you're finished exploring.")
            
            # Prepare output paths for bootstrap artifacts
            bootstrap_dir = Path(config["directories"]["bootstrap_artifacts"])
            bootstrap_dir.mkdir(parents=True, exist_ok=True)
            config_out = str(bootstrap_dir / f"{site_name}.bootstrap.json")
            steps_out = str(bootstrap_dir / f"{site_name}.steps.json")
            
            result = bootstrap_recorder.run_bootstrap(
                url=config["bootstrap_url"],
                site_name=site_name,
                output_dir=config["directories"]["bootstrap_artifacts"],
                config_out=config_out,
                steps_out=steps_out,
                viewport_width=config["viewport"]["width"],
                viewport_height=config["viewport"]["height"],
                ignore_https_errors=config["ignore_https_errors"],
                record_video=False,
                browser_type=self.browser_var.get(),
                finish_flag_file=self.bootstrap_flag_file,
            )
            
            # Check if user stopped it
            if not self.bootstrap_running:
                self._log("Bootstrap cancelled")
                return
            
            self._log(f"✓ Site initialized successfully!")
            self._log(f"Configuration saved: {result['config_out']}")
            self._log(f"Steps saved: {result['steps_out']}")
            self.root.after(0, lambda: messagebox.showinfo("Success", f"Site '{site_name}' initialized and configured.\n\nYou can now use Capture to take snapshots of the site."))
        except Exception as exc:
            self._log(f"ERROR: {exc}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Bootstrap failed: {exc}"))
        finally:
            self.bootstrap_running = False
            # Clean up flag file
            if hasattr(self, 'bootstrap_flag_file') and self.bootstrap_flag_file:
                Path(self.bootstrap_flag_file).unlink(missing_ok=True)
            
            self.root.after(0, lambda: (
                self.stop_bootstrap_btn.config(state="disabled"),
                self.init_btn.config(state="normal"),
            ))

    def _start_capture(self) -> None:
        """Start capture (now or schedule)."""
        site_name = self.capture_site_var.get()
        if not site_name:
            messagebox.showerror("Error", "Please select a site")
            return
        
        self._log(f"DEBUG: Loading config for site: '{site_name}'")
        config = load_site_config(site_name)
        if not config:
            self._log(f"ERROR: Could not find config for '{site_name}'")
            self._log(f"Available sites: {list_sites()}")
            messagebox.showerror("Error", f"Could not load config for '{site_name}'\n\nPlease check the Setup tab and create the site configuration first.")
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
