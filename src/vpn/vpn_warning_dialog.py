import customtkinter as ctk
import logging

class VPNWarningDialog:
    def __init__(self, parent=None):
        self.result = False
        
        # Create dialog window
        if parent:
            self.window = ctk.CTkToplevel(parent)
        else:
            self.window = ctk.CTk()
            
        self.window.title("VPN Warning")
        self.window.geometry("400x200")
        self.window.resizable(False, False)
        
        # Make it modal if it has a parent
        if parent:
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
            text="No, Connect VPN",
            command=self.on_no,
            width=120
        )
        self.no_button.pack(side="left", padx=10)
        
        # Wait for window
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.window.bind("<Escape>", lambda e: self.on_close())
        
        # Center on parent if exists
        if parent:
            self.window.geometry(f"+{parent.winfo_x() + 50}+{parent.winfo_y() + 50}")
        
        self.window.mainloop()
    
    def on_yes(self):
        """User clicked Yes"""
        self.result = True
        self.window.quit()
        self.window.destroy()
    
    def on_no(self):
        """User clicked No"""
        self.result = False
        self.window.quit()
        self.window.destroy()
    
    def on_close(self):
        """Window was closed"""
        self.result = False
        self.window.quit()
        self.window.destroy()

def show_vpn_warning(parent=None) -> bool:
    """
    Show VPN warning dialog and return True if user wants to continue
    """
    try:
        dialog = VPNWarningDialog(parent)
        return dialog.result
    except Exception as e:
        logging.error(f"Error showing VPN warning: {e}")
        return False
