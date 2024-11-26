import customtkinter as ctk
import logging
from tkinter import messagebox
import threading
import time
import os
import json
import sys
import hid
import wmi

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')

# Security Key USB identifiers
SECURITY_KEYS = {
    'ZUKEY': {
        'vendor_id': 0x1949,
        'product_id': 0x0429,
        'name': 'Amazon ZUKEY 2',
        'manufacturer': 'Amazon'
    },
    'YUBIKEY': {
        'vendor_id': 0x1050,
        'product_ids': [0x0407, 0x0410, 0x0111, 0x0116, 0x0401, 0x0403, 0x0405, 0x0406, 0x0407, 0x0410],
        'name': 'Yubico YubiKey',
        'manufacturer': 'Yubico'
    }
}

class SecurityKeyManager:
    """Manages security key detection and interaction."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self.device = None
        self.current_key_type = None
        self.last_auth_time = None
        self.wmi = wmi.WMI()

    def detect_security_key(self):
        """Detect if any supported security key is connected."""
        try:
            # Enumerate all HID devices
            for device in hid.enumerate():
                # Check for ZUKEY
                if (device['vendor_id'] == SECURITY_KEYS['ZUKEY']['vendor_id'] and 
                    device['product_id'] == SECURITY_KEYS['ZUKEY']['product_id']):
                    self.current_key_type = 'ZUKEY'
                    return SECURITY_KEYS['ZUKEY']
                
                # Check for YUBIKEY
                if (device['vendor_id'] == SECURITY_KEYS['YUBIKEY']['vendor_id'] and 
                    device['product_id'] in SECURITY_KEYS['YUBIKEY']['product_ids']):
                    self.current_key_type = 'YUBIKEY'
                    return SECURITY_KEYS['YUBIKEY']
            
            self.current_key_type = None
            return None
            
        except Exception as e:
            logging.error(f"Error detecting security key: {e}")
            return None

    def get_device_info(self):
        """Get detailed information about the connected security key."""
        try:
            if not self.current_key_type:
                return None

            key_info = SECURITY_KEYS[self.current_key_type]
            usb_devices = self.wmi.Win32_PnPEntity()

            for device in usb_devices:
                try:
                    if not hasattr(device, 'DeviceID') or not device.DeviceID:
                        continue

                    device_id = device.DeviceID
                    vid_part = device_id.split("VID_")[1]
                    vendor_id = int(vid_part.split("&")[0], 16)
                    pid_part = device_id.split("PID_")[1]
                    product_id = int(pid_part.split("\\")[0], 16)

                    if self.current_key_type == 'ZUKEY':
                        if vendor_id == key_info['vendor_id'] and product_id == key_info['product_id']:
                            return self._format_device_info(device, key_info)
                    elif self.current_key_type == 'YUBIKEY':
                        if vendor_id == key_info['vendor_id'] and product_id in key_info['product_ids']:
                            return self._format_device_info(device, key_info)

                except Exception as e:
                    logging.debug(f"Error parsing device ID: {e}")
                    continue

            return None

        except Exception as e:
            logging.error(f"Error getting device info: {e}")
            return None

    def _format_device_info(self, device, key_info):
        """Format device information into a consistent structure."""
        try:
            serial = getattr(device, 'PNPDeviceID', 'Unknown').split("\\")[-1]
            firmware = getattr(device, 'DeviceID', 'Unknown').split("\\")[-1]
            status = getattr(device, 'Status', 'Connected')

            return {
                'connected': True,
                'serial': serial,
                'firmware': firmware,
                'manufacturer': key_info['manufacturer'],
                'name': key_info['name'],
                'status': status,
                'last_used': self.last_auth_time,
                'vendor_id': f"0x{key_info['vendor_id']:04X}",
                'product_id': (f"0x{key_info['product_id']:04X}" if self.current_key_type == 'ZUKEY' 
                             else f"0x{key_info['product_ids'][0]:04X}")
            }
        except Exception as e:
            logging.error(f"Error formatting device info: {e}")
            return None

    def connect_to_device(self):
        """Establish connection with the security key device."""
        try:
            if not self.current_key_type:
                return False

            key_info = SECURITY_KEYS[self.current_key_type]
            for device in hid.enumerate():
                if self.current_key_type == 'ZUKEY':
                    if (device['vendor_id'] == key_info['vendor_id'] and 
                        device['product_id'] == key_info['product_id']):
                        return self._open_device(device['vendor_id'], device['product_id'])
                elif self.current_key_type == 'YUBIKEY':
                    if (device['vendor_id'] == key_info['vendor_id'] and 
                        device['product_id'] in key_info['product_ids']):
                        return self._open_device(device['vendor_id'], device['product_id'])
            return False

        except Exception as e:
            logging.error(f"Error connecting to device: {e}")
            return False

    def _open_device(self, vendor_id, product_id):
        """Open HID device connection."""
        try:
            if self.device:
                self.device.close()
            
            self.device = hid.device()
            self.device.open(vendor_id, product_id)
            self.device.set_nonblocking(1)
            return True

        except Exception as e:
            logging.error(f"Error opening device: {e}")
            return False

    def close(self):
        """Clean up resources."""
        try:
            if self.device:
                self.device.close()
                self.device = None
            self._stop_event.set()
        except Exception as e:
            logging.error(f"Error closing device: {e}")

def open_manage_window(root):
    """Open the security key management window."""
    try:
        from security_key_gui import SecurityKeyWindow
        window = SecurityKeyWindow(root)
        return window
    except Exception as e:
        logging.error(f"Error opening security key window: {e}")
        messagebox.showerror("Error", f"Failed to open security key manager: {e}")
        return None
