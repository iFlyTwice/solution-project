import customtkinter as ctk
from tkinter import messagebox
import json
import os
import logging

class SettingsDialog:
    def __init__(self, parent):
        self.parent = parent
        self.settings_file = os.path.join(os.path.dirname(__file__), "settings.json")
        self.settings = self.load_settings()
        self.apply_settings()  # Apply settings immediately on initialization
        
    def load_settings(self):
        """Load settings from JSON file"""
        default_settings = {
            "vpn_server": "iad-f-orca.amazon.com",
            "auto_connect": False,
            "theme": "system",
            "retry_connection": True,
            "opacity": 1.0,
            "show_notifications": True,
            "notification_sound": True,
            "show_icons": True,
            "compact_mode": False,
            "autosave_settings": True
        }
        
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    saved_settings = json.load(f)
                    # Update default settings with saved ones
                    default_settings.update(saved_settings)
            except Exception as e:
                logging.error(f"Error loading settings: {e}")
        return default_settings
        
    def save_settings(self):
        """Save settings to JSON file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving settings: {e}")
            
    def apply_settings(self):
        """Apply all current settings"""
        self.apply_theme()
        if hasattr(self.parent, 'attributes'):
            self.parent.attributes('-alpha', self.settings.get("opacity", 1.0))
        
        # Trigger UI refresh if compact mode changes
        if hasattr(self.parent, 'refresh_ui'):
            self.parent.refresh_ui()
            
    def apply_theme(self, theme=None):
        """Apply the selected theme"""
        if theme is None:
            theme = self.settings.get("theme", "system")
        ctk.set_appearance_mode(theme)
        
    def get_vpn_server(self):
        """Get the configured VPN server"""
        return self.settings.get("vpn_server", "iad-f-orca.amazon.com")
        
    def should_auto_connect(self):
        """Check if VPN should auto-connect"""
        return self.settings.get("auto_connect", False)
        
    def show_dialog(self):
        """Show settings dialog"""
        settings_window = ctk.CTkToplevel(self.parent)
        settings_window.title("Settings")
        settings_window.geometry("800x700")  # Made window wider for better spacing
        
        # Center the window
        window_width = 800
        window_height = 700
        screen_width = settings_window.winfo_screenwidth()
        screen_height = settings_window.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        settings_window.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        # Create main container with padding
        main_container = ctk.CTkFrame(settings_window, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=30, pady=20)

        # Header section with modern title and subtitle
        header_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Settings",
            font=("Helvetica", 28, "bold"),
            text_color=("gray10", "gray90")
        )
        title_label.pack(pady=(0, 5))
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Customize your Quick Links experience",
            font=("Helvetica", 14),
            text_color=("gray40", "gray60")
        )
        subtitle_label.pack()

        # Create modern tabview with larger tabs
        tabview = ctk.CTkTabview(
            main_container,
            fg_color=("gray95", "gray10"),
            segmented_button_fg_color=("gray85", "gray20"),
            segmented_button_selected_color=("gray75", "gray30"),
            segmented_button_selected_hover_color=("gray70", "gray35"),
            segmented_button_unselected_hover_color=("gray80", "gray25")
        )
        tabview.pack(fill="both", expand=True)

        # Create tabs with icons (using emoji as placeholders)
        vpn_tab = tabview.add("🔒 VPN")
        ui_tab = tabview.add("🎨 Interface")
        notif_tab = tabview.add("🔔 Notifications")
        links_tab = tabview.add("🔗 Quick Links")

        # VPN Settings Tab
        vpn_frame = ctk.CTkFrame(vpn_tab, fg_color="transparent")
        vpn_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # VPN Server section
        vpn_section = self._create_section(vpn_frame, "VPN Configuration", "Configure your VPN connection settings")
        
        server_entry = ctk.CTkEntry(
            vpn_section,
            placeholder_text="Enter VPN server address",
            width=300,
            height=35
        )
        server_entry.insert(0, self.settings.get("vpn_server", ""))
        server_entry.pack(pady=(10, 5))

        auto_connect = ctk.CTkSwitch(
            vpn_section,
            text="Auto-connect to VPN on startup",
            font=("Helvetica", 12),
            progress_color=("#2B7DE9", "#306998"),
            variable=ctk.BooleanVar(value=self.settings.get("auto_connect", False))
        )
        auto_connect.pack(pady=10)

        retry_connection = ctk.CTkSwitch(
            vpn_section,
            text="Automatically retry failed connections",
            font=("Helvetica", 12),
            progress_color=("#2B7DE9", "#306998"),
            variable=ctk.BooleanVar(value=self.settings.get("retry_connection", True))
        )
        retry_connection.pack(pady=10)

        # Interface Settings Tab
        ui_frame = ctk.CTkFrame(ui_tab, fg_color="transparent")
        ui_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Appearance section
        appearance_section = self._create_section(ui_frame, "Appearance", "Customize the look and feel")
        
        theme_var = ctk.StringVar(value=self.settings.get("theme", "system"))
        theme_label = ctk.CTkLabel(appearance_section, text="Theme Mode:", font=("Helvetica", 12))
        theme_label.pack(pady=(10, 5))
        
        theme_frame = ctk.CTkFrame(appearance_section, fg_color="transparent")
        theme_frame.pack(fill="x", pady=5)
        
        themes = [("System", "system"), ("Light", "light"), ("Dark", "dark")]
        for i, (text, value) in enumerate(themes):
            ctk.CTkRadioButton(
                theme_frame,
                text=text,
                value=value,
                variable=theme_var,
                font=("Helvetica", 12),
                fg_color=("#2B7DE9", "#306998")
            ).pack(side="left", padx=10)

        opacity_label = ctk.CTkLabel(appearance_section, text="Window Opacity:", font=("Helvetica", 12))
        opacity_label.pack(pady=(15, 5))
        
        opacity_slider = ctk.CTkSlider(
            appearance_section,
            from_=0.3,
            to=1.0,
            number_of_steps=70,
            width=250,
            progress_color=("#2B7DE9", "#306998"),
            button_color=("#2B7DE9", "#306998"),
            button_hover_color=("#2269D2", "#245580")
        )
        opacity_slider.set(self.settings.get("opacity", 1.0))
        opacity_slider.pack(pady=(0, 15))

        # Notification Settings Tab
        notif_frame = ctk.CTkFrame(notif_tab, fg_color="transparent")
        notif_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Notifications section
        notif_section = self._create_section(notif_frame, "Notification Settings", "Configure how you receive notifications")
        
        show_notifications = ctk.CTkSwitch(
            notif_section,
            text="Enable notifications",
            font=("Helvetica", 12),
            progress_color=("#2B7DE9", "#306998"),
            variable=ctk.BooleanVar(value=self.settings.get("show_notifications", True))
        )
        show_notifications.pack(pady=10)

        notification_sound = ctk.CTkSwitch(
            notif_section,
            text="Play notification sounds",
            font=("Helvetica", 12),
            progress_color=("#2B7DE9", "#306998"),
            variable=ctk.BooleanVar(value=self.settings.get("notification_sound", True))
        )
        notification_sound.pack(pady=10)

        # Quick Links Tab
        links_frame = ctk.CTkFrame(links_tab, fg_color="transparent")
        links_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Links section
        links_section = self._create_section(links_frame, "Quick Links Settings", "Customize your quick links display")
        
        show_icons = ctk.CTkSwitch(
            links_section,
            text="Show link icons",
            font=("Helvetica", 12),
            progress_color=("#2B7DE9", "#306998"),
            variable=ctk.BooleanVar(value=self.settings.get("show_icons", True))
        )
        show_icons.pack(pady=10)

        compact_mode = ctk.CTkSwitch(
            links_section,
            text="Compact mode",
            font=("Helvetica", 12),
            progress_color=("#2B7DE9", "#306998"),
            variable=ctk.BooleanVar(value=self.settings.get("compact_mode", False))
        )
        compact_mode.pack(pady=10)

        # Bottom button section with modern styling
        button_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        button_frame.pack(fill="x", pady=20)

        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=120,
            height=35,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            command=settings_window.destroy
        )
        cancel_button.pack(side="right", padx=10)

        save_button = ctk.CTkButton(
            button_frame,
            text="Save Changes",
            width=120,
            height=35,
            fg_color=("#2B7DE9", "#306998"),
            hover_color=("#2269D2", "#245580"),
            command=lambda: self._save_and_close(settings_window)
        )
        save_button.pack(side="right")

    def _create_section(self, parent, title, subtitle=None):
        """Helper method to create consistent section styling"""
        section = ctk.CTkFrame(parent, fg_color=("gray90", "gray15"), corner_radius=10)
        section.pack(fill="x", pady=10, padx=5)
        
        title_label = ctk.CTkLabel(
            section,
            text=title,
            font=("Helvetica", 16, "bold"),
            text_color=("gray10", "gray90")
        )
        title_label.pack(pady=(15, 0), padx=15, anchor="w")
        
        if subtitle:
            subtitle_label = ctk.CTkLabel(
                section,
                text=subtitle,
                font=("Helvetica", 12),
                text_color=("gray40", "gray60")
            )
            subtitle_label.pack(pady=(0, 15), padx=15, anchor="w")
        
        return section

    def _save_and_close(self, window):
        """Save settings and close the window"""
        # Get all the settings from the dialog
        for widget in window.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                self._collect_settings_from_frame(widget)
        
        # Save and apply settings
        self.save_settings()
        self.apply_settings()
        
        # Refresh the main window's UI if compact mode changed
        if hasattr(self.parent, 'refresh_ui'):
            self.parent.refresh_ui()
            
        window.destroy()
        
    def _collect_settings_from_frame(self, frame):
        """Recursively collect settings from all widgets in the frame"""
        for widget in frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                self._collect_settings_from_frame(widget)
            elif isinstance(widget, ctk.CTkSwitch):
                # Get the switch text and use it to determine the setting
                setting_name = widget.cget("text").lower().replace(" ", "_")
                if setting_name in self.settings:
                    self.settings[setting_name] = widget.get()
            elif isinstance(widget, ctk.CTkSlider):
                # Handle opacity slider
                if "opacity" in self.settings:
                    self.settings["opacity"] = widget.get()
            elif isinstance(widget, ctk.CTkEntry):
                # Handle VPN server entry
                if "vpn_server" in self.settings:
                    self.settings["vpn_server"] = widget.get()
            elif isinstance(widget, ctk.CTkRadioButton):
                # Handle theme selection
                if widget.get() == widget.cget("value") and "theme" in self.settings:
                    self.settings["theme"] = widget.cget("value")
