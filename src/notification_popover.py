import customtkinter as ctk
from datetime import datetime
import logging
from tkinter import messagebox
from config_manager import ConfigManager

class NotificationPopover:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.visible = False
        self.notification_frame = None
        self.notifications_cache = []
        self._drag_data = {"x": 0, "y": 0, "item": None, "click_x": 0, "click_y": 0}
        
    def start_drag(self, event):
        """Start dragging the notification popover."""
        if not self.notification_frame:
            return
            
        self._drag_data = {
            "x": self.notification_frame.winfo_x(),
            "y": self.notification_frame.winfo_y(),
            "click_x": event.x_root,
            "click_y": event.y_root,
            "item": event.widget
        }
        
    def drag(self, event):
        """Handle dragging of the notification popover."""
        if not self._drag_data["item"]:
            return
            
        # Calculate the distance moved
        dx = event.x_root - self._drag_data["click_x"]
        dy = event.y_root - self._drag_data["click_y"]
        
        # Update position
        new_x = self._drag_data["x"] + dx
        new_y = self._drag_data["y"] + dy
        
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        frame_width = self.notification_frame.winfo_width()
        frame_height = self.notification_frame.winfo_height()
        
        # Keep partially visible on screen (at least 30 pixels)
        new_x = max(-frame_width + 30, min(new_x, screen_width - 30))
        new_y = max(-frame_height + 30, min(new_y, screen_height - 30))
        
        # Place the frame
        self.notification_frame.place(x=new_x, y=new_y)
        
    def stop_drag(self, event):
        """Stop dragging the notification popover."""
        if self._drag_data["item"]:
            # Save position after drag ends
            if self.notification_frame:
                state = {
                    'x': self.notification_frame.winfo_x(),
                    'y': self.notification_frame.winfo_y()
                }
                ConfigManager.save_window_state('notification_popover', state)
            
            # Reset drag data
            self._drag_data = {"x": 0, "y": 0, "item": None, "click_x": 0, "click_y": 0}
            
    def calculate_popover_position(self):
        """Calculate the optimal position for the notification popover."""
        try:
            button = self.app.notification_button
            
            # Get button position in screen coordinates
            button_x = button.winfo_rootx()
            button_y = button.winfo_rooty()
            
            # Calculate initial position (align right edge with button)
            x = button_x - 240  # Width of popover is 300, align with right edge
            y = button_y + button.winfo_height() + 5
            
            # Convert to window coordinates
            root_x = self.root.winfo_rootx()
            root_y = self.root.winfo_rooty()
            rel_x = x - root_x
            rel_y = y - root_y
            
            return rel_x, rel_y
            
        except Exception as e:
            logging.error(f"Error calculating popover position: {e}")
            return 5, 5  # Default position if calculation fails

    def create_popover(self):
        """Create the notification popover UI."""
        try:
            # Create main frame with overrideredirect
            self.notification_frame = ctk.CTkFrame(
                self.root,
                width=300,
                height=400,
                fg_color=("gray85", "gray20"),
                corner_radius=10,
                border_width=1,
                border_color=("gray80", "gray30")
            )
            
            # Load saved position or use default
            state = ConfigManager.get_window_state('notification_popover')
            x = state.get('x', 240)
            y = state.get('y', 100)
            self.notification_frame.place(x=x, y=y)
            
            # Lift the frame to be on top
            self.notification_frame.lift()
            
            # Add drag bindings
            self.notification_frame.bind('<Button-1>', self.start_drag)
            self.notification_frame.bind('<B1-Motion>', self.drag)
            self.notification_frame.bind('<ButtonRelease-1>', self.stop_drag)

            # Create title bar for dragging
            title_bar = ctk.CTkFrame(
                self.notification_frame,
                height=30,
                fg_color=("gray75", "gray25"),
                corner_radius=8
            )
            title_bar.pack(fill="x", padx=2, pady=(2, 0))
            title_bar.pack_propagate(False)
            
            # Add title label
            title_label = ctk.CTkLabel(
                title_bar,
                text="Notifications",
                font=("Helvetica", 12, "bold")
            )
            title_label.pack(side="left", padx=10)
            
            # Add clear button
            clear_btn = ctk.CTkButton(
                title_bar,
                text="Clear All",
                command=self.app.clear_notifications,
                width=80,
                height=25,
                fg_color=("gray65", "gray35"),
                hover_color=("gray55", "gray45")
            )
            clear_btn.pack(side="right", padx=5)
            
            # Bind dragging events to title bar
            for widget in [title_bar, title_label]:
                widget.bind("<Button-1>", self.start_drag)
                widget.bind("<B1-Motion>", self.drag)
                widget.bind("<ButtonRelease-1>", self.stop_drag)
            
            # Create scrollable frame for notifications
            self.notification_list = ctk.CTkScrollableFrame(
                self.notification_frame,
                width=280,
                height=350,
                fg_color="transparent"
            )
            self.notification_list.pack(fill="both", expand=True, padx=5, pady=5)
            
            # Update notifications display
            self.update_notifications()
            
        except Exception as e:
            logging.error(f"Error creating notification popover: {e}")

    def show(self):
        """Show the notification popover."""
        try:
            if self.visible:
                return
                
            self.create_popover()
            self.visible = True
            
            # Ensure popover is on top
            if self.notification_frame:
                self.notification_frame.lift()
            
            # Bind click outside to close
            self.root.bind('<Button-1>', self.app.check_click_outside_popover)
            
        except Exception as e:
            logging.error(f"Error showing notification popover: {e}")
            
    def hide(self):
        """Hide the notification popover."""
        try:
            if not self.visible:
                return
                
            if self.notification_frame:
                self.notification_frame.destroy()
                self.notification_frame = None
                
            self.visible = False
            
        except Exception as e:
            logging.error(f"Error hiding notification popover: {e}")
            
    def is_click_inside(self, x_root, y_root):
        """Check if a click at screen coordinates (x_root, y_root) is inside the popover."""
        if not self.notification_frame:
            return False
            
        # Get frame bounds in screen coordinates
        frame_x = self.notification_frame.winfo_rootx()
        frame_y = self.notification_frame.winfo_rooty()
        frame_width = self.notification_frame.winfo_width()
        frame_height = self.notification_frame.winfo_height()
        
        # Check if click is within bounds
        return (frame_x <= x_root <= frame_x + frame_width and
                frame_y <= y_root <= frame_y + frame_height)

    def format_notification(self, notification):
        """Format notification dictionary into a readable string."""
        try:
            if isinstance(notification, dict):
                message = notification.get('message', '')
                timestamp = notification.get('timestamp', '')
                level = notification.get('level', '')
                
                # Format based on notification level
                icon = "⚠️ " if level == "warning" else "ℹ️ "
                return f"{icon}{timestamp}\n{message}"
            else:
                return str(notification)
        except Exception as e:
            logging.error(f"Error formatting notification: {e}")
            return str(notification)

    def update_notifications(self):
        """Updates the notification display in the popover."""
        try:
            if not self.notification_list:
                return
                
            # Clear existing notifications
            for widget in self.notification_list.winfo_children():
                widget.destroy()
                
            # Get current notifications from app
            notifications = self.app.notifications if hasattr(self.app, 'notifications') else []
            
            if not notifications:
                # Show "No notifications" message
                no_notif_label = ctk.CTkLabel(
                    self.notification_list,
                    text="No notifications",
                    text_color=("gray60", "gray50")
                )
                no_notif_label.pack(pady=20)
                return
                
            # Create notification widgets with error handling
            for idx, notification in enumerate(notifications):
                try:
                    # Create frame with color based on notification level
                    level = notification.get('level') if isinstance(notification, dict) else ''
                    bg_color = ("gray80", "gray25") if level == "warning" else ("gray90", "gray15")
                    
                    notification_frame = ctk.CTkFrame(
                        self.notification_list,
                        fg_color=bg_color,
                        corner_radius=8
                    )
                    notification_frame.pack(fill="x", padx=5, pady=2)
                    
                    # Create text widget for notification content
                    text = ctk.CTkTextbox(
                        notification_frame,
                        height=50,
                        wrap="word",
                        fg_color="transparent"
                    )
                    text.pack(side="left", fill="x", expand=True, padx=(5, 0))
                    
                    # Format and insert notification content
                    formatted_text = self.format_notification(notification)
                    text.insert("1.0", formatted_text)
                    text.configure(state="disabled")
                    
                    # Add remove button
                    remove_btn = ctk.CTkButton(
                        notification_frame,
                        text="✕",
                        width=30,
                        command=lambda i=idx: self.remove_notification(i),
                        fg_color=("gray70", "gray30"),
                        hover_color=("gray60", "gray40")
                    )
                    remove_btn.pack(side="right", padx=5)
                    
                except Exception as e:
                    logging.error(f"Error creating notification widget: {e}")
                    continue
                    
            # Update immediately
            self.notification_list.update_idletasks()
            
        except Exception as e:
            logging.error(f"Error updating notifications: {e}")

    def remove_notification(self, notification_index):
        """Remove a single notification."""
        try:
            if notification_index < len(self.app.notifications):
                self.app.notifications.pop(notification_index)
                self.update_notifications()
                if hasattr(self.app, 'update_notification_button'):
                    self.app.update_notification_button()
        except Exception as e:
            logging.error("Error removing notification: {}".format(e))
