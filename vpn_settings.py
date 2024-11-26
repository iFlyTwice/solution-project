import os
import subprocess
import json
import logging
from typing import Dict, Optional, Tuple

def get_vpn_settings() -> Dict:
    """
    Get VPN settings from the settings file.
    Returns an empty dict if the file doesn't exist or can't be read.
    """
    try:
        settings_file = os.path.join(os.path.dirname(__file__), "vpn_settings.json")
        if os.path.exists(settings_file):
            with open(settings_file, "r") as f:
                return json.load(f)
        return {}
    except Exception as e:
        logging.error(f"Error reading VPN settings: {e}")
        return {}

# Default Cisco AnyConnect paths
ANYCONNECT_PATHS = [
    r"C:\Program Files (x86)\Cisco\Cisco AnyConnect Secure Mobility Client",
    r"C:\Program Files\Cisco\Cisco AnyConnect Secure Mobility Client"
]

def get_anyconnect_path():
    """Find the Cisco AnyConnect installation directory."""
    for path in ANYCONNECT_PATHS:
        if os.path.exists(path):
            return path
    return None

def launch_anyconnect(vpn_server="iad-f-orca.amazon.com"):
    """
    Launch Cisco AnyConnect and connect to the specified VPN server.
    """
    try:
        anyconnect_dir = get_anyconnect_path()
        if not anyconnect_dir:
            raise FileNotFoundError("Cisco AnyConnect installation not found")

        # Launch the GUI client
        vpnui_path = os.path.join(anyconnect_dir, "vpnui.exe")
        if not os.path.exists(vpnui_path):
            raise FileNotFoundError(f"vpnui.exe not found in {anyconnect_dir}")

        # First try to connect using CLI
        vpncli_path = os.path.join(anyconnect_dir, "vpncli.exe")
        if os.path.exists(vpncli_path):
            try:
                # Try to connect using CLI first
                subprocess.run([vpncli_path, "connect", vpn_server], 
                             check=True, 
                             capture_output=True,
                             timeout=5)
                return True, "VPN connection initiated"
            except subprocess.TimeoutExpired:
                pass  # Timeout is expected as it waits for credentials
            except subprocess.CalledProcessError:
                pass  # Error is expected if needs authentication

        # Launch the GUI as fallback
        subprocess.Popen([vpnui_path])
        return True, "Launched Cisco AnyConnect UI"

    except FileNotFoundError as e:
        return False, f"Error: {str(e)}"
    except Exception as e:
        return False, f"Error launching AnyConnect: {str(e)}"

def get_cisco_anyconnect_status() -> Tuple[bool, str]:
    """
    Check if Cisco AnyConnect is connected.
    Returns a tuple of (is_connected, status_message)
    """
    try:
        anyconnect_dir = get_anyconnect_path()
        if not anyconnect_dir:
            return False, "Cisco AnyConnect not found"

        vpncli_path = os.path.join(anyconnect_dir, "vpncli.exe")
        if not os.path.exists(vpncli_path):
            return False, "vpncli.exe not found"

        # Run vpncli.exe state command and capture output
        result = subprocess.run([vpncli_path, "state"], capture_output=True, text=True)
        output = (result.stdout + result.stderr).lower()
        
        # Simply check if connected
        if "state: connected" in output:
            return True, "Connected"
        elif "state: disconnected" in output:
            return False, "Disconnected"
        elif "state: connecting" in output:
            return False, "Connecting"
        else:
            return False, f"Unknown state: {output.strip()}"

    except Exception as e:
        logging.error(f"Error checking Cisco AnyConnect status: {e}")
        return False, f"Error: {str(e)}"
