import customtkinter as ctk
import logging
from tkinter import messagebox
import threading
import time
import os
import json
from datetime import datetime

class SecurityKeyWindow:
    """GUI window for security key management."""
    
    def __init__(self, root):
        """Initialize the security key management window."""
        try:
            logging.info("Starting SecurityKeyWindow initialization...")
            
            # Store root reference and validate
            if not root or not hasattr(root, 'winfo_exists') or not root.winfo_exists():
                raise ValueError("Invalid root window")
            self.root = root
            
            # Initialize state before creating window
            self._stop_event = threading.Event()
            self._lock = threading.Lock()
            self.monitor_thread = None
            self.device_info_labels = {}
            self.window = None
            
            # Create manager instance
            from manage_zukey import SecurityKeyManager
            self.key_manager = SecurityKeyManager()
            
            # Create window in the main thread using after
            self.root.after(0, self._create_window)
            
        except Exception as e:
            logging.error(f"Failed to initialize security key window: {e}")
            raise

    def _create_window(self):
        """Create the window and set up UI in the main thread."""
        try:
            # Create window
            self.window = ctk.CTkToplevel(self.root)
            self.window.title("Security Key Manager")
            self.window.geometry("800x600")
            self.window.transient(self.root)
            self.window.grab_set()
            
            # Set up UI
            self._setup_ui()
            
            # Start monitoring in separate thread
            self._start_monitoring()
            
            # Bind events
            self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            logging.info("SecurityKeyWindow initialization complete")
            
        except Exception as e:
            logging.error(f"Failed to create window: {e}")
            if self.window:
                try:
                    self.window.destroy()
                except:
                    pass
            raise
    
    def _setup_ui(self):
        """Set up the UI components."""
        try:
            # Create notebook for tabs
            self.notebook = ctk.CTkTabview(self.window)
            self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Create tabs
            self.status_tab = self.notebook.add("Status")
            self.operations_tab = self.notebook.add("Operations")
            
            # Set up status tab
            self._setup_status_tab()
            
            # Set up operations tab
            self._setup_operations_tab()
            
            # Add status bar
            self.status_bar = ctk.CTkLabel(self.window, text="Ready", anchor="w")
            self.status_bar.pack(fill="x", padx=10, pady=5)
            
        except Exception as e:
            logging.error(f"Error setting up UI: {e}")
            raise
    
    def _setup_status_tab(self):
        """Set up the status tab content."""
        try:
            # Create frame for device info
            info_frame = ctk.CTkFrame(self.status_tab)
            info_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Add device info labels
            labels = [
                "Status", "Name", "Manufacturer", "Serial",
                "Firmware", "Vendor ID", "Product ID", "Last Used"
            ]
            
            for i, label in enumerate(labels):
                title = ctk.CTkLabel(info_frame, text=f"{label}:", anchor="w")
                title.grid(row=i, column=0, padx=5, pady=2, sticky="w")
                
                value = ctk.CTkLabel(info_frame, text="Not connected", anchor="w")
                value.grid(row=i, column=1, padx=5, pady=2, sticky="w")
                
                self.device_info_labels[label.lower()] = value
            
            # Configure grid
            info_frame.grid_columnconfigure(1, weight=1)
            
        except Exception as e:
            logging.error(f"Error setting up status tab: {e}")
            raise
    
    def _setup_operations_tab(self):
        """Set up the operations tab content."""
        try:
            # Create frame for operations
            ops_frame = ctk.CTkFrame(self.operations_tab)
            ops_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Add operation buttons
            self.verify_button = ctk.CTkButton(
                ops_frame, 
                text="Verify Security Key",
                command=self._verify_key
            )
            self.verify_button.pack(pady=5)
            
            self.test_button = ctk.CTkButton(
                ops_frame,
                text="Test Connection",
                command=self._test_connection
            )
            self.test_button.pack(pady=5)
            
        except Exception as e:
            logging.error(f"Error setting up operations tab: {e}")
            raise
    
    def _start_monitoring(self):
        """Start the security key monitoring thread."""
        try:
            if not self._stop_event.is_set():
                self.monitor_thread = threading.Thread(
                    target=self._monitor_loop,
                    daemon=True
                )
                self.monitor_thread.start()
                
        except Exception as e:
            logging.error(f"Error starting monitoring: {e}")
            self.update_status(f"Failed to start monitoring: {e}", "error")
    
    def _monitor_loop(self):
        """Monitor security key status."""
        try:
            while not self._stop_event.is_set():
                try:
                    # Check if window still exists
                    if not self.window.winfo_exists():
                        break
                    
                    # Detect security key
                    key_info = self.key_manager.detect_security_key()
                    if key_info:
                        device_info = self.key_manager.get_device_info()
                        if device_info:
                            self.update_ui(self._update_device_info, device_info)
                        else:
                            self.update_ui(self._clear_device_info)
                    else:
                        self.update_ui(self._clear_device_info)
                    
                    # Sleep with interruption checks
                    for _ in range(10):  # Check every 0.1 seconds
                        if self._stop_event.is_set():
                            return
                        time.sleep(0.1)
                        
                except Exception as e:
                    logging.error(f"Error in monitor loop: {e}")
                    if self._stop_event.is_set():
                        return
                    time.sleep(1)
                    
        except Exception as e:
            logging.error(f"Monitor thread error: {e}")
        finally:
            logging.info("Monitor thread stopping")
    
    def update_ui(self, func, *args, **kwargs):
        """Schedule UI updates to run in the main thread."""
        if self.window and self.window.winfo_exists():
            self.window.after(0, func, *args, **kwargs)
    
    def _update_device_info(self, info):
        """Update device information display."""
        try:
            if not self.window.winfo_exists():
                return
                
            # Update labels
            self.device_info_labels['status'].configure(text=info['status'])
            self.device_info_labels['name'].configure(text=info['name'])
            self.device_info_labels['manufacturer'].configure(text=info['manufacturer'])
            self.device_info_labels['serial'].configure(text=info['serial'])
            self.device_info_labels['firmware'].configure(text=info['firmware'])
            self.device_info_labels['vendor id'].configure(text=info['vendor_id'])
            self.device_info_labels['product id'].configure(text=info['product_id'])
            
            last_used = info['last_used']
            if last_used:
                last_used_str = last_used.strftime("%Y-%m-%d %H:%M:%S")
            else:
                last_used_str = "Never"
            self.device_info_labels['last used'].configure(text=last_used_str)
            
            # Update status
            self.update_status("Security key connected")
            
        except Exception as e:
            logging.error(f"Error updating device info: {e}")
    
    def _clear_device_info(self):
        """Clear device information display."""
        try:
            if not self.window.winfo_exists():
                return
                
            for label in self.device_info_labels.values():
                label.configure(text="Not connected")
            
            self.update_status("No security key detected", "warning")
            
        except Exception as e:
            logging.error(f"Error clearing device info: {e}")
    
    def _verify_key(self):
        """Verify security key operation."""
        try:
            if not self.key_manager.current_key_type:
                messagebox.showwarning("Warning", "No security key detected")
                return
                
            if self.key_manager.connect_to_device():
                messagebox.showinfo("Success", "Security key verified successfully")
            else:
                messagebox.showerror("Error", "Failed to verify security key")
                
        except Exception as e:
            logging.error(f"Error verifying key: {e}")
            messagebox.showerror("Error", f"Failed to verify key: {e}")
    
    def _test_connection(self):
        """Test security key connection."""
        try:
            if not self.key_manager.current_key_type:
                messagebox.showwarning("Warning", "No security key detected")
                return
                
            if self.key_manager.connect_to_device():
                self.key_manager.last_auth_time = datetime.now()
                messagebox.showinfo("Success", "Connection test successful")
            else:
                messagebox.showerror("Error", "Connection test failed")
                
        except Exception as e:
            logging.error(f"Error testing connection: {e}")
            messagebox.showerror("Error", f"Connection test failed: {e}")
    
    def update_status(self, message, status_type="info"):
        """Update the status bar message."""
        try:
            if not self.window.winfo_exists():
                return
                
            color = {
                "info": "gray",
                "warning": "orange",
                "error": "red"
            }.get(status_type, "gray")
            
            self.status_bar.configure(text=message, text_color=color)
            
        except Exception as e:
            logging.error(f"Error updating status: {e}")
    
    def on_closing(self):
        """Handle window closing."""
        try:
            logging.info("Closing security key window")
            
            # Stop monitoring
            self._stop_event.set()
            
            if self.monitor_thread and self.monitor_thread.is_alive():
                logging.info("Waiting for monitor thread...")
                self.monitor_thread.join(timeout=1.0)
            
            # Close manager
            if hasattr(self, 'key_manager'):
                self.key_manager.close()
            
            # Destroy window
            if hasattr(self, 'window') and self.window:
                try:
                    self.window.grab_release()
                    self.window.destroy()
                except:
                    pass
                
        except Exception as e:
            logging.error(f"Error closing window: {e}")
            # Force destroy
            if hasattr(self, 'window') and self.window:
                try:
                    self.window.destroy()
                except:
                    pass
