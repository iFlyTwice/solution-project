import os
import json
import logging
import customtkinter as ctk

class NotificationPopover:
    NOTIFICATION_ICONS = {
        "error": {"symbol": "⛔", "color": "#EF4444"},
        "warning": {"symbol": "⚠️", "color": "#F59E0B"},
        "info": {"symbol": "ℹ️", "color": "#3B82F6"},
        "success": {"symbol": "✅", "color": "#10B981"}
    }

    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.visible = False
        self.window = None
        self.current_filter = "all"  # Filter state
        self.sort_order = "newest"   # Sort state
        
        # Create the popover window
        self.create_popover()
        
    def create_popover(self):
        """Creates the notification popover window with modern styling."""
        self.window = ctk.CTkToplevel(self.root)
        self.window.withdraw()
        
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        
        # Add shadow effect with nested frames
        outer_frame = ctk.CTkFrame(
            self.window,
            fg_color=("gray85", "gray20"),
            corner_radius=15
        )
        outer_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.main_frame = ctk.CTkFrame(
            outer_frame,
            fg_color=("gray95", "gray10"),
            corner_radius=12
        )
        self.main_frame.pack(fill="both", expand=True, padx=1, pady=1)

        # Make the entire window draggable
        for widget in [self.window, outer_frame, self.main_frame]:
            widget.bind('<Button-1>', self.start_drag)
            widget.bind('<B1-Motion>', self.on_drag)
        
        # Header frame
        self._create_header_frame()
        
        # Filter and Sort Controls
        self._create_filter_controls()
        
        # Separator
        self._create_separator()
        
        # Scrollable notification container
        self.notification_container = ctk.CTkScrollableFrame(
            self.main_frame,
            fg_color="transparent",
            height=300
        )
        self.notification_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Empty state label
        self.empty_label = ctk.CTkLabel(
            self.notification_container,
            text="No notifications",
            font=("Segoe UI", 12),
            text_color=("gray60", "gray50")
        )

    def _create_header_frame(self):
        """Creates the header frame with modern styling."""
        header_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color="transparent",
            height=45
        )
        header_frame.pack(fill="x", padx=12, pady=(12, 5))
        
        # Title with notification count
        self.title_label = ctk.CTkLabel(
            header_frame,
            text="Notifications",
            font=("Segoe UI Semibold", 16),
            anchor="w"
        )
        self.title_label.pack(side="left", padx=5)
        
        # Controls frame with modern buttons
        controls_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_frame.pack(side="right", padx=5)
        
        # Modern button style
        button_style = {
            "corner_radius": 8,
            "font": ("Segoe UI", 11),
            "width": 80,
            "height": 28,
            "fg_color": ("gray80", "gray25"),
            "hover_color": ("gray70", "gray35"),
            "text_color": ("gray15", "gray90")
        }
        
        mark_read_button = ctk.CTkButton(
            controls_frame,
            text="Mark All",
            command=self.mark_all_as_read,
            **button_style
        )
        mark_read_button.pack(side="left", padx=4)
        
        clear_button = ctk.CTkButton(
            controls_frame,
            text="Clear All",
            command=self.clear_all_notifications,
            **button_style
        )
        clear_button.pack(side="left", padx=4)

    def _create_filter_controls(self):
        """Creates the filter and sort controls."""
        filter_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color="transparent",
            height=30
        )
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        # Filter dropdown
        filter_values = ["all", "unread", "error", "warning", "info", "success"]
        self.filter_var = ctk.StringVar(value="all")
        filter_dropdown = ctk.CTkOptionMenu(
            filter_frame,
            values=filter_values,
            variable=self.filter_var,
            command=self._on_filter_change,
            width=100,
            height=24,
            font=("Segoe UI", 12)
        )
        filter_dropdown.pack(side="left", padx=5)
        
        # Sort dropdown
        sort_values = ["newest", "oldest"]
        self.sort_var = ctk.StringVar(value="newest")
        sort_dropdown = ctk.CTkOptionMenu(
            filter_frame,
            values=sort_values,
            variable=self.sort_var,
            command=self._on_sort_change,
            width=100,
            height=24,
            font=("Segoe UI", 12)
        )
        sort_dropdown.pack(side="right", padx=5)

    def _create_separator(self):
        """Creates a separator line."""
        separator = ctk.CTkFrame(
            self.main_frame,
            height=1,
            fg_color=("gray80", "gray25")
        )
        separator.pack(fill="x", padx=10, pady=5)

    def _on_filter_change(self, value):
        """Handles filter change."""
        self.current_filter = value
        self.update_notifications()

    def _on_sort_change(self, value):
        """Handles sort order change."""
        self.sort_order = value
        self.update_notifications()

    def mark_all_as_read(self):
        """Marks all notifications as read."""
        for notification in self.app.notifications:
            notification["read"] = True
        self.app.unread_notifications.clear()
        self.update_notifications()
        self.app.update_notification_button()
        self._save_notifications()

    def _save_notifications(self):
        """Saves notifications to file."""
        try:
            config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
            notification_file = os.path.join(config_dir, "notifications.json")
            os.makedirs(config_dir, exist_ok=True)
            with open(notification_file, 'w') as f:
                json.dump(self.app.notifications, f)
        except Exception as e:
            logging.error(f"Failed to save notifications: {e}")

    def update_notifications(self):
        """Updates the notification list based on current filter and sort settings."""
        if not self.window or not self.notification_container:
            return
            
        # Clear existing notifications
        for widget in self.notification_container.winfo_children():
            widget.destroy()
            
        # Filter notifications
        filtered_notifications = self._get_filtered_notifications()
        
        if not filtered_notifications:
            self.empty_label.pack(pady=20)
            self.title_label.configure(text=f"Notifications (0/{len(self.app.notifications)})")
            return
        else:
            self.empty_label.pack_forget()
            self.title_label.configure(text=f"Notifications ({len(filtered_notifications)}/{len(self.app.notifications)})")
            
        # Sort notifications
        sorted_notifications = self._sort_notifications(filtered_notifications)
        
        # Add notifications
        for notification in sorted_notifications:
            self.create_notification_item(notification)

    def _get_filtered_notifications(self):
        """Returns filtered notifications based on current filter."""
        if self.current_filter == "all":
            return self.app.notifications
        elif self.current_filter == "unread":
            return self.app.unread_notifications
        else:
            return [n for n in self.app.notifications if n.get("level") == self.current_filter]

    def _sort_notifications(self, notifications):
        """Sorts notifications based on current sort order."""
        return sorted(notifications, 
                     key=lambda x: x.get("timestamp", ""),
                     reverse=(self.sort_order == "newest"))

    def create_notification_item(self, notification):
        """Creates a single notification item with enhanced modern styling."""
        frame = ctk.CTkFrame(
            self.notification_container,
            fg_color=("gray92", "gray17") if not notification.get("read", False) else ("gray95", "gray13"),
            corner_radius=10
        )
        frame.pack(fill="x", padx=8, pady=4)
        
        level = notification.get("level", "info")
        style = self.NOTIFICATION_ICONS.get(level, self.NOTIFICATION_ICONS["info"])
        
        # Content grid layout
        frame.grid_columnconfigure(1, weight=1)
        
        # Icon with background
        icon_frame = ctk.CTkFrame(
            frame,
            fg_color=self._adjust_color(style["color"], 0.15),
            corner_radius=8,
            width=32,
            height=32
        )
        icon_frame.grid(row=0, column=0, rowspan=2, padx=(10, 8), pady=10, sticky="ns")
        icon_frame.grid_propagate(False)
        
        icon_label = ctk.CTkLabel(
            icon_frame,
            text=style["symbol"],
            font=("Segoe UI", 14),
            text_color=style["color"]
        )
        icon_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Message with improved typography
        message_label = ctk.CTkLabel(
            frame,
            text=notification["message"],
            font=("Segoe UI", 12),
            justify="left",
            wraplength=220,
            anchor="w"
        )
        message_label.grid(row=0, column=1, padx=(0, 10), pady=(8, 0), sticky="w")
        
        # Info container
        info_frame = ctk.CTkFrame(frame, fg_color="transparent")
        info_frame.grid(row=1, column=1, padx=(0, 10), pady=(2, 8), sticky="w")
        
        # Category pill
        category_frame = ctk.CTkFrame(
            info_frame,
            fg_color=self._adjust_color(style["color"], 0.15),
            corner_radius=12,
            height=22
        )
        category_frame.pack(side="left", padx=(0, 8))
        
        category_label = ctk.CTkLabel(
            category_frame,
            text=level.capitalize(),
            font=("Segoe UI", 10),
            text_color=style["color"]
        )
        category_label.pack(padx=8, pady=2)
        
        # Timestamp
        time_label = ctk.CTkLabel(
            info_frame,
            text=notification["timestamp"],
            font=("Segoe UI", 10),
            text_color=("gray45", "gray65")
        )
        time_label.pack(side="left")
        
        # Hover effects
        def on_enter(e):
            frame.configure(fg_color=("gray88", "gray22"))
            
        def on_leave(e):
            frame.configure(fg_color=("gray92", "gray17") if not notification.get("read", False) else ("gray95", "gray13"))
        
        for widget in [frame, message_label, time_label, category_frame, icon_frame]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", lambda e, n=notification: self._mark_notification_as_read(n, frame))

    def _adjust_color(self, hex_color, alpha):
        """Adjusts color opacity by blending with the background color."""
        # Get the background color based on appearance mode
        bg_color = ("gray95", "gray10")  # Default background colors
        current_bg = bg_color[1] if self.window.cget("fg_color")[1].startswith("gray") else bg_color[0]
        
        # Convert the background color to RGB
        if current_bg.startswith("gray"):
            # Convert gray value to RGB
            gray_val = int(current_bg[4:]) if len(current_bg) > 4 else int(current_bg[4])
            bg_rgb = (gray_val, gray_val, gray_val)
        else:
            bg_rgb = self._hex_to_rgb(current_bg)
        
        # Convert the target color to RGB
        target_rgb = self._hex_to_rgb(hex_color)
        
        # Blend the colors
        final_rgb = self._blend_colors(target_rgb, bg_rgb, alpha)
        
        # Convert back to hex
        return "#{:02x}{:02x}{:02x}".format(*final_rgb)
    
    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _blend_colors(self, color1, color2, alpha):
        """Blend two RGB colors using alpha value."""
        return tuple(int(c1 * alpha + c2 * (1 - alpha)) for c1, c2 in zip(color1, color2))

    def _mark_notification_as_read(self, notification, frame):
        """Marks a notification as read with visual feedback."""
        if not notification.get("read", False):
            notification["read"] = True
            if notification in self.app.unread_notifications:
                self.app.unread_notifications.remove(notification)
            frame.configure(fg_color=("gray95", "gray13"))
            self.app.update_notification_button()
            self._save_notifications()

    def show(self):
        """Shows the notification popover."""
        if not self.window:
            self.create_popover()
            
        # Position the window below the notification button
        button = self.app.notification_button
        x = button.winfo_rootx() - self.window.winfo_width() + button.winfo_width()
        y = button.winfo_rooty() + button.winfo_height() + 5
        
        self.window.geometry(f"300x400+{x}+{y}")
        self.window.deiconify()
        self.visible = True
        
        # Update notifications after window is shown
        self.root.after(100, self.update_notifications)
        
    def hide(self):
        """Hides the notification popover."""
        if self.window:
            self.window.withdraw()
        self.visible = False
        
    def clear_all_notifications(self):
        """Clears all notifications."""
        self.app.notifications.clear()
        self.app.unread_notifications.clear()
        self.update_notifications()
        self.app.update_notification_button()
        
        # Save empty notifications
        try:
            config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
            notification_file = os.path.join(config_dir, "notifications.json")
            os.makedirs(config_dir, exist_ok=True)
            with open(notification_file, 'w') as f:
                json.dump([], f)
        except Exception as e:
            logging.error(f"Failed to save empty notifications: {e}")
            
    def is_click_inside(self, x, y):
        """Checks if a click is inside the popover window."""
        if not self.window:
            return False
            
        win_x = self.window.winfo_x()
        win_y = self.window.winfo_y()
        win_width = self.window.winfo_width()
        win_height = self.window.winfo_height()
        
        return (win_x <= x <= win_x + win_width and
                win_y <= y <= win_y + win_height)

    def start_drag(self, event):
        """Store initial position for dragging."""
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        self._window_start_x = self.window.winfo_x()
        self._window_start_y = self.window.winfo_y()

    def on_drag(self, event):
        """Handle window dragging."""
        # Calculate the distance moved
        dx = event.x_root - self._drag_start_x
        dy = event.y_root - self._drag_start_y
        
        # Update window position
        new_x = self._window_start_x + dx
        new_y = self._window_start_y + dy
        
        # Get screen dimensions
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # Get window dimensions
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()
        
        # Keep window within screen bounds
        new_x = max(0, min(new_x, screen_width - window_width))
        new_y = max(0, min(new_y, screen_height - window_height))
        
        # Move the window
        self.window.geometry(f"+{new_x}+{new_y}")
