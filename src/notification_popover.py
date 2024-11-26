import os
import json
import logging
import customtkinter as ctk

class NotificationPopover:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.visible = False
        self.window = None
        
        # Create the popover window
        self.create_popover()
        
    def create_popover(self):
        """Creates the notification popover window with modern styling."""
        self.window = ctk.CTkToplevel(self.root)
        self.window.withdraw()  # Hide initially
        
        # Set window attributes
        self.window.overrideredirect(True)  # Remove window decorations
        self.window.attributes('-topmost', True)
        
        # Create main frame with rounded corners and padding
        self.main_frame = ctk.CTkFrame(
            self.window,
            fg_color=("gray95", "gray15"),
            corner_radius=12
        )
        self.main_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Header frame
        header_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color="transparent",
            height=40
        )
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Make header draggable
        header_frame.bind('<Button-1>', self.start_drag)
        header_frame.bind('<B1-Motion>', self.on_drag)
        
        # Title with notification count
        self.title_label = ctk.CTkLabel(
            header_frame,
            text="Notifications",
            font=("Segoe UI", 14, "bold"),
            anchor="w"
        )
        self.title_label.pack(side="left", padx=5)
        
        # Make title label draggable too
        self.title_label.bind('<Button-1>', self.start_drag)
        self.title_label.bind('<B1-Motion>', self.on_drag)
        
        # Clear all button
        clear_button = ctk.CTkButton(
            header_frame,
            text="Clear All",
            font=("Segoe UI", 12),
            width=70,
            height=24,
            command=self.clear_all_notifications,
            fg_color=("gray75", "gray30"),
            hover_color=("gray65", "gray40")
        )
        clear_button.pack(side="right", padx=5)
        
        # Separator
        separator = ctk.CTkFrame(
            self.main_frame,
            height=1,
            fg_color=("gray80", "gray25")
        )
        separator.pack(fill="x", padx=10, pady=5)
        
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
            
    def update_notifications(self):
        """Updates the notification list."""
        if not self.window or not self.notification_container:
            return
            
        # Clear existing notifications
        for widget in self.notification_container.winfo_children():
            widget.destroy()
            
        if not self.app.notifications:
            self.empty_label.pack(pady=20)
            self.title_label.configure(text="Notifications (0)")
            return
        else:
            self.empty_label.pack_forget()
            self.title_label.configure(text=f"Notifications ({len(self.app.notifications)})")
            
        # Add notifications in reverse chronological order
        for notification in reversed(self.app.notifications):
            self.create_notification_item(notification)
            
    def create_notification_item(self, notification):
        """Creates a single notification item."""
        # Container frame for the notification
        frame = ctk.CTkFrame(
            self.notification_container,
            fg_color=("gray90", "gray20") if not notification.get("read", False) else "transparent",
            corner_radius=8
        )
        frame.pack(fill="x", padx=5, pady=3)
        
        # Icon based on notification level
        icon = "🔴" if notification["level"] == "error" else "🟡" if notification["level"] == "warning" else "🔵"
        icon_label = ctk.CTkLabel(
            frame,
            text=icon,
            font=("Segoe UI", 14)
        )
        icon_label.pack(side="left", padx=(10, 5), pady=10)
        
        # Message and timestamp
        text_frame = ctk.CTkFrame(frame, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=5)
        
        message_label = ctk.CTkLabel(
            text_frame,
            text=notification["message"],
            font=("Segoe UI", 12),
            justify="left",
            wraplength=200
        )
        message_label.pack(anchor="w")
        
        time_label = ctk.CTkLabel(
            text_frame,
            text=notification["timestamp"],
            font=("Segoe UI", 10),
            text_color=("gray50", "gray60")
        )
        time_label.pack(anchor="w")
        
        # Mark as read when clicked
        def mark_as_read(event):
            if not notification.get("read", False):
                notification["read"] = True
                if notification in self.app.unread_notifications:
                    self.app.unread_notifications.remove(notification)
                frame.configure(fg_color="transparent")
                self.app.update_notification_button()
                
                # Save updated notifications
                try:
                    config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
                    notification_file = os.path.join(config_dir, "notifications.json")
                    os.makedirs(config_dir, exist_ok=True)
                    with open(notification_file, 'w') as f:
                        json.dump(self.app.notifications, f)
                except Exception as e:
                    logging.error(f"Failed to save notification state: {e}")
                
        frame.bind("<Button-1>", mark_as_read)
        message_label.bind("<Button-1>", mark_as_read)
        time_label.bind("<Button-1>", mark_as_read)
        
        # Add hover effect
        def on_enter(e):
            if notification.get("read", False):
                frame.configure(fg_color=("gray85", "gray25"))
                
        def on_leave(e):
            if notification.get("read", False):
                frame.configure(fg_color="transparent")
                
        frame.bind("<Enter>", on_enter)
        frame.bind("<Leave>", on_leave)
        
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
        """Start window drag operation."""
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        self._window_start_x = self.window.winfo_x()
        self._window_start_y = self.window.winfo_y()
        
    def on_drag(self, event):
        """Handle window drag operation."""
        dx = event.x_root - self._drag_start_x
        dy = event.y_root - self._drag_start_y
        new_x = self._window_start_x + dx
        new_y = self._window_start_y + dy
        self.window.geometry(f"+{new_x}+{new_y}")
