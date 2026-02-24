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


class WhistleblowerUI:
    """Main Tkinter UI for Whistleblower."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Whistleblower - BAS Capture Tool")
        self.root.geometry("900x700")
        
        # Thread management
        self.bootstrap_thread: threading.Thread | None = None
        self.capture_thread: threading.Thread | None = None
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
        
        self.bootstrap_ignore_https = tk.BooleanVar(value=False)
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


def main() -> int:
    """Main entry point for Tkinter UI."""
    root = tk.Tk()
    app = WhistleblowerUI(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
