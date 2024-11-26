import logging
import os
import sys
import json
import time
import threading
import subprocess
import uuid
import re
import traceback
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from tkinter import messagebox
import tkinter as tk
from PIL import Image

import boto3
import customtkinter as ctk
import importlib.metadata
import requests
from requests_aws4auth import AWS4Auth
import cv2
import numpy as np
import pyautogui
from plyer import notification
import pystray
import ctypes
import socket
from vpn_settings import is_vpn_connected, connect_to_vpn_with_fallback, connect_to_vpn
from notification_popover import NotificationPopover
from constants import LINKS, KNOWN_SECURITY_KEYS
import hid
import keyboard
import ipaddress
import importlib
from config_manager import ConfigManager
from gui_helpers import create_button_frame, create_security_keys_list, update_security_keys_list, get_connected_keys, toggle_pin_visibility
import manage_zukey

import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

def setup_logging():
    """Setup logging configuration."""
    try:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Set up file handler for detailed logging
        log_file = os.path.join('logs', 'quicklinks.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Set up console handler with more detailed output
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)  # Changed from ERROR to INFO to show more details
        
        # Create formatters and add it to the handlers
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')  # Added timestamp to console output
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        
        # Get the root logger and configure it
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        
        # Remove any existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Add our configured handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # Log initial setup message
        logger.info("Logging system initialized")
        
    except Exception as e:
        print(f"Error setting up logging: {e}")
        traceback.print_exc()  # Print full traceback for setup errors

# Define the URLs
LINKS = {
    "GENERAL FEATURES": "http://toolkit.corp.amazon.com/",
    "MIDWAY ACCESS": "https://midway-auth.amazon.com/login#midway",
    "TICKETS LINK": "https://sn.opstechit.amazon.dev/now/sow/list/params/list-id/5157c5f0d50016d8460775c0d73bf852/tiny-id/f0dPdsysuOM3HFYqPzQNNuQeKbR8w039",
    "REPORTS": "https://your-reports-page.url"
}

# Define the configuration file path
CONFIG_FILE = "gui_config.json"

VPN_CHECK_URL = "iad-f-orca.amazon.com"

def is_vpn_connected():
    """
    Check if VPN is connected by checking Cisco AnyConnect status.
    """
    try:
        # Check Cisco AnyConnect status
        from vpn_settings import get_cisco_anyconnect_status
        is_connected, status = get_cisco_anyconnect_status()
        logging.info(f"Cisco AnyConnect Status: ({is_connected}, {status!r})")
        return is_connected
    except Exception as e:
        logging.error(f"Error checking VPN connection: {e}")
        return False

def show_vpn_warning():
    """
    Shows a custom window indicating that the VPN connection is required.
    """
    vpn_window = ctk.CTk()
    vpn_window.title("VPN Connection Required")
    vpn_window.geometry("400x400")  # Increased height to accommodate new button
    
    # Center the window
    window_width = 400
    window_height = 400  # Increased height
    screen_width = vpn_window.winfo_screenwidth()
    screen_height = vpn_window.winfo_screenheight()
    center_x = int(screen_width/2 - window_width/2)
    center_y = int(screen_height/2 - window_height/2)
    vpn_window.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    
    # Warning icon and message
    warning_frame = ctk.CTkFrame(vpn_window, fg_color="transparent")
    warning_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    warning_icon = ctk.CTkLabel(
        warning_frame,
        text="⚠️",
        font=("Segoe UI Emoji", 48)
    )
    warning_icon.pack(pady=(20, 10))
    
    warning_label = ctk.CTkLabel(
        warning_frame,
        text="VPN Connection Required",
        font=("Arial", 20, "bold")
    )
    warning_label.pack(pady=5)
    
    message_label = ctk.CTkLabel(
        warning_frame,
        text="Please connect to the Amazon VPN\nto access internal resources.",
        font=("Arial", 12),
        justify="center"
    )
    message_label.pack(pady=10)
    
    # Button frame
    button_frame = ctk.CTkFrame(warning_frame, fg_color="transparent")
    button_frame.pack(fill="x", padx=20, pady=20)
    
    def launch_vpn_gui():
        """Launch the VPN GUI and close this window"""
        vpn_window.withdraw()  # Hide the warning window
        try:
            import subprocess
            import os
            
            # Get the path to vpn_gui.py
            current_dir = os.path.dirname(os.path.abspath(__file__))
            vpn_gui_path = os.path.join(current_dir, "vpn_gui.py")
            
            # Launch VPN GUI
            subprocess.Popen([sys.executable, vpn_gui_path], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Start checking for VPN connection
            check_vpn_status()
            
        except Exception as e:
            logging.error(f"Failed to launch VPN GUI: {e}")
            message_label.configure(text=f"Error launching VPN GUI: {str(e)}")
            vpn_window.deiconify()  # Show the warning window again

    def continue_without_vpn():
        """Close the warning window and continue without VPN"""
        vpn_window.destroy()
        root = ctk.CTk()
        root.title("Quick Links Dashboard")
        root.geometry(DEFAULT_WINDOW_SIZE)
        app = QuickLinksApp(root)
        root.mainloop()
    
    def check_vpn_status():
        """Check if VPN is connected and close warning if it is"""
        if is_vpn_connected():
            vpn_window.destroy()  # Close the warning window
            return
        # Check again in 2 seconds
        vpn_window.after(2000, check_vpn_status)
    
    # Connect button
    connect_button = ctk.CTkButton(
        button_frame,
        text="Connect to VPN",
        font=("Arial", 12, "bold"),
        command=launch_vpn_gui,
        fg_color="#2B7DE9",
        hover_color="#1c54a1",
        height=35
    )
    connect_button.pack(pady=10, fill="x")
    
    # Continue without VPN button
    continue_button = ctk.CTkButton(
        button_frame,
        text="Continue Without VPN",
        font=("Arial", 12),
        command=continue_without_vpn,
        fg_color="#808080",  # Gray color to indicate it's not recommended
        hover_color="#666666",
        height=35
    )
    continue_button.pack(pady=5, fill="x")
    
    # Retry button
    retry_button = ctk.CTkButton(
        button_frame,
        text="Retry Connection",
        font=("Arial", 12),
        command=lambda: retry_vpn_check(vpn_window, warning_label),
        fg_color="transparent",
        hover_color=("gray85", "gray25"),
        height=35,
        border_width=1
    )
    retry_button.pack(pady=5, fill="x")
    
    vpn_window.mainloop()

def retry_vpn_check(vpn_window, warning_label):
    """
    Retries the VPN connection check and updates the warning message accordingly.
    """
    if is_vpn_connected():
        messagebox.showinfo("VPN Status", "Successfully connected to Amazon IAD Orca VPN")
        vpn_window.destroy()  # Close the current window
        root = ctk.CTk()
        app = QuickLinksApp(root)  # Create a new instance
        app.root.mainloop()
    else:
        vpn_window.destroy()  # Close the current warning window
        show_vpn_warning()  # Show the VPN connection required window

def save_window_geometry(root):
    """
    Saves the window geometry (size and position) to a JSON file.
    
    Args:
        root (ctk.CTk): The root window instance.
    """
    geometry = root.geometry()  # Get geometry as "WxH+X+Y"
    config = {"geometry": geometry}
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
        logging.info(f"Window geometry saved to {CONFIG_FILE}.")
    except Exception as e:
        logging.exception("Failed to save window geometry.")

def load_window_geometry(root):
    """
    Loads the window geometry (size and position) from a JSON file, if it exists.
    
    Args:
        root (ctk.CTk): The root window instance.
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            geometry = config.get("geometry", None)
            if geometry:
                root.geometry(geometry)
                logging.info(f"Window geometry loaded from {CONFIG_FILE}: {geometry}")
        except Exception as e:
            logging.warning("Failed to load window geometry. Using default size.")
            root.geometry("800x600")  # Default size
    else:
        logging.info("No configuration file found. Using default window size.")
        root.geometry("800x600")  # Default size

def wait_for_element(template, confidence=0.9, timeout=5):
    """
    Waits for an element to appear on the screen using PyAutoGUI.

    Args:
        template (str): Path to the image template for matching.
        confidence (float): Confidence level for the match.
        timeout (int): Maximum time to wait in seconds.

    Returns:
        location: Coordinates of the matched element, or None if not found.
    """
    start = time.time()
    while time.time() - start < timeout:
        location = pyautogui.locateOnScreen(template, confidence=confidence)
        if location:
            return location
        time.sleep(0.1)  # Short interval for faster checks
    return None

class QuickLinksApp:
    _instance = None

    def __init__(self, root):
        if QuickLinksApp._instance is not None:
            raise Exception("This class is a singleton!")
        QuickLinksApp._instance = self
        
        self.root = root
        self.root.title("Quick Links Dashboard")
        
        # Thread management
        self._stop_event = threading.Event()
        self._ui_update_lock = threading.Lock()
        self.active_threads = []
        self._after_ids = set()  # Keep track of after callbacks
        
        # Initialize settings first
        from settings_dialog import SettingsDialog
        self.settings = SettingsDialog(self.root)
        
        # Load window state and settings
        self.load_window_state()
        
        # Apply theme from settings
        theme = self.settings.settings.get("theme", "system")
        ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme("blue")
        
        # Apply opacity
        opacity = self.settings.settings.get("opacity", 1.0)
        self.root.attributes('-alpha', opacity)
        
        # Initialize notifications with settings
        self.notifications = []
        self.unread_notifications = []
        self.notification_visible = False
        self.notification_popover = None
        self.notification_ui = None  # Initialize to None first
        
        # Configure root grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Initialize window state variables first
        self.always_on_top = False
        self.notifications_visible = False
        
        # Create main container frame with modern styling
        self.main_container = ctk.CTkFrame(
            self.root,
            fg_color=("gray95", "gray10"),
            corner_radius=15
        )
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create the top control frame for buttons with glass effect
        self.top_controls = ctk.CTkFrame(
            self.root,
            fg_color=("gray90", "gray15"),
            corner_radius=10,
            height=40
        )
        self.top_controls.place(relx=1.0, rely=0, anchor="ne", x=-30, y=30)
        
        # Add notification toggle button to top controls
        self.notification_button = ctk.CTkButton(
            self.top_controls,
            text="🔔 0",  # Bell emoji with initial count
            width=60,
            command=None,  # Remove command to prevent double triggering
            height=30
        )
        self.notification_button.pack(side="left", padx=5, pady=5)
        
        # Now create the notification UI after all widgets are set up
        self.notification_ui = NotificationPopover(self.root, self)
        
        # Bind single click event
        self.notification_button.bind('<Button-1>', self.handle_notification_click)
        
        # Add always on top toggle button to top controls
        self.always_on_top_button = ctk.CTkButton(
            self.top_controls,
            text="📌",  # Pin emoji for always on top
            width=30,
            height=30,
            command=self.toggle_always_on_top,
            fg_color=("gray80", "gray20"),
            hover_color=("gray70", "gray30")
        )
        self.always_on_top_button.pack(side="left", padx=5, pady=5)
        
        # Add settings button to top controls
        self.settings_button = ctk.CTkButton(
            self.top_controls,
            text="⚙️",  # Gear emoji for settings
            width=30,
            height=30,
            command=self.open_settings,
            fg_color=("gray80", "gray20"),
            hover_color=("gray70", "gray30")
        )
        self.settings_button.pack(side="left", padx=5, pady=5)
        
        # Initialize failure_status_label
        self.failure_status_label = ctk.CTkLabel(
            self.root,
            text="",  # Initially empty
            font=("Helvetica", 14),
            text_color="red",
            anchor="center"
        )
        self.failure_status_label.pack(pady=10, padx=60, fill="x")
        
        # Create GUI elements
        self.create_widgets()
        
        # Load persistent notifications in background
        threading.Thread(target=self._load_persistent_notifications, daemon=True).start()
        
        # Setup system tray icon in background
        threading.Thread(target=self.setup_tray_icon, daemon=True).start()
        
        # Initialize security keys list
        self.security_keys = []
        self.notification_label = self.create_notification_label()
        self.update_keys_lock = threading.Lock()
        
        # Start monitoring security keys
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_security_keys, daemon=True)
        self.monitor_thread.start()
        self.active_threads.append(self.monitor_thread)
        
        # Add custom logging handler to direct logs to the textbox
        self.add_textbox_log_handler()
        
        # Initialize automation lock
        self.automation_lock = threading.Lock()
        
        # Schedule periodic tasks with longer intervals
        self.root.after(5000, self.check_dpi_scaling)  # Check DPI less frequently
        self.root.after(1000, self.update)  # Update UI every second
        
        # Bind window events
        self.root.bind('<Configure>', lambda e: self.root.after(100, lambda: self.on_window_configure(e)))
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _load_persistent_notifications(self):
        """Load persistent notifications in background thread."""
        try:
            config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
            notification_file = os.path.join(config_dir, "notifications.json")
            if os.path.exists(notification_file):
                with open(notification_file, 'r') as f:
                    stored_notifications = json.load(f)
                    with self._ui_update_lock:
                        self.notifications = stored_notifications
                        self.unread_notifications = [n for n in stored_notifications if not n.get("read", False)]
                    # Update UI in main thread
                    self.root.after(0, self.update_notification_button)
        except Exception as e:
            logging.error(f"Failed to load persistent notifications: {e}")

    def update(self):
        """Updates the GUI components or performs scheduled updates."""
        try:
            # Only update if window exists
            if not self.root.winfo_exists():
                return
                
            # Update notification count
            self.update_notification_button()
            
            # Schedule next update
            self.root.after(1000, self.update)
            
        except Exception as e:
            logging.error(f"Error in update loop: {e}")
            # Try to reschedule even if there was an error
            self.root.after(1000, self.update)

    def on_closing(self):
        """Handle window closing."""
        try:
            logging.info("Closing application...")
            
            # Cancel all pending after callbacks
            for after_id in list(self._after_ids):
                try:
                    self.root.after_cancel(after_id)
                except Exception:
                    pass
            self._after_ids.clear()
            
            # Set stop event
            self._stop_event.set()
            
            # Wait for threads
            for thread in self.active_threads:
                if thread.is_alive():
                    thread.join(timeout=1.0)
            
            # Save window state
            self.save_window_state()
            
            # Destroy window and quit
            self.root.quit()
            self.root.destroy()
            
        except Exception as e:
            logging.error(f"Error during application shutdown: {e}")
            try:
                self.root.destroy()
            except:
                pass

    @classmethod
    def get_instance(cls):
        """
        Returns the singleton instance of QuickLinksApp.
        """
        if cls._instance is None:
            logging.error("QuickLinksApp instance not available")
            raise RuntimeError("QuickLinksApp instance not available - the application must be initialized first")
        return cls._instance

    def add_textbox_log_handler(self):
        """
        Adds a custom logging handler to direct log messages to the log_textbox.
        """
        if hasattr(self, 'log_textbox') and self.log_textbox:
            handler = TextBoxHandler(self)  # Pass self instead of log_queue
            handler.setLevel(logging.INFO)
            logging.getLogger().addHandler(handler)
            logging.info("TextBoxHandler added to logger.")
        else:
            logging.warning("log_textbox not initialized. Cannot add TextBoxHandler.")

    def set_window_icon(self):
        """Sets the window icon if the icon file exists, otherwise uses a default."""
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "icon.ico")
        
        try:
            # For Windows, use iconbitmap
            if os.name == 'nt':
                self.root.iconbitmap(icon_path)
            else:
                # For other platforms, use PhotoImage
                icon = PhotoImage(file=icon_path)
                self.root.iconphoto(True, icon)
            logging.info("Window icon set successfully.")
        except Exception as e:
            logging.warning(f"Failed to set window icon: {str(e)}")
    
    def create_widgets(self):
        """
        Creates all the GUI widgets with modern styling.
        """
        # Create main content frame with modern styling
        self.content_frame = ctk.CTkFrame(
            self.main_container,
            fg_color="transparent"
        )
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Create button frame and buttons with modern styling
        self.button_frame = create_button_frame(
            root=self.content_frame,
            links=LINKS,
            open_link_callback=self.open_link,
            handle_midway_access_callback=self.handle_midway_access,
            open_manage_zukey_callback=self.open_manage_zukey,
            open_general_dashboard_callback=self.open_general_dashboard_window,
            open_scanner_apw_callback=self.open_scanner_apw
        )
        self.button_frame.pack(fill="x", padx=20, pady=10)  # Store the reference

        # Create log frame
        self.log_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=("gray85", "gray20"),
            corner_radius=10
        )
        self.log_frame.pack(fill="both", expand=True, padx=20, pady=(10, 20))

        # Create log textbox
        self.log_textbox = ctk.CTkTextbox(
            self.log_frame,
            wrap="word",
            font=("Consolas", 12),
            fg_color=("white", "gray10"),
            text_color=("black", "white"),
            height=150
        )
        self.log_textbox.pack(fill="both", expand=True, padx=10, pady=10)

        # Configure textbox highlighting
        self.configure_textbox_highlighting()

        # Load existing logs
        self.load_logs()

        # Create copy logs button
        self.copy_logs_button = ctk.CTkButton(
            self.log_frame,
            text="Copy Logs",
            command=lambda: self.copy_logs_to_clipboard(self.log_textbox),
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40")
        )
        self.copy_logs_button.pack(pady=(0, 10))

        # Add status label with modern styling
        self.midway_status_label = ctk.CTkLabel(
            self.content_frame,
            text="",
            font=("Segoe UI", 14),
            text_color=("gray20", "gray80"),
            anchor="center"
        )
        self.midway_status_label.pack(pady=10, padx=60, fill="x")
        
        # Create security keys section with modern styling
        self.security_keys_list = create_security_keys_list(
            self.content_frame, 
            self.on_security_key_double_click
        )
        
        # Add Failure Status Label
        self.failure_status_label = ctk.CTkLabel(
            self.root,
            text="",  # Initially empty
            font=("Helvetica", 14),
            text_color="red",
            anchor="center"
        )
        self.failure_status_label.pack(pady=10, padx=60, fill="x")
        
    def refresh_ui(self):
        """Refresh the UI when settings change"""
        if hasattr(self, 'button_frame'):
            self.button_frame.destroy()
            
        # Create new button frame with current settings
        self.button_frame = create_button_frame(
            root=self.content_frame,
            links=LINKS,
            open_link_callback=self.open_link,
            handle_midway_access_callback=self.handle_midway_access,
            open_manage_zukey_callback=self.open_manage_zukey,
            open_general_dashboard_callback=self.open_general_dashboard_window,
            open_scanner_apw_callback=self.open_scanner_apw
        )
        self.button_frame.pack(fill="x", padx=20, pady=10)  # Store the reference

    def load_logs(self):
        """
        Loads the contents of the log file into the log textbox.
        """
        try:
            with open('link_opener.log', 'r') as log_file:
                content = log_file.read()
            self.log_textbox.configure(state="normal")
            self.log_textbox.delete("0.0", "end")
            self.log_textbox.insert("0.0", content)
            self.log_textbox.configure(state="disabled")
        except Exception as e:
            logging.exception("Failed to load log file.")
            self.log_textbox.configure(state="normal")
            self.log_textbox.delete("0.0", "end")
            self.log_textbox.insert("0.0", f"Failed to load log file.\nError: {e}")
            self.log_textbox.configure(state="disabled")

    def toggle_pin_visibility(self):
        self.pin_visible = toggle_pin_visibility(
            pin_entry=self.pin_entry,
            show_pin_button=self.show_pin_button,
            pin_visible=self.pin_visible
        )

    def open_link(self, url, name):
        try:
            logging.info(f"Opening link: {name} ({url})")
            if not self.check_vpn_connection():
                logging.warning("VPN connection not detected")
                show_vpn_warning()
                return
            
            threading.Thread(target=self.open_link_thread, args=(url, name), daemon=True).start()
        except Exception as e:
            logging.error(f"Error opening link {name}: {e}", exc_info=True)

    def open_link_thread(self, url, name):
        try:
            loop = asyncio.new_event_loop()      # Create a new event loop
            asyncio.set_event_loop(loop)         # Set it as the current event loop in this thread
            loop.run_until_complete(self.async_open_link(url, name))
        except Exception as e:
            logging.exception(f"Failed to open URL with Playwright: {name} - {url}")
            self.root.after(0, lambda e=e: self.update_notification(f"Failed to open {name}.\nError: {e}", "red"))  # Added error message

    async def setup_playwright(self, channel="chrome", headless=False, args=None):
        """
        Sets up Playwright with a new browser, context, and page.

        Args:
            channel (str): The browser channel to use.
            headless (bool): Whether to run the browser in headless mode.
            args (list): Additional arguments for browser launch.

        Returns:
            tuple: (page, context, browser, playwright)
        """
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(channel=channel, headless=headless, args=args or [])
            context = await browser.new_context()
            page = await context.new_page()
            return page, context, browser, playwright
        except Exception as e:
            logging.exception("Failed to setup Playwright.")
            raise

    async def navigate_to_page(self, page, url, timeout=60000):
        """
        Navigates the Playwright page to the specified URL.

        Args:
            page (Page): The Playwright Page object.
            url (str): The URL to navigate to.
            timeout (int): The timeout for page navigation in milliseconds.
        """
        try:
            await page.goto(url, timeout=timeout)
            logging.info(f"Successfully navigated to {url}.")
        except PlaywrightTimeoutError:
            logging.error(f"Timeout while navigating to {url}.")
            raise
        except Exception as e:
            logging.exception(f"Failed to navigate to {url}.")
            raise

    async def async_open_link(self, url, name):
        try:
            # Check VPN connection before proceeding
            if "corp.amazon.com" in url and not self.check_vpn_connection():
                logging.error("VPN is not connected. Cannot access internal URLs.")
                self.update_notification(
                    "VPN Connection Error",
                    "Please connect to the corporate VPN before running this script."
                )
                return
            
            page, context, browser, playwright = await self.setup_playwright(args=["--start-maximized"])
            await self.navigate_to_page(page, url)
            logging.info(f"Opened URL with Playwright: {name} - {url}")
            page_title = await page.title()
            logging.info(f"Page Title for {name}: {page_title}")
        finally:
            await close_resources(page, context, browser, playwright)

    def create_notification_label(self):
        """
        Creates a notification label below the PIN field for status updates.
        """
        notification_label = ctk.CTkLabel(
            self.root,
            text="",  # Initially empty
            font=("Helvetica", 12),
            text_color="green",
            anchor="w"
        )
        # Place the label below the PIN field (adjust coordinates as needed)
        notification_label.place(x=150, y=120)  # Adjust `x` and `y` based on GUI layout
        return notification_label

    def monitor_security_keys(self):
        """Monitor for security key changes."""
        logging.info("Starting security key monitoring")
        last_keys = set()
        
        while self.monitoring:
            try:
                with self.update_keys_lock:
                    current_keys = set(get_connected_keys())
                    
                    # Only process changes if the keys have changed
                    if current_keys != last_keys:
                        logging.info(f"Security keys changed. Current keys: {current_keys}")
                        self.security_keys = current_keys
                        self.root.after(0, lambda: self.update_security_keys_list(current_keys))
                        
                        # Added keys
                        added_keys = current_keys - last_keys
                        if added_keys:
                            for key in added_keys:
                                self.add_notification(f"Security key connected: {key}", level="info")
                                self.notify_key_event(key, "connected")
                        
                        # Removed keys
                        removed_keys = last_keys - current_keys
                        if removed_keys:
                            for key in removed_keys:
                                self.add_notification(f"Security key disconnected: {key}", level="warning")
                                self.notify_key_event(key, "disconnected")
                        
                        last_keys = current_keys
                
            except Exception as e:
                logging.error(f"Error in security key monitoring: {e}", exc_info=True)
                time.sleep(5)  # Wait before retrying
            
            time.sleep(1)  # Check every second

    def is_security_key(self, device):
        """
        Determines if a device is a security key.
        """
        # ZUKEY 2 specific identifiers
        ZUKEY_VENDOR_ID = 0x1949
        ZUKEY_PRODUCT_ID = 0x0429

        # Check for ZUKEY 2 first
        if device.get('vendor_id') == ZUKEY_VENDOR_ID and device.get('product_id') == ZUKEY_PRODUCT_ID:
            return True

        # Other known security key vendors
        known_vendors = [0x1050, 0x096e]  # YubiKey and other vendors
        if device.get('vendor_id') in known_vendors:
            return True

        # Check product name for keywords
        key_keywords = ["yubikey", "titan", "authenticator", "zukey"]
        product = (device.get("product_string", "") or "").lower()
        manufacturer = (device.get("manufacturer_string", "") or "").lower()
        
        return any(keyword in product or keyword in manufacturer for keyword in key_keywords)

    def update_security_keys_list(self, keys):
        """
        Updates the security keys list in the GUI.
        """
        self.security_keys_list.configure(state="normal")
        self.security_keys_list.delete("1.0", "end")
        for key in keys:
            self.security_keys_list.insert("end", f"{key}\n")
        self.security_keys_list.configure(state="disabled")

    def notify_key_event(self, key, event_type):
        """
        Shows a system notification for security key events.
        """
        try:
            title = "Security Key Event"
            message = f"Security key {event_type}: {key}"
            
            notification.notify(
                title=title,
                message=message,
                app_name="QuickLinks",
                app_icon=None,  # You can add an icon path here
                timeout=5,
            )
            logging.info(f"Security key notification sent: {message}")
        except Exception as e:
            logging.error(f"Failed to show notification: {e}")

    def on_closing(self):
        """
        Handles the window close event. Stops the monitoring thread and saves the window geometry before closing.
        """
        try:
            # Save final state including position and always-on-top
            state = {
                'geometry': self.root.geometry(),
                'always_on_top': self.always_on_top,
                'settings': self.settings.settings if hasattr(self, 'settings') else {}
            }
            with open(os.path.join(os.path.dirname(__file__), "window_state.json"), 'w') as f:
                json.dump(state, f)
            
            # Stop monitoring thread
            self.monitoring = False
            if hasattr(self, 'monitor_thread'):
                self.monitor_thread.join(timeout=1.0)
            
            # Remove tray icon
            if hasattr(self, 'icon'):
                self.icon.stop()
            
            # Destroy window
            self.root.destroy()
            sys.exit(0)
            
        except Exception as e:
            logging.error(f"Error during application shutdown: {e}")
            self.root.destroy()
            sys.exit(1)
    
    def on_minimize(self):
        """
        Handles the window minimize event.
        """
        self.root.iconify()

    def handle_midway_access(self):
        """
        Handles the MIDWAY ACCESS button click.
        """
        # Start the automation directly
        threading.Thread(target=self.run_midway_automation, daemon=True).start()

    def run_midway_automation(self):
        """
        Runs the MIDWAY ACCESS automation.
        """
        try:
            self.start_loading()
            asyncio.run(self.midway_automation())
        except Exception as e:
            logging.exception("An error occurred during MIDWAY ACCESS automation.")
            error_message = f"Automation failed: {str(e)}"
            self.show_failure_status(error_message)
        finally:
            self.stop_loading()

    async def midway_automation(self):
        """
        Automates accessing MIDWAY ACCESS.
        """
        # Check VPN connection before proceeding
        if not self.check_vpn_connection():
            self.midway_status_label.configure(
                text="Error: Please connect to the corporate VPN.",
                text_color="red"
            )
            logging.error("VPN is not connected. Cannot access MIDWAY ACCESS.")
            return
            
        url = LINKS["MIDWAY ACCESS"]
        try:
            page, context, browser, playwright = await open_page(url)
        
            # Update the success label
            self.midway_status_label.configure(
                text="Successfully opened MIDWAY ACCESS.",
                text_color="green"
            )
            # Schedule the label to be cleared after 5 seconds
            self.root.after(5000, self.clear_failure_status_label)
        except PlaywrightTimeoutError:
            logging.exception("Timeout occurred during MIDWAY ACCESS automation.")
            self.midway_status_label.configure(
                text="Timeout occurred while opening MIDWAY ACCESS.",
                text_color="red"
            )
            # Schedule the label to be cleared after 5 seconds
            self.root.after(5000, self.clear_failure_status_label)
        except Exception as e:
            if "ERR_NAME_NOT_RESOLVED" in str(e):
                self.midway_status_label.configure(
                    text="Error: Unable to resolve the domain. Please check your VPN connection.",
                    text_color="red"
                )
            else:
                self.midway_status_label.configure(
                    text=f"Automation Error: {e}",
                    text_color="red"
                )
            logging.exception("Failed to complete MIDWAY ACCESS automation.")
            self.root.after(5000, self.clear_failure_status_label)

    def start_loading(self):
        """
        Starts the progress bar animation.
        """
        if hasattr(self, "progress_bar"):
            self.progress_bar.start()
        else:
            logging.error("Progress bar not initialized.")
    
    def stop_loading(self):
        """
        Stops the progress bar animation.
        """
        if hasattr(self, "progress_bar"):
            self.progress_bar.stop()
        else:
            logging.error("Progress bar not initialized.")

    def show_message(self, title, message):
        """
        Shows a success message using a messagebox.

        Args:
            title (str): Title of the messagebox.
            message (str): Message to display.
        """
        self.root.after(0, lambda: self.update_notification(title, message))

    def show_error(self, title, message):
        """
        Shows an error message using a messagebox.

        Args:
            title (str): Title of the messagebox.
            message (str): Message to display.
        """
        self.root.after(0, lambda: self.update_notification(title, message))

    def setup_tray_icon(self):
        """
        Sets up the system tray icon using pystray.
        """
        try:
            tray_icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "tray_icon.ico")
            
            try:
                # For Windows, use iconbitmap
                if os.name == 'nt':
                    self.root.iconbitmap(tray_icon_path)
                else:
                    # For other platforms, use PhotoImage
                    icon = PhotoImage(file=tray_icon_path)
                    self.root.iconphoto(True, icon)
                logging.info("Window icon set successfully.")
            except Exception as e:
                logging.warning(f"Failed to set window icon: {str(e)}")
            
            # Create system tray icon
            icon_image = Image.open(tray_icon_path)
            menu = pystray.Menu(
                pystray.MenuItem("Show", self.show_window),
                pystray.MenuItem("Exit", self.exit_application)
            )
            self.tray_icon = pystray.Icon("QuickLinks", icon_image, "QuickLinks", menu)
            
            # Start the tray icon in a separate thread
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            logging.info("System tray icon set up successfully.")
            
        except Exception as e:
            logging.error(f"Failed to set up tray icon: {str(e)}")
    
    def show_window(self):
        """
        Restores the main window from the system tray.
        """
        try:
            # Load saved geometry
            state_file = os.path.join(os.path.dirname(__file__), "window_state.json")
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    
                # Restore window geometry
                self.root.geometry(state.get('geometry', '800x600'))
                
                # Restore always-on-top state
                self.always_on_top = state.get('always_on_top', False)
                self.root.attributes('-topmost', self.always_on_top)
                if hasattr(self, 'always_on_top_button'):
                    self.always_on_top_button.configure(
                        fg_color="gray70" if self.always_on_top else "transparent"
                    )
                    
                # Restore settings if available
                if hasattr(self, 'settings') and 'settings' in state:
                    self.settings.settings.update(state['settings'])
                    self.settings.save_settings()
                    self.settings.apply_theme()
                    
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            
        except Exception as e:
            logging.error(f"Error restoring window: {e}")
            self.root.deiconify()

    def exit_application(self):
        """
        Exits the application gracefully.
        """
        try:
            self.tray_icon.stop()
        except Exception:
            pass
        self.root.quit()

    def open_manage_zukey(self):
        """Open the Manage Zukey window in a separate thread."""
        logging.info("Starting to open Manage Zukey window...")
        try:
            # Validate root window
            if not self.root or not self.root.winfo_exists():
                logging.error("Invalid root window")
                return
            logging.info("Root window check passed")

            # Import the module
            try:
                import manage_zukey
                logging.info("Successfully imported manage_zukey module")
            except ImportError as e:
                logging.error(f"Failed to import manage_zukey module: {e}")
                messagebox.showerror("Error", f"Failed to load security key manager: {e}")
                return

            # Create and start the GUI thread
            def run_zukey_window():
                try:
                    window = manage_zukey.open_manage_window(self.root)
                    if window:
                        logging.info("Manage Zukey window opened successfully")
                        # Wait for window to be destroyed
                        while window.window.winfo_exists():
                            time.sleep(0.1)
                except Exception as e:
                    logging.error(f"Error in Zukey window thread: {e}")

            zukey_thread = threading.Thread(target=run_zukey_window, daemon=True)
            zukey_thread.start()

        except Exception as e:
            logging.error(f"Failed to open Manage Zukey window: {e}")
            messagebox.showerror("Error", f"Failed to open security key manager: {e}")

    def open_general_dashboard_window(self):
        """
        Opens the General Features window.
        """
        try:
            if not self.is_vpn_connected():
                raise Exception("VPN not connected. Please connect to VPN first.")

            from ScannerAPW_BTN import PasscodeApp
            scanner_window = self.create_toplevel_window(PasscodeApp)
            scanner_window.focus_force()

        except Exception as e:
            logging.error(f"Error opening scanner APW: {e}")
            self.show_error("Scanner APW Error", str(e))

    def show_failure_status(self, error_message):
        """
        Updates and displays the failure status label with the provided error message.

        Args:
            error_message (str): The error message to display.
        """
        self.failure_status_label.configure(text=error_message)
        self.failure_status_label.pack(fill="x", padx=60, pady=10)
        # Schedule to clear the label after 5 seconds
        self.root.after(5000, self.clear_failure_status_label)
    
    def clear_failure_status_label(self):
        """
        Clears the failure_status_label text.
        """
        self.failure_status_label.configure(text="")

    def open_windows_hello_setup(self, key_name):
        """
        Opens the Windows Hello Security Key PIN and Reset dialog using template matching.
        
        Args:
            key_name (str): Name of the security key.
        """
        try:
            logging.info(f"Opening Windows Hello setup for security key: {key_name}")

            # Step 1: Open Sign-in Options via ms-settings
            subprocess.run("start ms-settings:signinoptions", shell=True, check=True)
            time.sleep(5)  # Wait for Settings to open

            # Step 2: Automate navigation to Security Key settings using template matching
            templates = [
                ("accounts_button.png", 0.8),
                ("sign_in_options_button.png", 0.8),
                ("security_key_button.png", 0.8),
                ("manage_button.png", 0.8)
            ]

            for template, confidence in templates:
                if not self.locate_and_click(template, confidence, wait_time=2):
                    logging.error(f"Failed to locate and click on {template}.")
                    self.update_notification(f"Error: Could not navigate to {template}.", "red")
                    return

            logging.info("Windows Hello Security Key dialog opened successfully.")
            self.update_notification(f"Windows Hello setup opened for: {key_name}", "green")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to open Sign-in Options: {e}")
            self.update_notification(f"Error: Failed to open Sign-in Options.\n{e}", "red")
        except Exception as e:
            logging.error(f"An error occurred while opening Windows Hello setup: {e}")
            self.update_notification(f"Error: An unexpected error occurred.\n{e}", "red")
    
    def locate_and_click(self, template_path, confidence=0.8, wait_time=1):
        """
        Locates an image on the screen and clicks on it using template matching.
    
        Args:
            template_path (str): Path to the image template for matching.
            confidence (float): Confidence level for template matching.
            wait_time (int): Time to wait after clicking.
    
        Returns:
            bool: True if the image was found and clicked, False otherwise.
        """
        try:
            logging.info(f"Looking for {template_path} on the screen...")
            screenshot = pyautogui.screenshot()
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                logging.error(f"Template image {template_path} not found.")
                return False
            screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            res = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= confidence)
            if len(loc[0]) > 0:
                top_left = (loc[1][0], loc[0][0])
                center_x = top_left[0] + template.shape[1] // 2
                center_y = top_left[1] + template.shape[0] // 2
                pyautogui.click(center_x, center_y)
                logging.info(f"Clicked on {template_path}.")
                time.sleep(wait_time)
                return True
            else:
                logging.warning(f"{template_path} not found on the screen.")
                return False
        except Exception as e:
            logging.error(f"Error locating or clicking {template_path}: {e}")
            return False

    def copy_logs_to_clipboard(self, textbox):
        """
        Copies the content of the specified textbox to the clipboard.
        """
        try:
            textbox.configure(state="normal")
            log_content = textbox.get("1.0", "end").strip()
            textbox.configure(state="disabled")
            self.root.clipboard_clear()
            self.root.clipboard_append(log_content)
            self.root.update()
            self.update_notification("Logs copied to clipboard successfully!", "green")
        except Exception as e:
            logging.error(f"Failed to copy logs: {e}")
            self.update_notification("Failed to copy logs.", "red")

    def configure_textbox_highlighting(self):
        """
        Configures highlighting for specific keywords in the log textbox.
        """
        if hasattr(self, 'log_textbox') and self.log_textbox:
            self.log_textbox.tag_config("highlight", foreground="green")
        else:
            logging.warning("log_textbox not initialized. Cannot configure highlighting.")

    def update_logs_in_main_thread(self, log_entry):
        """
        Appends a log entry to the log textbox directly in the main thread.
        """
        if hasattr(self, 'log_textbox') and self.log_textbox:
            try:
                self.log_textbox.configure(state="normal")
                if "Detected keys" in log_entry:
                    self.log_textbox.insert("end", log_entry + "\n", "highlight")
                else:
                    self.log_textbox.insert("end", log_entry + "\n")
                self.log_textbox.configure(state="disabled")
                self.log_textbox.see("end")  # Auto-scroll to the latest log
            except Exception as e:
                print(f"Error updating logs in main thread: {e}")
        else:
            logging.warning("log_textbox not initialized. Cannot update logs.")

    def check_dpi_scaling(self):
        """
        Checks and handles DPI scaling settings for the application.
        """
        try:
            logging.debug("Checking DPI scaling...")
            self.root.after(1000, self.check_dpi_scaling)
        except Exception as e:
            logging.error(f"Error in DPI scaling check: {e}")

    def open_scanner_apw(self):
        """Opens the Scanner APW (Passcode Finder) window."""
        try:
            logging.info("Opening Scanner APW...")
            
            # Check VPN first
            if not self.check_vpn_connection():
                from vpn_warning_dialog import show_vpn_warning
                if not show_vpn_warning(self.root):
                    logging.info("User cancelled Scanner APW due to no VPN")
                    return
                logging.info("User chose to continue without VPN")
            
            # Launch the PasscodeApp
            import subprocess
            import sys
            import os
            
            # Get the path to ScannerAPW_BTN.py
            scanner_path = os.path.join(os.path.dirname(__file__), "ScannerAPW_BTN.py")
            
            # Launch the script in a new process
            subprocess.Popen([sys.executable, scanner_path], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            
            logging.info("Scanner APW launched successfully")
                
        except Exception as e:
            logging.error(f"Error opening Scanner APW: {e}")
            self.update_notification("Error opening Scanner APW", "error")
    
    def close_scanner_apw(self):
        """Handle Scanner APW window closing"""
        try:
            if hasattr(self, 'scanner_window') and self.scanner_window:
                self.scanner_window.destroy()
                self.scanner_window = None
                logging.info("Scanner APW window closed")
        except Exception as e:
            logging.error(f"Error closing Scanner APW window: {e}")
    
    def load_window_state(self):
        """Load window position, size, and always-on-top state"""
        try:
            state_file = os.path.join(os.path.dirname(__file__), "window_state.json")
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    
                self.root.geometry(state.get('geometry', '800x600'))
                
                self.always_on_top = state.get('always_on_top', False)
                self.root.attributes('-topmost', self.always_on_top)
                if hasattr(self, 'always_on_top_button'):
                    self.always_on_top_button.configure(
                        fg_color="gray70" if self.always_on_top else "transparent"
                    )
                    
                if hasattr(self, 'settings') and 'settings' in state:
                    self.settings.settings.update(state['settings'])
                    self.settings.save_settings()
                    self.settings.apply_theme()
                    
        except Exception as e:
            logging.error(f"Error loading window state: {e}")
            self.root.geometry("800x600")

    def on_window_configure(self, event):
        """Handle window movement/resize events."""
        if event.widget == self.root:
            state = {
                'geometry': self.root.geometry(),
                'always_on_top': self.always_on_top,
                'settings': self.settings.settings if hasattr(self, 'settings') else {}
            }
            with open(os.path.join(os.path.dirname(__file__), "window_state.json"), 'w') as f:
                json.dump(state, f)

    def toggle_always_on_top(self):
        """Toggle window always-on-top state"""
        self.always_on_top = not self.always_on_top
        self.root.attributes('-topmost', self.always_on_top)
        self.always_on_top_button.configure(
            fg_color="gray70" if self.always_on_top else "transparent"
        )
        state = {
            'geometry': self.root.geometry(),
            'always_on_top': self.always_on_top,
            'settings': self.settings.settings if hasattr(self, 'settings') else {}
        }
        with open(os.path.join(os.path.dirname(__file__), "window_state.json"), 'w') as f:
            json.dump(state, f)
        
    def create_toplevel_window(self, window_class, *args, **kwargs):
        """Create a new toplevel window that inherits always-on-top state"""
        window = window_class(self.root, *args, **kwargs)
        window.attributes('-topmost', self.always_on_top)
        return window
        
    def show_dialog(self, dialog_class, *args, **kwargs):
        """Show a dialog that inherits always-on-top state"""
        dialog = dialog_class(self.root, *args, **kwargs)
        if self.always_on_top:
            dialog.attributes('-topmost', True)
        dialog.show_dialog()

    def handle_notification_click(self, event):
        """Handle notification button click with proper event handling."""
        if not self.notification_ui:
            return
            
        if not self.notification_ui.visible:
            self.notification_ui.show()
            self.root.after(100, lambda: self.root.bind('<Button-1>', self.check_click_outside_popover))
        else:
            self.notification_ui.hide()
            self.root.unbind('<Button-1>')
            
        return "break"
        
    def check_click_outside_popover(self, event):
        """Checks if click is outside the notification popover."""
        try:
            if not hasattr(self, 'notification_ui') or not self.notification_ui or not self.notification_ui.visible:
                return
            
            click_x = event.x_root
            click_y = event.y_root
            
            button = self.notification_button
            if (button.winfo_rootx() <= click_x <= button.winfo_rootx() + button.winfo_width() and
                button.winfo_rooty() <= click_y <= button.winfo_rooty() + button.winfo_height()):
                return "break"
            
            if not self.notification_ui.is_click_inside(click_x, click_y):
                self.notification_ui.hide()
            
        except Exception as e:
            logging.error(f"Error checking click outside popover: {e}")

    def toggle_notification_popover(self, *args):
        """Toggle the notification popover visibility."""
        try:
            if not hasattr(self, 'notification_ui') or not self.notification_ui:
                self.notification_ui = NotificationPopover(self.root, self)
                self.notification_ui.show()
            elif not self.notification_ui.visible:
                self.notification_ui.show()
            else:
                self.notification_ui.hide()
            
        except Exception as e:
            logging.error(f"Error toggling notification popover: {e}")

    def update_notification_button(self):
        """Updates the notification button text with unread count."""
        try:
            unread_count = len(self.unread_notifications)
            self.notification_button.configure(text=f"🔔 {unread_count}")
            self.notification_button.update()
            
        except Exception as e:
            logging.error(f"Error updating notification button: {e}")

    def clear_notifications(self):
        """Clears all notifications and updates the display."""
        try:
            self.notifications.clear()
            self.unread_notifications.clear()
            self.update_notification_button()
            self.toggle_notification_popover()
        except Exception as e:
            logging.error(f"Error clearing notifications: {e}")

    def add_notification(self, message, level="info"):
        """Add a notification to the list and persist it."""
        try:
            notification = {
                "message": message,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "level": level,
                "read": False
            }
            
            self.notifications.append(notification)
            
            if not notification["read"]:
                self.unread_notifications.append(notification)
            
            try:
                config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
                notification_file = os.path.join(config_dir, "notifications.json")
                os.makedirs(config_dir, exist_ok=True)
                with open(notification_file, 'w') as f:
                    json.dump(self.notifications, f)
            except Exception as e:
                logging.error(f"Failed to save notification to file: {e}")
            
            if hasattr(self, 'notification_ui') and self.notification_ui and self.notification_ui.visible:
                self.notification_ui.update_notifications()
                
            self.update_notification_button()
                
            logging.info(f"Added notification: {message}")
        except Exception as e:
            logging.error(f"Failed to add notification: {e}")

    def update_notification_display(self):
        """
        Updates the notification display in the GUI.
        """
        try:
            if hasattr(self, 'notification_frame'):
                for widget in self.notification_frame.winfo_children():
                    widget.destroy()
                
                for notification in reversed(self.notifications[-10:]):
                    color = "#FFE4E1" if notification["level"] == "warning" else "#E8F5E9"
                    msg = f"{notification['timestamp']}: {notification['message']}"
                    
                    label = ctk.CTkLabel(
                        self.notification_frame,
                        text=msg,
                        fg_color=color,
                        corner_radius=8,
                        padx=10,
                        pady=5
                    )
                    label.pack(fill="x", padx=5, pady=2)
        except Exception as e:
            logging.error(f"Error updating notification display: {e}")

    def on_security_key_double_click(self, security_keys_list):
        """
        Handles double-click events on the security keys list.

        Args:
            security_keys_list (CTkTextbox): The textbox widget simulating the security key list.
        """
        try:
            cursor_position = security_keys_list.index("@%d,%d" % (security_keys_list.winfo_pointerx(), security_keys_list.winfo_pointery()))
            line_start = cursor_position.split(".")[0]
            key_name = security_keys_list.get(f"{line_start}.0", f"{line_start}.end").strip()

            if key_name:
                logging.info(f"Double-clicked on security key: {key_name}")
                self.open_windows_hello_setup(key_name)
            else:
                logging.warning("Double-clicked but no valid key was found.")
                self.update_notification("No valid security key was selected.", "red")
        except Exception as e:
            logging.error(f"Error handling double-click event: {e}")
            self.update_notification(f"Error: An error occurred while handling the double-click event.\n{e}", "red")
    
    def update_notification(self, message, status="info"):
        """Update the notification label with the given message and status."""
        try:
            # Map status to colors
            color_map = {
                "info": "gray",
                "success": "green",
                "warning": "orange",
                "error": "red"
            }
            color = color_map.get(status, "gray")
            
            def update_label():
                try:
                    if hasattr(self, 'notification_label'):
                        self.notification_label.configure(text=message)
                        self.notification_label.configure(text_color=color)
                except Exception as e:
                    logging.error(f"Error updating notification label: {e}")
            
            # Schedule the update on the main thread
            self.root.after(0, update_label)
            
        except Exception as e:
            logging.error(f"Error in update_notification: {e}")
    
    @staticmethod
    def update_notification_static(message, color="green"):
        """
        Static method to update the notification label from outside the class.
        """
        instance = QuickLinksApp.get_instance()
        if instance:
            instance.update_notification(message, color)

    def click_animation(self):
        """
        Handles the click animation.
        """
        try:
            logging.debug("Processing click animation...")
            self.root.after(1000, self.click_animation)
        except Exception as e:
            logging.error(f"Error in click animation: {e}")

    def check_vpn_connection(self, test_url="http://internal.example.com"):
        try:
            logging.debug(f"Checking VPN connection using {test_url}")
            socket.gethostbyname(VPN_CHECK_URL)
            logging.info("VPN connection successful")
            return True
        except socket.gaierror:
            logging.warning("VPN connection check failed")
            return False
        except Exception as e:
            logging.error(f"Unexpected error checking VPN connection: {e}", exc_info=True)
            return False

    def open_settings(self):
        """Open settings dialog"""
        from settings_dialog import SettingsDialog
        dialog = self.show_dialog(SettingsDialog)
        dialog.show_dialog()

    def connect_vpn(self):
        """Open the Cisco VPN window"""
        try:
            vpn_paths = [
                r"C:\Program Files (x86)\Cisco\Cisco AnyConnect Secure Mobility Client\vpnui.exe",
                r"C:\Program Files\Cisco\Cisco AnyConnect Secure Mobility Client\vpnui.exe"
            ]
            
            for path in vpn_paths:
                if os.path.exists(path):
                    subprocess.Popen(path)
                    return True
                    
            logging.error("Cisco AnyConnect not found in expected locations")
            return False
        except Exception as e:
            logging.error(f"Error opening VPN window: {e}")
            return False

    def is_vpn_connected(self):
        """Check if VPN is connected by querying the VPN client."""
        try:
            result = subprocess.run(
                ["vpncli.exe", "state"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            return "Connected" in result.stdout
        except Exception as e:
            logging.error(f"Error checking VPN status: {e}")
            return False
            
    def get_scanner_code(self, serial, pin):
        """Get scanner code using proper Midway authentication."""
        try:
            serial_number = parse_sn(serial)
            if not serial_number:
                raise Exception("Invalid serial number format")
            
            if not self.is_vpn_connected():
                raise Exception("VPN not connected")
            
            midway_helper = MidwayAuthHelper()
            
            for region in Region:
                try:
                    access, secret, session = midway_helper.get_creds(
                        device_admin_lambda_accounts[region]["aws_account_id"],
                        device_admin_lambda_accounts[region]["identity_pool_id"]
                    )
                    
                    aws_auth = AWS4Auth(
                        access,
                        secret,
                        region.value,
                        "execute-api",
                        session_token=session,
                    )
                    
                    url = f"{device_admin_lambda_accounts[region]['endpoint']}/devices/{serial_number}/passcode"
                    
                    def get_code():
                        response = requests.get(url, auth=aws_auth, timeout=30)
                        response.raise_for_status()
                        return response.json()
                    
                    result = retry(get_code, 3)
                    
                    if "reported" in result:
                        code = result["reported"]
                        if "desired" in result and result["reported"] != result["desired"]:
                            code = f"Current: {result['reported']}, Upcoming: {result['desired']}"
                        return code
                        
                except Exception as region_error:
                    logging.debug(f"Failed to get code from {region}: {region_error}")
                    continue
            
            raise Exception("Scanner code not found in any region")
            
        except Exception as e:
            logging.error(f"Error getting scanner code: {e}")
            raise Exception(f"Failed to get scanner code: {str(e)}")
            
    def get_midway_token(self):
        """Get Midway authentication token by first running mwinit."""
        try:
            result = subprocess.run(
                ["mwinit", "-o"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if "Authentication successful" not in result.stdout:
                raise Exception("mwinit authentication failed")
            
            home = os.path.expanduser("~")
            token_file = os.path.join(home, ".midway", "credentials")
            
            if not os.path.exists(token_file):
                raise Exception("Midway credentials file not found")
                
            with open(token_file, 'r') as f:
                creds = json.load(f)
                
            if 'AccessKeyId' not in creds or 'SecretAccessKey' not in creds or 'SessionToken' not in creds:
                raise Exception("Invalid credentials format in Midway file")
                
            return {
                'AccessKeyId': creds['AccessKeyId'],
                'SecretKey': creds['SecretAccessKey'],
                'SessionToken': creds['SessionToken']
            }
            
        except subprocess.TimeoutExpired:
            logging.error("mwinit timed out")
            raise Exception("Authentication timed out. Please try again.")
        except Exception as e:
            logging.error(f"Error getting Midway token: {e}")
            raise Exception(f"Failed to get authentication token: {str(e)}")
            
class Region(Enum):
    us_west_2 = "us-west-2"
    ap_northeast_1 = "ap-northeast-1"
    ap_south_1 = "ap-south-1"
    eu_west_1 = "eu-west-1"
    us_east_1 = "us-east-1"

    def __str__(self):
        return self.value

device_admin_lambda_accounts = {
    Region.us_west_2: {
        "aws_account_id": "315464380417",
        "identity_pool_id": "us-west-2:d40aaf6c-7dac-4055-8521-5536b1ca0f0b",
        "endpoint": "https://device-admin.integ.us-west-2.device-manager.a2z.com",
    },
    Region.ap_northeast_1: {
        "aws_account_id": "020236585023",
        "identity_pool_id": "ap-northeast-1:e31b73b6-40be-4593-bf81-8453ac65002e",
        "endpoint": "https://device-admin.prod.ap-northeast-1.device-manager.a2z.com",
    },
    Region.ap_south_1: {
        "aws_account_id": "844454935789",
        "identity_pool_id": "ap-south-1:78af6327-f5b3-4d4a-871a-3fa139199f8a",
        "endpoint": "https://device-admin.prod.ap-south-1.device-manager.a2z.com",
    },
    Region.eu_west_1: {
        "aws_account_id": "431731427104",
        "identity_pool_id": "eu-west-1:3db507bd-17b3-4b71-b62a-8f8cc4d16a21",
        "endpoint": "https://device-admin.prod.eu-west-1.device-manager.a2z.com",
    },
    Region.us_east_1: {
        "aws_account_id": "350385424153",
        "identity_pool_id": "us-east-1:a4768e9b-429c-4bfd-82da-574f0cca1630",
        "endpoint": "https://device-admin.prod.us-east-1.device-manager.a2z.com",
    },
}

class MidwayAuthHelper:
    def __init__(self):
        self.cookies = self._get_cookies()
        self.jwt = self._get_midway_token(self.cookies, "cognito.amazon.com")

    def get_creds(self, aws_account_id, identity_pool_id):
        """Get AWS credentials using Midway authentication."""
        try:
            cognito_id = self._get_cognito_id_for_jwt(
                aws_account_id,
                identity_pool_id,
                self.jwt,
            )
            return self._issue_creds_for_cognito_id(cognito_id, self.jwt)
        except Exception as e:
            logging.error(f"Error getting credentials: {e}")
            raise

    def _get_cookies(self):
        """Get Midway cookies from the cookie file."""
        cookies = {}
        home_dir = "userprofile" if os.name == "nt" else "HOME"
        midway_cookie_path = os.path.join(os.environ.get(home_dir), ".midway", "cookie")
        
        try:
            with open(midway_cookie_path, "r") as file:
                for line in file:
                    parts = line.split()
                    if len(parts) == 7:
                        cookies[parts[5]] = parts[6]
            return cookies
        except FileNotFoundError:
            raise Exception("Midway token not found. Please run 'mwinit --aea' before retry")

    def _get_midway_token(self, cookies, audience):
        """Get Midway token using the cookies."""
        midway_url = "https://midway-auth.amazon.com/SSO"
        audience_url = f"https://{audience}:443"
        
        headers = {
            "host": "midway-auth.amazon.com",
            "origin": audience
        }
        
        params = {
            "response_type": "id_token",
            "scope": "openid",
            "client_id": audience,
            "redirect_uri": audience_url,
            "nonce": str(uuid.uuid4().hex)
        }
        
        response = requests.get(
            midway_url,
            params=params,
            cookies=cookies,
            headers=headers
        )
        response.raise_for_status()
        return response.text

    def _get_cognito_id_for_jwt(self, aws_account, cognito_pool_id, jwt):
        """Get Cognito ID using the JWT token."""
        identity_response = boto3.client("cognito-identity").get_id(
            AccountId=aws_account,
            IdentityPoolId=cognito_pool_id,
            Logins={"midway-auth.amazon.com": jwt},
        )
        return identity_response["IdentityId"]

    def _issue_creds_for_cognito_id(self, cognito_id, jwt):
        """Get AWS credentials using the Cognito ID."""
        credentials_response = boto3.client(
            "cognito-identity"
        ).get_credentials_for_identity(
            IdentityId=cognito_id,
            Logins={"midway-auth.amazon.com": jwt}
        )
        credentials = credentials_response["Credentials"]
        return (
            credentials["AccessKeyId"],
            credentials["SecretKey"],
            credentials["SessionToken"]
        )

def retry(f, times):
    """Retry a function multiple times."""
    try:
        return f()
    except:
        if times == 0:
            raise
        return retry(f, times - 1)

def parse_sn(sn):
    """Parse scanner serial number."""
    pattern = re.compile("[sS]?([a-zA-Z0-9]+)(_[a-zA-Z0-9]*)?")
    match = pattern.match(sn)
    groups = [] if not match else match.groups()
    return groups[0] if groups else None

class TextBoxHandler(logging.Handler):
    """
    Custom logging handler that writes log records to a textbox.
    """
    def __init__(self, app):
        super().__init__()
        self.app = app

    def emit(self, record):
        log_entry = self.format(record)
        self.app.update_logs_in_main_thread(log_entry)

def check_dependencies():
    """
    Verifies that all required dependencies are installed using importlib.metadata.
    
    Raises:
        EnvironmentError: If any dependencies are missing.
    """
    required_packages = {
        'playwright': 'Playwright',
        'hidapi': 'HID Library',
        'customtkinter': 'CustomTkinter',
        'requests': 'Requests',
        'boto3': 'Boto3',
        'selenium': 'Selenium',
        'pyautogui': 'PyAutoGUI'
    }
    
    missing = []
    for package, display_name in required_packages.items():
        try:
            importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            missing.append(display_name)
    
    if missing:
        raise EnvironmentError(f"Missing dependencies: {', '.join(missing)}")

VPN_CHECK_INTERVAL = 5000
DEFAULT_WINDOW_SIZE = "600x700"
COLOR_SCHEME = {
    "success": "#2B7DE9",
    "warning": "orange",
    "error": "red"
}

def validate_serial(serial):
    """Validate serial number format."""
    pattern = r'^[A-Z0-9]{10,}$'
    return bool(re.match(pattern, serial))

def save_last_successful_settings(region):
    """Save last successful configuration."""
    settings = {
        'region': region,
        'last_success': datetime.now().isoformat()
    }
    with open('last_settings.json', 'w') as f:
        json.dump(settings, f)

def main():
    """
    Main entry point of the application.
    Checks VPN connection and launches appropriate window.
    """
    try:
        check_dependencies()
        
        setup_logging()
        
        # Check VPN connection before proceeding
        if not is_vpn_connected():
            logging.warning("VPN not connected. Showing VPN warning window.")
            show_vpn_warning()
            return
            
        root = ctk.CTk()
        root.title("Quick Links Dashboard")
        
        root.geometry(DEFAULT_WINDOW_SIZE)
        
        app = QuickLinksApp(root)
        
        root.mainloop()
        
    except Exception as e:
        error_message = f"Error starting application: {str(e)}"
        logging.error(error_message)
        messagebox.showerror("Error", error_message)
        sys.exit(1)

if __name__ == "__main__":
    main()
