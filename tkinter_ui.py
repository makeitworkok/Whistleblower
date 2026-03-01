#!/usr/bin/env python3
# Copyright (c) 2025-2026 Chris Favre - MIT License
# See LICENSE file for full terms
"""Tkinter desktop UI for Whistleblower (bootstrap + capture)."""

from __future__ import annotations

import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Any

import bootstrap_recorder
import whistleblower
import analyze_capture
import tree_spider


class WhistleblowerUI:
    """Main Tkinter UI for Whistleblower."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Whistleblower - BAS Capture Tool")
        self.root.geometry("900x700")
        
        # Thread management
        self.bootstrap_thread: threading.Thread | None = None
        self.capture_thread: threading.Thread | None = None
        self.analysis_thread: threading.Thread | None = None
        self.spider_thread: threading.Thread | None = None
        self.spider_stop_event: threading.Event | None = None
        self.log_queue: queue.Queue[str] = queue.Queue()
        
        # Browser type variable
        self.browser_var = tk.StringVar(value="chromium")
        
        # Create main UI
        self._create_widgets()
        
        # Start log processor
        self._process_log_queue()
    
    def _create_widgets(self) -> None:
        """Create all UI widgets."""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Browser selection frame
        browser_frame = ttk.LabelFrame(main_frame, text="Browser Selection", padding="5")
        browser_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        ttk.Label(browser_frame, text="Browser:").grid(row=0, column=0, padx=5, sticky=tk.W)
        browser_dropdown = ttk.Combobox(
            browser_frame,
            textvariable=self.browser_var,
            values=["chromium", "firefox", "webkit"],
            state="readonly",
            width=20,
        )
        browser_dropdown.grid(row=0, column=1, padx=5, sticky=tk.W)
        ttk.Label(
            browser_frame,
            text="(Chromium includes Edge on Windows)",
            font=("TkDefaultFont", 9, "italic"),
        ).grid(row=0, column=2, padx=5, sticky=tk.W)
        
        # Notebook (tabs)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 10))
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Bootstrap tab
        self.bootstrap_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.bootstrap_tab, text="Bootstrap")
        self._create_bootstrap_tab()
        
        # Capture tab
        self.capture_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.capture_tab, text="Capture")
        self._create_capture_tab()
        
        # Schedule tab
        self.schedule_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.schedule_tab, text="Schedule")
        self._create_schedule_tab()
        
        # Analysis tab with scrollbar
        analysis_container = ttk.Frame(self.notebook)
        self.notebook.add(analysis_container, text="Analysis")
        
        # Create canvas and scrollbar for analysis tab
        analysis_canvas = tk.Canvas(analysis_container, bg="white", highlightthickness=0)
        analysis_scrollbar = ttk.Scrollbar(analysis_container, orient="vertical", command=analysis_canvas.yview)
        self.analysis_tab = ttk.Frame(analysis_canvas, padding="10")
        
        self.analysis_tab.bind(
            "<Configure>",
            lambda e: analysis_canvas.configure(scrollregion=analysis_canvas.bbox("all"))
        )
        
        analysis_canvas.create_window((0, 0), window=self.analysis_tab, anchor="nw")
        analysis_canvas.configure(yscrollcommand=analysis_scrollbar.set)
        
        # Pack canvas and scrollbar
        analysis_canvas.pack(side="left", fill="both", expand=True)
        analysis_scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel for scrolling
        def _on_mousewheel(event):
            analysis_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        analysis_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        self._create_analysis_tab()
        
        # Explore tab
        self.explore_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.explore_tab, text="Explore")
        self._create_explore_tab()
        
        # Log output frame
        log_frame = ttk.LabelFrame(main_frame, text="Output Log", padding="5")
        log_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")
        main_frame.rowconfigure(2, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state='disabled')
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Clear log button
        ttk.Button(log_frame, text="Clear Log", command=self._clear_log).grid(
            row=1, column=0, pady=(5, 0), sticky=tk.E
        )
    
    def _create_bootstrap_tab(self) -> None:
        """Create the Bootstrap tab widgets."""
        # URL input
        ttk.Label(self.bootstrap_tab, text="URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.bootstrap_url = tk.StringVar(value="https://")
        ttk.Entry(self.bootstrap_tab, textvariable=self.bootstrap_url, width=50).grid(
            row=0, column=1, sticky="ew", pady=5, padx=5
        )
        self.bootstrap_tab.columnconfigure(1, weight=1)
        
        # Site name input
        ttk.Label(self.bootstrap_tab, text="Site Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.bootstrap_site_name = tk.StringVar(value="my_site")
        ttk.Entry(self.bootstrap_tab, textvariable=self.bootstrap_site_name, width=50).grid(
            row=1, column=1, sticky="ew", pady=5, padx=5
        )
        
        # Output directory
        ttk.Label(self.bootstrap_tab, text="Output Dir:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.bootstrap_output_dir = tk.StringVar(value="data/bootstrap")
        dir_frame = ttk.Frame(self.bootstrap_tab)
        dir_frame.grid(row=2, column=1, sticky="ew", pady=5, padx=5)
        ttk.Entry(dir_frame, textvariable=self.bootstrap_output_dir, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(dir_frame, text="Browse...", command=self._browse_bootstrap_dir).pack(side=tk.LEFT, padx=(5, 0))
        
        # Viewport settings
        viewport_frame = ttk.LabelFrame(self.bootstrap_tab, text="Viewport Settings", padding="5")
        viewport_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)
        
        ttk.Label(viewport_frame, text="Width:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.bootstrap_width = tk.IntVar(value=1920)
        ttk.Spinbox(viewport_frame, from_=800, to=4000, textvariable=self.bootstrap_width, width=10).grid(
            row=0, column=1, padx=5
        )
        
        ttk.Label(viewport_frame, text="Height:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.bootstrap_height = tk.IntVar(value=1080)
        ttk.Spinbox(viewport_frame, from_=600, to=4000, textvariable=self.bootstrap_height, width=10).grid(
            row=0, column=3, padx=5
        )
        
        # Options
        options_frame = ttk.LabelFrame(self.bootstrap_tab, text="Options", padding="5")
        options_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)
        
        self.bootstrap_ignore_https = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Ignore HTTPS errors",
            variable=self.bootstrap_ignore_https
        ).grid(row=0, column=0, sticky=tk.W, padx=5)
        
        self.bootstrap_record_video = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame,
            text="Record video",
            variable=self.bootstrap_record_video
        ).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Start button
        self.bootstrap_btn = ttk.Button(
            self.bootstrap_tab,
            text="Start Bootstrap Recording",
            command=self._start_bootstrap
        )
        self.bootstrap_btn.grid(row=5, column=0, columnspan=2, pady=20)
    
    def _create_capture_tab(self) -> None:
        """Create the Capture tab widgets."""
        # Config file selection
        ttk.Label(self.capture_tab, text="Config File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.capture_config = tk.StringVar(value="")
        config_frame = ttk.Frame(self.capture_tab)
        config_frame.grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        self.capture_tab.columnconfigure(1, weight=1)
        
        ttk.Entry(config_frame, textvariable=self.capture_config, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(config_frame, text="Browse...", command=self._browse_config).pack(side=tk.LEFT, padx=(5, 0))
        
        # Data directory
        ttk.Label(self.capture_tab, text="Data Dir:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.capture_data_dir = tk.StringVar(value="data")
        data_frame = ttk.Frame(self.capture_tab)
        data_frame.grid(row=1, column=1, sticky="ew", pady=5, padx=5)
        ttk.Entry(data_frame, textvariable=self.capture_data_dir, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(data_frame, text="Browse...", command=self._browse_data_dir).pack(side=tk.LEFT, padx=(5, 0))
        
        # Timeout settings
        timeout_frame = ttk.LabelFrame(self.capture_tab, text="Timeout Settings (ms)", padding="5")
        timeout_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        
        ttk.Label(timeout_frame, text="Navigation:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.capture_timeout = tk.IntVar(value=30000)
        ttk.Spinbox(timeout_frame, from_=5000, to=120000, increment=5000, textvariable=self.capture_timeout, width=10).grid(
            row=0, column=1, padx=5
        )
        
        ttk.Label(timeout_frame, text="Settle:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.capture_settle = tk.IntVar(value=5000)
        ttk.Spinbox(timeout_frame, from_=0, to=60000, increment=1000, textvariable=self.capture_settle, width=10).grid(
            row=0, column=3, padx=5
        )
        
        ttk.Label(timeout_frame, text="Post-login:").grid(row=0, column=4, sticky=tk.W, padx=5)
        self.capture_post_login = tk.IntVar(value=10000)
        ttk.Spinbox(timeout_frame, from_=0, to=60000, increment=1000, textvariable=self.capture_post_login, width=10).grid(
            row=0, column=5, padx=5
        )
        
        # Options
        options_frame = ttk.LabelFrame(self.capture_tab, text="Options", padding="5")
        options_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)
        
        self.capture_headed = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame,
            text="Headed mode (show browser)",
            variable=self.capture_headed
        ).grid(row=0, column=0, sticky=tk.W, padx=5)
        
        self.capture_record_video = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame,
            text="Record video",
            variable=self.capture_record_video
        ).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Start button
        self.capture_btn = ttk.Button(
            self.capture_tab,
            text="Start Capture",
            command=self._start_capture
        )
        self.capture_btn.grid(row=4, column=0, columnspan=2, pady=20)
    
    def _browse_bootstrap_dir(self) -> None:
        """Browse for bootstrap output directory."""
        directory = filedialog.askdirectory(initialdir=self.bootstrap_output_dir.get())
        if directory:
            self.bootstrap_output_dir.set(directory)
    
    def _browse_config(self) -> None:
        """Browse for capture config file."""
        filename = filedialog.askopenfilename(
            initialdir="sites",
            title="Select Config File",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
        )
        if filename:
            self.capture_config.set(filename)
    
    def _browse_data_dir(self) -> None:
        """Browse for capture data directory."""
        directory = filedialog.askdirectory(initialdir=self.capture_data_dir.get())
        if directory:
            self.capture_data_dir.set(directory)
    
    def _log(self, message: str) -> None:
        """Add message to log queue."""
        self.log_queue.put(message)
    
    def _process_log_queue(self) -> None:
        """Process log messages from queue."""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.configure(state='normal')
                self.log_text.insert(tk.END, message + "\n")
                self.log_text.see(tk.END)
                self.log_text.configure(state='disabled')
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self._process_log_queue)
    
    def _clear_log(self) -> None:
        """Clear the log output."""
        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state='disabled')
    
    def _start_bootstrap(self) -> None:
        """Start bootstrap recording in a thread."""
        if self.bootstrap_thread is not None and self.bootstrap_thread.is_alive():
            messagebox.showwarning("Warning", "Bootstrap recording is already running")
            return
        
        # Validate inputs
        url = self.bootstrap_url.get().strip()
        site_name = self.bootstrap_site_name.get().strip()
        
        if not url or url == "https://":
            messagebox.showerror("Error", "Please enter a valid URL")
            return
        
        if not site_name:
            messagebox.showerror("Error", "Please enter a site name")
            return
        
        # Disable button
        self.bootstrap_btn.config(state='disabled')
        self._log("=== Starting Bootstrap Recording ===")
        self._log(f"URL: {url}")
        self._log(f"Site Name: {site_name}")
        self._log(f"Browser: {self.browser_var.get()}")
        
        # Start thread
        self.bootstrap_thread = threading.Thread(
            target=self._run_bootstrap_thread,
            args=(
                url,
                site_name,
                self.bootstrap_output_dir.get(),
                self.bootstrap_width.get(),
                self.bootstrap_height.get(),
                self.bootstrap_ignore_https.get(),
                self.bootstrap_record_video.get(),
                self.browser_var.get(),
            ),
            daemon=True,
        )
        self.bootstrap_thread.start()
    
    def _run_bootstrap_thread(
        self,
        url: str,
        site_name: str,
        output_dir: str,
        width: int,
        height: int,
        ignore_https: bool,
        record_video: bool,
        browser_type: str,
    ) -> None:
        """Run bootstrap recording in background thread."""
        try:
            self._log("Browser window will open. Follow the instructions in the browser console.")
            summary = bootstrap_recorder.run_bootstrap(
                url=url,
                site_name=site_name,
                output_dir=output_dir,
                viewport_width=width,
                viewport_height=height,
                ignore_https_errors=ignore_https,
                record_video=record_video,
                browser_type=browser_type,
            )
            self._log(f"Bootstrap complete!")
            self._log(f"Config: {summary['config_out']}")
            self._log(f"Steps: {summary['steps_out']}")
            self._log(f"Artifacts: {summary['artifacts_dir']}")
            self._log(f"Events recorded: {summary['events_recorded']}")
            messagebox.showinfo("Success", "Bootstrap recording completed!")
        except Exception as exc:
            self._log(f"ERROR: {exc}")
            messagebox.showerror("Error", f"Bootstrap failed: {exc}")
        finally:
            # Re-enable button
            self.root.after(0, lambda: self.bootstrap_btn.config(state='normal'))
    
    def _start_capture(self) -> None:
        """Start capture in a thread."""
        if self.capture_thread is not None and self.capture_thread.is_alive():
            messagebox.showwarning("Warning", "Capture is already running")
            return
        
        # Validate inputs
        config_path = self.capture_config.get().strip()
        
        if not config_path:
            messagebox.showerror("Error", "Please select a config file")
            return
        
        if not Path(config_path).exists():
            messagebox.showerror("Error", f"Config file not found: {config_path}")
            return
        
        # Disable button
        self.capture_btn.config(state='disabled')
        self._log("=== Starting Capture ===")
        self._log(f"Config: {config_path}")
        self._log(f"Browser: {self.browser_var.get()}")
        
        # Start thread
        self.capture_thread = threading.Thread(
            target=self._run_capture_thread,
            args=(
                config_path,
                self.capture_data_dir.get(),
                self.capture_timeout.get(),
                self.capture_settle.get(),
                self.capture_post_login.get(),
                self.capture_headed.get(),
                self.capture_record_video.get(),
            ),
            daemon=True,
        )
        self.capture_thread.start()
    
    def _run_capture_thread(
        self,
        config_path: str,
        data_dir: str,
        timeout_ms: int,
        settle_ms: int,
        post_login_wait_ms: int,
        headed: bool,
        record_video: bool,
    ) -> None:
        """Run capture in background thread."""
        try:
            self._log("Starting capture session...")
            result = whistleblower.run_capture(
                config_path=config_path,
                data_dir=data_dir,
                timeout_ms=timeout_ms,
                settle_ms=settle_ms,
                post_login_wait_ms=post_login_wait_ms,
                headed=headed,
                record_video=record_video,
            )
            self._log(f"Capture complete!")
            self._log(f"Output: {result['run_dir']}")
            self._log(f"Site: {result['site_name']}")
            self._log(f"Targets captured: {result['targets_captured']}")
            messagebox.showinfo("Success", "Capture completed!")
        except Exception as exc:
            self._log(f"ERROR: {exc}")
            messagebox.showerror("Error", f"Capture failed: {exc}")
        finally:
            # Re-enable button
            self.root.after(0, lambda: self.capture_btn.config(state='normal'))
    
    def _create_schedule_tab(self) -> None:
        """Create the Schedule tab for recurring captures."""
        # Config file selection
        ttk.Label(self.schedule_tab, text="Config File:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.schedule_config = tk.StringVar(value="")
        config_frame = ttk.Frame(self.schedule_tab)
        config_frame.grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        self.schedule_tab.columnconfigure(1, weight=1)
        
        ttk.Entry(config_frame, textvariable=self.schedule_config, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(config_frame, text="Browse...", command=self._browse_schedule_config).pack(side=tk.LEFT, padx=(5, 0))
        
        # Data directory
        ttk.Label(self.schedule_tab, text="Data Dir:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.schedule_data_dir = tk.StringVar(value="data")
        data_frame = ttk.Frame(self.schedule_tab)
        data_frame.grid(row=1, column=1, sticky="ew", pady=5, padx=5)
        ttk.Entry(data_frame, textvariable=self.schedule_data_dir, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(data_frame, text="Browse...", command=self._browse_schedule_data_dir).pack(side=tk.LEFT, padx=(5, 0))
        
        # Schedule settings
        schedule_frame = ttk.LabelFrame(self.schedule_tab, text="Schedule", padding="5")
        schedule_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        
        ttk.Label(schedule_frame, text="Interval (minutes):").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.schedule_interval = tk.IntVar(value=60)
        ttk.Spinbox(schedule_frame, from_=1, to=1440, increment=5, textvariable=self.schedule_interval, width=10).grid(
            row=0, column=1, padx=5
        )
        
        # Timeout settings (same as capture)
        timeout_frame = ttk.LabelFrame(self.schedule_tab, text="Timeout Settings (ms)", padding="5")
        timeout_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)
        
        ttk.Label(timeout_frame, text="Navigation:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.schedule_timeout = tk.IntVar(value=30000)
        ttk.Spinbox(timeout_frame, from_=5000, to=120000, increment=5000, textvariable=self.schedule_timeout, width=10).grid(
            row=0, column=1, padx=5
        )
        
        ttk.Label(timeout_frame, text="Settle:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.schedule_settle = tk.IntVar(value=5000)
        ttk.Spinbox(timeout_frame, from_=0, to=60000, increment=1000, textvariable=self.schedule_settle, width=10).grid(
            row=0, column=3, padx=5
        )
        
        # Start/Stop buttons frame
        button_frame = ttk.Frame(self.schedule_tab)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        self.schedule_start_btn = ttk.Button(
            button_frame,
            text="Start Schedule",
            command=self._start_schedule
        )
        self.schedule_start_btn.pack(side=tk.LEFT, padx=5)
        
        self.schedule_stop_btn = ttk.Button(
            button_frame,
            text="Stop Schedule",
            command=self._stop_schedule,
            state='disabled'
        )
        self.schedule_stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Status
        self.schedule_status = tk.StringVar(value="Not running")
        ttk.Label(self.schedule_tab, text="Status:").grid(row=5, column=0, sticky=tk.W, pady=5, padx=5)
        ttk.Label(self.schedule_tab, textvariable=self.schedule_status).grid(row=5, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Schedule control
        self.schedule_thread: threading.Thread | None = None
        self.schedule_running = False
    
    def _browse_schedule_config(self) -> None:
        """Browse for schedule config file."""
        filename = filedialog.askopenfilename(
            initialdir="sites",
            title="Select Config File",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
        )
        if filename:
            self.schedule_config.set(filename)
    
    def _browse_schedule_data_dir(self) -> None:
        """Browse for schedule data directory."""
        directory = filedialog.askdirectory(initialdir=self.schedule_data_dir.get())
        if directory:
            self.schedule_data_dir.set(directory)
    
    def _start_schedule(self) -> None:
        """Start scheduled captures."""
        if self.schedule_running:
            messagebox.showwarning("Warning", "Schedule is already running")
            return
        
        config_path = self.schedule_config.get().strip()
        if not config_path:
            messagebox.showerror("Error", "Please select a config file")
            return
        
        if not Path(config_path).exists():
            messagebox.showerror("Error", f"Config file not found: {config_path}")
            return
        
        self.schedule_running = True
        self.schedule_start_btn.config(state='disabled')
        self.schedule_stop_btn.config(state='normal')
        self.schedule_status.set("Running - Next capture in progress")
        
        self._log("=== Starting Scheduled Captures ===")
        self._log(f"Config: {config_path}")
        self._log(f"Interval: {self.schedule_interval.get()} minutes")
        
        self.schedule_thread = threading.Thread(
            target=self._run_schedule_thread,
            args=(
                config_path,
                self.schedule_data_dir.get(),
                self.schedule_interval.get(),
                self.schedule_timeout.get(),
                self.schedule_settle.get(),
            ),
            daemon=True,
        )
        self.schedule_thread.start()
    
    def _stop_schedule(self) -> None:
        """Stop scheduled captures."""
        self.schedule_running = False
        self.schedule_start_btn.config(state='normal')
        self.schedule_stop_btn.config(state='disabled')
        self.schedule_status.set("Stopped")
        self._log("Scheduler stopped by user")
    
    def _run_schedule_thread(
        self,
        config_path: str,
        data_dir: str,
        interval_minutes: int,
        timeout_ms: int,
        settle_ms: int,
    ) -> None:
        """Run scheduled captures in background thread."""
        import time
        
        capture_count = 0
        try:
            while self.schedule_running:
                capture_count += 1
                self._log(f"\n[Capture #{capture_count}] Starting at {datetime.now().strftime('%H:%M:%S')}")
                
                try:
                    result = whistleblower.run_capture(
                        config_path=config_path,
                        data_dir=data_dir,
                        timeout_ms=timeout_ms,
                        settle_ms=settle_ms,
                    )
                    self._log(f"✓ Capture #{capture_count} completed: {result['run_dir']}")
                except Exception as exc:
                    self._log(f"✗ Capture #{capture_count} failed: {exc}")
                
                # Update status
                next_in = interval_minutes * 60
                self.root.after(0, lambda ni=next_in: self.schedule_status.set(f"Next capture in {ni}s"))
                
                # Sleep in 1-second intervals to allow quick stopping
                sleep_remaining = interval_minutes * 60
                while sleep_remaining > 0 and self.schedule_running:
                    time.sleep(1)
                    sleep_remaining -= 1
                    if sleep_remaining % 10 == 0 and sleep_remaining > 0:
                        self.root.after(0, lambda sr=sleep_remaining: self.schedule_status.set(f"Next capture in {sr}s"))
        
        except Exception as exc:
            self._log(f"ERROR in scheduler: {exc}")
        finally:
            self.schedule_running = False
            self.root.after(0, lambda: self.schedule_start_btn.config(state='normal'))
            self.root.after(0, lambda: self.schedule_stop_btn.config(state='disabled'))
            self.root.after(0, lambda: self.schedule_status.set("Stopped"))
    
    def _create_analysis_tab(self) -> None:
        """Create the Analysis tab widgets."""
        # Run directory selection
        ttk.Label(self.analysis_tab, text="Run Dir:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.analysis_run_dir = tk.StringVar(value="")
        run_frame = ttk.Frame(self.analysis_tab)
        run_frame.grid(row=0, column=1, sticky="ew", pady=5, padx=5)
        self.analysis_tab.columnconfigure(1, weight=1)
        
        ttk.Entry(run_frame, textvariable=self.analysis_run_dir, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(run_frame, text="Browse...", command=self._browse_analysis_run_dir).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(self.analysis_tab, text="Site:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.analysis_site = tk.StringVar(value="")
        ttk.Entry(self.analysis_tab, textvariable=self.analysis_site, width=40).grid(row=1, column=1, sticky="ew", pady=5, padx=5)
        
        # Data directory
        ttk.Label(self.analysis_tab, text="Data Dir:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.analysis_data_dir = tk.StringVar(value="data")
        data_frame = ttk.Frame(self.analysis_tab)
        data_frame.grid(row=2, column=1, sticky="ew", pady=5, padx=5)
        ttk.Entry(data_frame, textvariable=self.analysis_data_dir, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(data_frame, text="Browse...", command=self._browse_analysis_data_dir).pack(side=tk.LEFT, padx=(5, 0))
        
        # Provider selection
        provider_frame = ttk.LabelFrame(self.analysis_tab, text="LLM Provider", padding="5")
        provider_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)
        
        self.analysis_provider = tk.StringVar(value="openai")
        ttk.Radiobutton(
            provider_frame,
            text="OpenAI (GPT-4)",
            variable=self.analysis_provider,
            value="openai"
        ).grid(row=0, column=0, sticky=tk.W, padx=5)
        
        ttk.Radiobutton(
            provider_frame,
            text="xAI (Grok)",
            variable=self.analysis_provider,
            value="xai"
        ).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # API Keys
        api_frame = ttk.LabelFrame(self.analysis_tab, text="API Keys", padding="5")
        api_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)
        
        ttk.Label(api_frame, text="OpenAI Key:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.analysis_openai_key = tk.StringVar(value="")
        ttk.Entry(api_frame, textvariable=self.analysis_openai_key, width=40, show="*").grid(row=0, column=1, padx=5, sticky="ew")
        api_frame.columnconfigure(1, weight=1)
        
        ttk.Label(api_frame, text="xAI Key:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.analysis_xai_key = tk.StringVar(value="")
        ttk.Entry(api_frame, textvariable=self.analysis_xai_key, width=40, show="*").grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(
            api_frame,
            text="(Or set OPENAI_API_KEY / XAI_API_KEY environment variables)",
            font=("TkDefaultFont", 9, "italic"),
        ).grid(row=2, column=0, columnspan=2, pady=5)
        
        # Options
        options_frame = ttk.LabelFrame(self.analysis_tab, text="Options", padding="5")
        options_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)
        
        ttk.Label(options_frame, text="Max DOM chars:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.analysis_max_dom = tk.IntVar(value=12000)
        ttk.Spinbox(options_frame, from_=1000, to=50000, increment=1000, textvariable=self.analysis_max_dom, width=10).grid(
            row=0, column=1, padx=5
        )
        
        self.analysis_combine = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Combine run (single analysis)",
            variable=self.analysis_combine
        ).grid(row=0, column=2, sticky=tk.W, padx=5)
        
        # Date range filter
        date_frame = ttk.LabelFrame(self.analysis_tab, text="Date Range Filter (Optional)", padding="5")
        date_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=10)
        date_frame.columnconfigure(1, weight=1)
        date_frame.columnconfigure(3, weight=1)
        
        ttk.Label(date_frame, text="Start Date (YYYY-MM-DD HH:MM):").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.analysis_start_utc = tk.StringVar(value="")
        ttk.Entry(date_frame, textvariable=self.analysis_start_utc, width=30).grid(row=0, column=1, padx=5, sticky="ew")
        
        ttk.Label(date_frame, text="End Date (YYYY-MM-DD HH:MM):").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.analysis_end_utc = tk.StringVar(value="")
        ttk.Entry(date_frame, textvariable=self.analysis_end_utc, width=30).grid(row=0, column=3, padx=5, sticky="ew")
        
        ttk.Label(date_frame, text="(Leave blank for all runs)", font=("TkDefaultFont", 9, "italic")).grid(
            row=1, column=0, columnspan=4, pady=5
        )
        
        # Start button
        self.analysis_btn = ttk.Button(
            self.analysis_tab,
            text="Start Analysis",
            command=self._start_analysis
        )
        self.analysis_btn.grid(row=7, column=0, columnspan=2, pady=20)
    
    def _browse_analysis_run_dir(self) -> None:
        """Browse for analysis run directory."""
        directory = filedialog.askdirectory(initialdir=self.analysis_data_dir.get())
        if directory:
            self.analysis_run_dir.set(directory)
    
    def _browse_analysis_data_dir(self) -> None:
        """Browse for analysis data directory."""
        directory = filedialog.askdirectory(initialdir=self.analysis_data_dir.get())
        if directory:
            self.analysis_data_dir.set(directory)
    
    def _start_analysis(self) -> None:
        """Start analysis in a thread."""
        if self.analysis_thread is not None and self.analysis_thread.is_alive():
            messagebox.showwarning("Warning", "Analysis is already running")
            return
        
        # Get provider and API key
        provider = self.analysis_provider.get()
        openai_key = self.analysis_openai_key.get().strip()
        xai_key = self.analysis_xai_key.get().strip()
        
        # Determine API key based on provider
        import os
        if provider == "openai":
            api_key = openai_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                messagebox.showerror("Error", "OpenAI API key required. Enter key or set OPENAI_API_KEY environment variable.")
                return
        else:  # xai
            api_key = xai_key or os.getenv("XAI_API_KEY")
            if not api_key:
                messagebox.showerror("Error", "xAI API key required. Enter key or set XAI_API_KEY environment variable.")
                return
        
        # Disable button
        self.analysis_btn.config(state='disabled')
        self._log("=== Starting Analysis ===")
        self._log(f"Provider: {provider}")
        
        # Start thread
        self.analysis_thread = threading.Thread(
            target=self._run_analysis_thread,
            args=(
                self.analysis_run_dir.get() or None,
                self.analysis_data_dir.get(),
                self.analysis_site.get() or None,
                self.analysis_start_utc.get().strip() or None,
                self.analysis_end_utc.get().strip() or None,
                provider,
                api_key,
                self.analysis_max_dom.get(),
                self.analysis_combine.get(),
            ),
            daemon=True,
        )
        self.analysis_thread.start()
    
    def _run_analysis_thread(
        self,
        run_dir: str | None,
        data_dir: str,
        site: str | None,
        start_utc: str | None,
        end_utc: str | None,
        provider: str,
        api_key: str,
        max_dom_chars: int,
        combine_run: bool,
    ) -> None:
        """Run analysis in background thread."""
        try:
            self._log("Running LLM analysis on capture artifacts...")
            result = analyze_capture.run_analysis(
                run_dir=run_dir,
                data_dir=data_dir,
                site=site,
                start_utc=start_utc,
                end_utc=end_utc,
                provider=provider,
                api_key=api_key,
                max_dom_chars=max_dom_chars,
                combine_run=combine_run,
            )
            self._log(f"Analysis complete!")
            self._log(f"Runs analyzed: {result['runs_analyzed']}")
            self._log(result['message'])
            for summary in result.get('run_summaries', []):
                self._log(f"  - {summary['run_dir']}")
            messagebox.showinfo("Success", "Analysis completed!")
        except Exception as exc:
            self._log(f"ERROR: {exc}")
            messagebox.showerror("Error", f"Analysis failed: {exc}")
        finally:
            # Re-enable button
            self.root.after(0, lambda: self.analysis_btn.config(state='normal'))
    
    def _show_about(self) -> None:
        """Show about dialog."""
        messagebox.showinfo(
            "About Whistleblower",
            "Whistleblower - BAS Capture Tool\n\n"
            "Copyright (c) 2025-2026 Chris Favre\n"
            "MIT License\n\n"
            "Desktop UI for automated building automation system\n"
            "screenshot and data capture."
        )

    def _create_explore_tab(self) -> None:
        """Create the Explore tab for read-only auto-exploration of BAS web UIs."""
        tab = self.explore_tab
        tab.columnconfigure(1, weight=1)

        # URL input
        ttk.Label(tab, text="URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.spider_url = tk.StringVar(value="https://")
        ttk.Entry(tab, textvariable=self.spider_url, width=50).grid(
            row=0, column=1, columnspan=2, sticky="ew", pady=5, padx=5
        )

        # Site name
        ttk.Label(tab, text="Site Name:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.spider_site_name = tk.StringVar(value="spider_run")
        ttk.Entry(tab, textvariable=self.spider_site_name, width=50).grid(
            row=1, column=1, columnspan=2, sticky="ew", pady=5, padx=5
        )

        # Output directory
        ttk.Label(tab, text="Output Dir:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.spider_output_dir = tk.StringVar(value="data/spider")
        dir_frame = ttk.Frame(tab)
        dir_frame.grid(row=2, column=1, columnspan=2, sticky="ew", pady=5, padx=5)
        ttk.Entry(dir_frame, textvariable=self.spider_output_dir, width=40).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        ttk.Button(
            dir_frame, text="Browse...", command=self._browse_spider_output_dir
        ).pack(side=tk.LEFT, padx=(5, 0))

        # Config file (optional, for login)
        ttk.Label(tab, text="Config File:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.spider_config = tk.StringVar(value="")
        cfg_frame = ttk.Frame(tab)
        cfg_frame.grid(row=3, column=1, columnspan=2, sticky="ew", pady=5, padx=5)
        ttk.Entry(cfg_frame, textvariable=self.spider_config, width=40).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )
        ttk.Button(
            cfg_frame, text="Browse...", command=self._browse_spider_config
        ).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(
            cfg_frame,
            text="(optional – needed for sites with login)",
            font=("TkDefaultFont", 9, "italic"),
        ).pack(side=tk.LEFT, padx=(5, 0))

        # Traversal settings
        traversal_frame = ttk.LabelFrame(tab, text="Traversal Settings", padding="5")
        traversal_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=10)

        ttk.Label(traversal_frame, text="Max Depth:").grid(
            row=0, column=0, sticky=tk.W, padx=5
        )
        self.spider_max_depth = tk.IntVar(value=3)
        ttk.Spinbox(
            traversal_frame,
            from_=1,
            to=10,
            textvariable=self.spider_max_depth,
            width=8,
        ).grid(row=0, column=1, padx=5)

        ttk.Label(traversal_frame, text="Max Pages:").grid(
            row=0, column=2, sticky=tk.W, padx=5
        )
        self.spider_max_pages = tk.IntVar(value=50)
        ttk.Spinbox(
            traversal_frame,
            from_=1,
            to=500,
            increment=10,
            textvariable=self.spider_max_pages,
            width=8,
        ).grid(row=0, column=3, padx=5)

        ttk.Label(traversal_frame, text="Timeout (ms):").grid(
            row=0, column=4, sticky=tk.W, padx=5
        )
        self.spider_timeout = tk.IntVar(value=30000)
        ttk.Spinbox(
            traversal_frame,
            from_=5000,
            to=120000,
            increment=5000,
            textvariable=self.spider_timeout,
            width=10,
        ).grid(row=0, column=5, padx=5)

        # Options
        options_frame = ttk.LabelFrame(tab, text="Options", padding="5")
        options_frame.grid(row=5, column=0, columnspan=3, sticky="ew", pady=10)

        self.spider_ignore_https = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Ignore HTTPS errors",
            variable=self.spider_ignore_https,
        ).grid(row=0, column=0, sticky=tk.W, padx=5)

        self.spider_take_screenshots = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Take screenshots",
            variable=self.spider_take_screenshots,
        ).grid(row=0, column=1, sticky=tk.W, padx=5)

        self.spider_same_domain = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Same domain only (recommended)",
            variable=self.spider_same_domain,
        ).grid(row=0, column=2, sticky=tk.W, padx=5)

        # Buttons
        btn_frame = ttk.Frame(tab)
        btn_frame.grid(row=6, column=0, columnspan=3, pady=20)

        self.spider_start_btn = ttk.Button(
            btn_frame,
            text="Start Exploration",
            command=self._start_spider,
        )
        self.spider_start_btn.pack(side=tk.LEFT, padx=5)

        self.spider_stop_btn = ttk.Button(
            btn_frame,
            text="Stop Exploration",
            command=self._stop_spider,
            state="disabled",
        )
        self.spider_stop_btn.pack(side=tk.LEFT, padx=5)

        # Status
        self.spider_status = tk.StringVar(value="Not running")
        ttk.Label(tab, text="Status:").grid(row=7, column=0, sticky=tk.W, padx=5)
        ttk.Label(tab, textvariable=self.spider_status).grid(
            row=7, column=1, sticky=tk.W, padx=5
        )

    def _browse_spider_output_dir(self) -> None:
        """Browse for spider output directory."""
        directory = filedialog.askdirectory(initialdir=self.spider_output_dir.get())
        if directory:
            self.spider_output_dir.set(directory)

    def _browse_spider_config(self) -> None:
        """Browse for optional site config file used for login."""
        filename = filedialog.askopenfilename(
            initialdir="sites",
            title="Select Config File (optional)",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*")),
        )
        if filename:
            self.spider_config.set(filename)

    def _start_spider(self) -> None:
        """Start the tree spider exploration in a thread."""
        if self.spider_thread is not None and self.spider_thread.is_alive():
            messagebox.showwarning("Warning", "Exploration is already running")
            return

        url = self.spider_url.get().strip()
        site_name = self.spider_site_name.get().strip()

        if not url or url == "https://":
            messagebox.showerror("Error", "Please enter a valid URL")
            return

        if not site_name:
            messagebox.showerror("Error", "Please enter a site name")
            return

        config_path = self.spider_config.get().strip() or None
        if config_path and not Path(config_path).exists():
            messagebox.showerror("Error", f"Config file not found: {config_path}")
            return

        self.spider_start_btn.config(state="disabled")
        self.spider_stop_btn.config(state="normal")
        self.spider_status.set("Running…")
        self._log("=== Starting Exploration ===")
        self._log(f"URL: {url}")
        self._log(f"Site Name: {site_name}")
        self._log(f"Browser: {self.browser_var.get()}")
        self._log(f"Max depth: {self.spider_max_depth.get()}  Max pages: {self.spider_max_pages.get()}")

        self.spider_stop_event = threading.Event()
        self.spider_thread = threading.Thread(
            target=self._run_spider_thread,
            args=(
                url,
                site_name,
                self.spider_output_dir.get(),
                config_path,
                self.spider_max_depth.get(),
                self.spider_max_pages.get(),
                self.spider_timeout.get(),
                self.spider_ignore_https.get(),
                self.spider_take_screenshots.get(),
                self.browser_var.get(),
                self.spider_same_domain.get(),
            ),
            daemon=True,
        )
        self.spider_thread.start()

    def _stop_spider(self) -> None:
        """Signal the running spider to stop."""
        if self.spider_stop_event is not None:
            self.spider_stop_event.set()
        self.spider_status.set("Stopping…")
        self._log("Stopping exploration (will finish current page)…")

    def _run_spider_thread(
        self,
        url: str,
        site_name: str,
        output_dir: str,
        config_path: str | None,
        max_depth: int,
        max_pages: int,
        timeout_ms: int,
        ignore_https: bool,
        take_screenshots: bool,
        browser_type: str,
        same_domain_only: bool,
    ) -> None:
        """Run the spider in a background thread."""
        try:
            result = tree_spider.run_spider(
                url=url,
                output_dir=output_dir,
                site_name=site_name,
                config_path=config_path,
                max_depth=max_depth,
                max_pages=max_pages,
                timeout_ms=timeout_ms,
                ignore_https_errors=ignore_https,
                take_screenshots=take_screenshots,
                browser_type=browser_type,
                same_domain_only=same_domain_only,
                stop_event=self.spider_stop_event,
                log_callback=self._log,
            )
            self._log(f"Exploration complete!")
            self._log(f"Pages visited : {result['total_pages']}")
            self._log(f"OK pages      : {result['ok_pages']}")
            self._log(f"Bad links     : {result['bad_links']}")
            if result["bad_link_details"]:
                self._log("Bad link details:")
                for bl in result["bad_link_details"]:
                    self._log(f"  [{bl['error']}] {bl['url']}")
            self._log(f"Report        : {result['report_path']}")
            messagebox.showinfo("Complete", "Exploration finished!")
        except Exception as exc:
            self._log(f"ERROR: {exc}")
            messagebox.showerror("Error", f"Exploration failed: {exc}")
        finally:
            self.root.after(0, lambda: self.spider_start_btn.config(state="normal"))
            self.root.after(0, lambda: self.spider_stop_btn.config(state="disabled"))
            self.root.after(0, lambda: self.spider_status.set("Not running"))


def main() -> int:
    """Main entry point for Tkinter UI."""
    root = tk.Tk()
    app = WhistleblowerUI(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
