import customtkinter as ctk
import subprocess
import threading
import logging
import winreg
import json
import time
import os
import sys
import keyboard
import pygetwindow as gw
import uiautomation as auto
from enum import Enum
from Core import QuickLinksApp
from tkinter import messagebox

class VPNState(Enum):
    DISCONNECTED = "Disconnected"
    CONNECTING = "Connecting..."
    CONNECTED = "Connected"
    DISCONNECTING = "Disconnecting..."
    ERROR = "Error"

class VPNManager:
    def __init__(self):
        self.connected = False
        self.state = VPNState.DISCONNECTED
        self.vpn_endpoint = "iad-f-orca.amazon.com"
        self.vpnui_path = self._find_vpnui()
        self._stop_monitor = False
        self._monitor_lock = threading.Lock()
        self._stop_event = threading.Event()
        self.monitor_thread = None
        self.status_callback = None
        
    def _find_vpnui(self):
        """Find the vpnui executable path"""
        possible_paths = [
            r"C:\Program Files (x86)\Cisco\Cisco AnyConnect Secure Mobility Client\vpnui.exe",
            r"C:\Program Files\Cisco\Cisco AnyConnect Secure Mobility Client\vpnui.exe"
        ]
        
        # Also try to find from registry
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Cisco\Cisco AnyConnect Secure Mobility Client")
            install_path = winreg.QueryValueEx(key, "InstallPath")[0]
            possible_paths.append(os.path.join(install_path, "vpnui.exe"))
        except Exception as e:
            logging.warning(f"Could not find VPN path in registry: {e}")
        
        for path in possible_paths:
            if os.path.exists(path):
                logging.info(f"Found vpnui at: {path}")
                return path
                
        logging.error("Could not find vpnui executable")
        return None
        
    def _find_vpn_profile(self):
        """Find the VPN profile name from the preferences file"""
        try:
            preferences_path = os.path.expandvars(
                r"%LOCALAPPDATA%\Cisco\Cisco AnyConnect Secure Mobility Client\preferences.xml"
            )
            if os.path.exists(preferences_path):
                with open(preferences_path, 'r') as f:
                    content = f.read()
                    if self.vpn_endpoint in content:
                        # Try to extract profile name
                        import xml.etree.ElementTree as ET
                        root = ET.fromstring(content)
                        for profile in root.findall(".//Profile"):
                            if self.vpn_endpoint in str(profile.text):
                                self.vpn_profile = profile.text.strip()
                                logging.info(f"Found VPN profile: {self.vpn_profile}")
                                return
        except Exception as e:
            logging.warning(f"Could not find VPN profile: {e}")
            
    def _find_vpn_window(self, timeout=5):
        """Find the VPN window using UI Automation"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Try to find the VPN window
            window = auto.WindowControl(searchDepth=1, Name='Cisco AnyConnect Secure Mobility Client')
            if window.Exists(0):
                return window
            time.sleep(0.5)
        return None
        
    def _ensure_vpn_window(self):
        """Make sure VPN window is open and ready"""
        # First check if window already exists
        window = self._find_vpn_window(timeout=1)
        if not window:
            # Kill any existing processes
            subprocess.run(['taskkill', '/F', '/IM', 'vpnui.exe'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
            time.sleep(1)
            
            # Launch VPN UI
            subprocess.Popen([self.vpnui_path], creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Wait for window
            window = self._find_vpn_window()
            
        if window:
            window.SetFocus()
            time.sleep(0.5)
            return window
        return None
        
    def connect(self):
        """Connect to VPN using CLI first, fallback to UI if needed"""
        try:
            if not self.vpnui_path:
                logging.error("VPN UI executable not found")
                return False
                
            # First check if we're already connected
            if self.check_status():
                logging.info("Already connected to VPN")
                return True
                
            # Kill any existing VPN processes that might interfere
            self._cleanup_vpn_processes()
            time.sleep(1)  # Give processes time to clean up
                
            # Try CLI connect first (most headless method)
            vpncli_path = self.vpnui_path.replace('vpnui.exe', 'vpncli.exe')
            if os.path.exists(vpncli_path):
                try:
                    logging.info("Attempting CLI connect")
                    # Run connect command with a timeout
                    result = subprocess.run(
                        [vpncli_path, 'connect', self.vpn_endpoint],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    # Check for specific error messages in the output
                    if "error: Connect not available" in result.stdout:
                        logging.warning("Connection blocked by another AnyConnect process")
                        self._cleanup_vpn_processes()
                        time.sleep(1)
                        # Retry connection once
                        result = subprocess.run(
                            [vpncli_path, 'connect', self.vpn_endpoint],
                            capture_output=True,
                            text=True,
                            timeout=10,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                    
                    # Give it a moment to connect
                    time.sleep(2)
                    if self.check_status():
                        logging.info("Successfully connected via CLI")
                        return True
                        
                except subprocess.TimeoutExpired:
                    logging.warning("CLI connect timed out")
                except Exception as e:
                    logging.warning(f"CLI connect failed: {e}")
            
            # If CLI fails, try UI method
            return self._connect_via_ui()
            
        except Exception as e:
            logging.error(f"Failed to connect: {e}")
            return False
            
    def _cleanup_vpn_processes(self):
        """Clean up any existing VPN processes"""
        try:
            # Kill vpnui.exe
            subprocess.run(['taskkill', '/F', '/IM', 'vpnui.exe'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL,
                         creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Kill vpncli.exe
            subprocess.run(['taskkill', '/F', '/IM', 'vpncli.exe'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL,
                         creationflags=subprocess.CREATE_NO_WINDOW)
                         
            logging.info("Cleaned up existing VPN processes")
        except Exception as e:
            logging.warning(f"Error cleaning up VPN processes: {e}")
            
    def _connect_via_ui(self):
        """Connect using the UI method"""
        try:
            # Kill any existing vpnui processes quietly
            self._cleanup_vpn_processes()
            time.sleep(0.5)
            
            # Launch VPN UI minimized
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 6  # SW_MINIMIZE
            
            subprocess.Popen([self.vpnui_path], 
                           startupinfo=startupinfo,
                           creationflags=subprocess.CREATE_NO_WINDOW)
            time.sleep(1)
            
            # Type endpoint and connect
            keyboard.write(self.vpn_endpoint)
            time.sleep(0.2)
            keyboard.press_and_release('enter')
            
            logging.info("Connection initiated via UI")
            return True
            
        except Exception as e:
            logging.error(f"Failed to connect via UI: {e}")
            return False
            
    def disconnect(self):
        """Disconnect from VPN using CLI only"""
        try:
            if not self.vpnui_path:
                logging.error("VPN UI executable not found")
                return False
                
            # Check if already disconnected
            if not self.check_status():
                logging.info("Already disconnected")
                return True
                
            # Use CLI disconnect only (most headless method)
            vpncli_path = self.vpnui_path.replace('vpnui.exe', 'vpncli.exe')
            if os.path.exists(vpncli_path):
                try:
                    logging.info("Attempting CLI disconnect")
                    result = subprocess.run(
                        [vpncli_path, 'disconnect'],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    # Give it a moment
                    time.sleep(2)
                    if not self.check_status():
                        logging.info("Successfully disconnected via CLI")
                        return True
                        
                except subprocess.TimeoutExpired:
                    logging.warning("CLI disconnect timed out")
                except Exception as e:
                    logging.warning(f"CLI disconnect failed: {e}")
                    
            # If CLI fails, try to kill the VPN UI process
            subprocess.run(['taskkill', '/F', '/IM', 'vpnui.exe'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL,
                         creationflags=subprocess.CREATE_NO_WINDOW)
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to disconnect: {e}")
            return False
            
    def check_status(self):
        """Check VPN connection status using vpncli silently"""
        try:
            if not self.vpnui_path:
                return False
                
            vpncli_path = self.vpnui_path.replace('vpnui.exe', 'vpncli.exe')
            if not os.path.exists(vpncli_path):
                return False
                
            try:
                result = subprocess.run(
                    [vpncli_path, 'state'],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                output = result.stdout.lower()
                is_connected = (
                    "state: connected" in output or
                    "vpn state: connected" in output or
                    "connection status: connected" in output
                )
                
                # Only log status changes to avoid spam
                if is_connected != self.connected:
                    logging.info(f"VPN connection status changed: {'Connected' if is_connected else 'Disconnected'}")
                
                return is_connected
                
            except subprocess.TimeoutExpired:
                return self.connected  # Keep previous state on timeout
            except Exception as e:
                logging.debug(f"Failed to check VPN status: {e}")
                return self.connected
                
        except Exception as e:
            logging.debug(f"Failed to check VPN status: {e}")
            return self.connected

    def set_status_callback(self, callback):
        """Set callback for status updates"""
        self.status_callback = callback

    def _start_status_monitor(self):
        """Start the status monitoring thread"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            logging.warning("VPN monitor thread already running")
            return
            
        self._stop_event.clear()
        self.monitor_thread = threading.Thread(target=self._status_monitor, daemon=True)
        self.monitor_thread.start()
        logging.info("VPN monitoring thread started")

    def _status_monitor(self):
        """Monitor VPN connection status"""
        try:
            while not self._stop_event.is_set() and not self._stop_monitor:
                with self._monitor_lock:
                    status = self.check_status()
                    if self.status_callback:
                        self.status_callback(status)
                time.sleep(2)  # Check every 2 seconds
        except Exception as e:
            logging.error(f"Error in VPN status monitor: {e}")
        finally:
            logging.info("VPN monitor thread stopping")

    def stop(self):
        """Stop the status monitor"""
        logging.info("Stopping VPN monitor...")
        self._stop_monitor = True
        self._stop_event.set()
        
        if hasattr(self, 'monitor_thread') and self.monitor_thread:
            try:
                self.monitor_thread.join(timeout=2)
                if self.monitor_thread.is_alive():
                    logging.warning("VPN monitor thread did not stop cleanly")
            except Exception as e:
                logging.error(f"Error stopping VPN monitor: {e}")
        
        logging.info("VPN monitor stopped")
        
class VPNGUI:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("Amazon VPN Manager")
        self.window.geometry("400x300")
        self.window.lift()  # Lift window to top
        self.window.attributes('-topmost', True)  # Keep on top
        self.window.after_idle(self.window.attributes, '-topmost', False)  # Allow it to go back
        
        # Register for Windows messages
        if sys.platform == 'win32':
            self.window.bind('<WM_QUERYENDSESSION>', self._handle_system_shutdown)
            self.window.protocol("WM_DELETE_WINDOW", self._handle_window_close)
        
        # Configure grid
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(2, weight=1)
        
        # Status label with larger font
        self.status_label = ctk.CTkLabel(
            self.window, 
            text="Checking Status...",
            font=("Arial", 16, "bold")
        )
        self.status_label.grid(row=0, column=0, pady=20, sticky="ew")
        
        # Endpoint label
        self.endpoint_label = ctk.CTkLabel(
            self.window,
            text="iad-f-orca.amazon.com",
            font=("Arial", 12)
        )
        self.endpoint_label.grid(row=1, column=0, pady=10, sticky="ew")
        
        # Button frame
        self.button_frame = ctk.CTkFrame(self.window)
        self.button_frame.grid(row=2, column=0, padx=20, pady=20, sticky="ew")
        self.button_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Connect button
        self.connect_button = ctk.CTkButton(
            self.button_frame,
            text="Connect",
            command=self.connect,
            font=("Arial", 12, "bold")
        )
        self.connect_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        # Disconnect button
        self.disconnect_button = ctk.CTkButton(
            self.button_frame,
            text="Disconnect",
            command=self.disconnect,
            font=("Arial", 12, "bold"),
            state="disabled"
        )
        self.disconnect_button.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # Initialize VPN manager
        self.vpn = VPNManager()
        self.vpn.set_status_callback(self.update_status)
        
        # Update initial status
        self.update_status(self.vpn.check_status())
        
    def update_status(self, is_connected):
        """Update UI based on connection status"""
        if is_connected:
            self.vpn.state = VPNState.CONNECTED
            self.status_label.configure(
                text=self.vpn.state.value,
                text_color="green"
            )
            self.connect_button.configure(state="disabled")
            self.disconnect_button.configure(state="normal")
            
            # Launch quick links dashboard and close VPN window
            self.window.after(1000, self._launch_dashboard)
        else:
            if self.vpn.state != VPNState.CONNECTING and self.vpn.state != VPNState.DISCONNECTING:
                self.vpn.state = VPNState.DISCONNECTED
                self.status_label.configure(
                    text=self.vpn.state.value,
                    text_color="red"
                )
                self.connect_button.configure(state="normal")
                self.disconnect_button.configure(state="disabled")
            
    def _launch_dashboard(self):
        """Launch the quick links dashboard and close VPN window"""
        try:
            # Wait a moment to ensure VPN is fully connected
            time.sleep(2)
            
            # Double check VPN connection before launching dashboard
            if not self.vpn.check_status():
                logging.warning("VPN not connected, delaying dashboard launch")
                # Retry after 2 seconds
                self.window.after(2000, self._launch_dashboard)
                return
                
            logging.info("VPN connected, launching dashboard...")
            
            # Create root window for dashboard
            root = ctk.CTk()
            
            # Configure root window
            root.title("Quick Links Dashboard")
            root.geometry("800x600")  # Set a default size
            root.lift()  # Bring to front
            
            try:
                # Initialize dashboard
                dashboard = QuickLinksApp(root)
                
                # Close VPN window
                self.window.withdraw()  # Hide instead of destroy
                
                # Start dashboard main loop
                root.mainloop()
                
                # If dashboard closes, also close VPN window
                self.window.destroy()
                
            except Exception as e:
                logging.error(f"Dashboard initialization failed: {e}")
                self.window.deiconify()  # Show VPN window again if dashboard fails
                messagebox.showerror("Error", "Failed to launch dashboard. Please try again.")
                
        except Exception as e:
            logging.error(f"Failed to launch dashboard: {e}")
            messagebox.showerror("Error", "Failed to launch dashboard. Please try again.")
        
    def _handle_system_shutdown(self, event=None):
        """Handle system shutdown/restart events"""
        try:
            logging.info("System shutdown detected - cleaning up...")
            # Disconnect VPN if connected to avoid connection issues on next startup
            if self.vpn.check_status():
                self.vpn.disconnect()
            # Clean up monitoring thread
            self.vpn.stop()
            # Allow system to continue shutdown
            self.window.quit()
            return True
        except Exception as e:
            logging.error(f"Error during shutdown cleanup: {e}")
            return False
            
    def _handle_window_close(self):
        """Handle window close button click"""
        try:
            if self.vpn.check_status():
                if messagebox.askyesno("Confirm Exit", 
                    "VPN is still connected. Disconnect and exit?"):
                    self.vpn.disconnect()
                else:
                    return
            self.vpn.stop()
            self.window.quit()
        except Exception as e:
            logging.error(f"Error during window close: {e}")
            self.window.quit()
        
    def connect(self):
        """Handle connect button click"""
        try:
            self.vpn.state = VPNState.CONNECTING
            self.status_label.configure(text=self.vpn.state.value, text_color="orange")
            self.connect_button.configure(state="disabled")
            self.window.update()
            
            if not os.path.exists(self.vpn.vpnui_path):
                self.vpn.state = VPNState.ERROR
                self.status_label.configure(text=self.vpn.state.value, text_color="red")
                self.connect_button.configure(state="normal")
                logging.error("Cisco AnyConnect client not found")
                return
                
            if self.vpn.connect():
                logging.info("Connection initiated")
            else:
                self.vpn.state = VPNState.ERROR
                self.status_label.configure(text=self.vpn.state.value, text_color="red")
                self.connect_button.configure(state="normal")
        except PermissionError:
            self.vpn.state = VPNState.ERROR
            self.status_label.configure(text=self.vpn.state.value, text_color="red")
            self.connect_button.configure(state="normal")
            logging.error("Permission denied when connecting to VPN")
        except Exception as e:
            self.vpn.state = VPNState.ERROR
            self.status_label.configure(text=self.vpn.state.value, text_color="red")
            self.connect_button.configure(state="normal")
            logging.error(f"VPN connection error: {e}")
        
    def disconnect(self):
        """Handle disconnect button click"""
        self.vpn.state = VPNState.DISCONNECTING
        self.status_label.configure(text=self.vpn.state.value, text_color="orange")
        self.disconnect_button.configure(state="disabled")
        self.window.update()
        
        if self.vpn.disconnect():
            logging.info("Disconnect initiated")
        else:
            self.vpn.state = VPNState.ERROR
            self.status_label.configure(text=self.vpn.state.value, text_color="red")
            self.disconnect_button.configure(state="normal")
        
    def run(self):
        """Start the GUI"""
        self.window.mainloop()
        self.vpn.stop()  # Clean up monitoring thread

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Set CustomTkinter appearance
    ctk.set_appearance_mode("dark")  # Options: "dark", "light"
    ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"
    
    # Create and run GUI
    gui = VPNGUI()
    gui.run()