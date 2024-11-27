import logging
import threading
import time
import os
import winreg
import subprocess
from .vpn_settings import get_cisco_anyconnect_status, connect_to_vpn_with_fallback

class VPNManager:
    def __init__(self):
        self.connected = False
        self.vpn_endpoint = "iad-f-orca.amazon.com"
        self.vpnui_path = self._find_vpnui()
        self._stop_monitor = False
        self._monitor_lock = threading.Lock()
        self._stop_event = threading.Event()
        self.monitor_thread = None
        self.status_callback = None
        
        # Start monitoring thread
        self._start_status_monitor()
        
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

    def connect(self):
        """Connect to VPN using the most reliable method"""
        try:
            if not self.vpnui_path:
                logging.error("VPN UI executable not found")
                return False
                
            # First check if we're already connected
            if self.check_status():
                logging.info("Already connected to VPN")
                return True
                
            # Use the improved connection method from vpn_settings
            success, message = connect_to_vpn_with_fallback(self.vpn_endpoint)
            if success:
                logging.info(f"VPN connection successful: {message}")
                return True
            else:
                logging.error(f"VPN connection failed: {message}")
                return False
                
        except Exception as e:
            logging.error(f"Failed to connect: {e}")
            return False
            
    def disconnect(self):
        """Disconnect from VPN using CLI"""
        try:
            if not self.vpnui_path:
                logging.error("VPN UI executable not found")
                return False
                
            # Check if already disconnected
            if not self.check_status():
                logging.info("Already disconnected")
                return True
                
            # Use CLI disconnect (most reliable method)
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
        """Check VPN connection status"""
        try:
            # Use the improved status check from vpn_settings
            is_connected, _ = get_cisco_anyconnect_status()
            
            # Only log status changes to avoid spam
            if is_connected != self.connected:
                logging.info(f"VPN connection status changed: {'Connected' if is_connected else 'Disconnected'}")
                self.connected = is_connected
                
            return is_connected
                
        except Exception as e:
            logging.debug(f"Failed to check VPN status: {e}")
            return self.connected

    def set_status_callback(self, callback):
        """Set callback for status updates"""
        self.status_callback = callback
        # Trigger initial status update
        if callback:
            callback(self.check_status())

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
