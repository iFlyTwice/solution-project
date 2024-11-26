import customtkinter as ctk
import logging

class VPNWarningDialog:
    def __init__(self, parent):
        self.parent = parent
        self.result = False
        
        # Create dialog window
        self.window = ctk.CTkToplevel(parent)
        self.window.title("VPN Warning")
        self.window.geometry("400x200")
        self.window.resizable(False, False)
        
        # Make it modal
        self.window.transient(parent)
        self.window.grab_set()
        
        # Center the window
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Warning message
        self.message = ctk.CTkLabel(
            self.window,
            text="Warning: VPN is not connected!\n\nThe application may not function correctly\nwithout a VPN connection.\n\nDo you want to continue anyway?",
            font=("Segoe UI", 12),
            wraplength=350,
            justify="center"
        )
        self.message.pack(pady=20)
        
        # Buttons frame
        self.button_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        self.button_frame.pack(pady=10)
        
        # Yes button
        self.yes_button = ctk.CTkButton(
            self.button_frame,
            text="Yes, Continue",
            command=self.on_yes,
            width=120
        )
        self.yes_button.pack(side="left", padx=10)
        
        # No button
        self.no_button = ctk.CTkButton(
            self.button_frame,
            text="No, Cancel",
            command=self.on_no,
            width=120
        )
        self.no_button.pack(side="left", padx=10)
        
        # Set focus to No button as safer default
        self.no_button.focus_set()
        
        # Wait for user response
        self.window.wait_window()
    
    def on_yes(self):
        """User clicked Yes"""
        self.result = True
        self.window.destroy()
    
    def on_no(self):
        """User clicked No"""
        self.result = False
        self.window.destroy()

def show_vpn_warning(parent):
    """Show VPN warning dialog and return True if user wants to continue"""
    try:
        dialog = VPNWarningDialog(parent)
        return dialog.result
    except Exception as e:
        logging.error(f"Error showing VPN warning dialog: {e}")
        return False
