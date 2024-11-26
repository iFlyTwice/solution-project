import json
import os
import platform
import subprocess
from pathlib import Path
import logging
import webbrowser


def load_vpn_settings():
    """
    Load VPN settings from a configuration file.
    """
    settings_path = Path.home() / ".vpn_settings.json"
    if not settings_path.exists():
        print("VPN settings file not found.")
        return {}
    try:
        with settings_path.open('r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("Error: VPN settings file is corrupt. Please fix the file.")
        return {}


# Default Cisco AnyConnect installation paths
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


# Default Cisco AnyConnect installation paths
ANYCONNECT_PATHS = [
    r"C:\Program Files (x86)\Cisco\Cisco AnyConnect Secure Mobility Client\vpncli.exe",
    r"C:\Program Files\Cisco\Cisco AnyConnect Secure Mobility Client\vpncli.exe"
]

def get_vpncli_path():
    """
    Find the vpncli executable in common installation paths.
    """
    for path in ANYCONNECT_PATHS:
        if os.path.exists(path):
            return path
    return None


def get_cisco_anyconnect_status():
    """
    Retrieve the VPN connection status from Cisco AnyConnect.
    Specifically checks for Amazon IAD Orca VPN connection.
    """
    vpncli = get_vpncli_path()
    if not vpncli:
        return "Cisco AnyConnect VPN client is not installed or vpncli.exe not found"

    try:
        # Use full path to vpncli.exe
        result = subprocess.run(
            [vpncli, "state"],  # Changed from stat to state for more detailed output
            capture_output=True,
            text=True,
            timeout=5
        )
        
        output = result.stdout.strip() if result.stdout else result.stderr.strip()
        
        # Log the complete output for debugging
        logging.info(f"VPN CLI Output: {output}")
        
        # Check various connection states
        if result.returncode == 0:
            output_lower = output.lower()
            
            # More detailed connection state checking
            if "connected" in output_lower:
                if "iad-f-orca" in output_lower or "amazon" in output_lower:
                    return "Connected to Amazon IAD Orca VPN"
                else:
                    return f"Connected to VPN but possibly wrong endpoint. Current connection: {output}"
            elif "disconnected" in output_lower:
                return "Not connected to VPN"
            else:
                return f"Unexpected VPN state: {output}"
        else:
            return f"Failed to get VPN status: {output}"
            
    except subprocess.TimeoutExpired:
        return "Cisco AnyConnect command timed out"
    except Exception as e:
        logging.error(f"Error checking VPN status: {str(e)}")
        return f"Error retrieving Cisco AnyConnect status: {str(e)}"


def launch_vpn_auth():
    """
    Launch the Cisco AnyConnect authentication page for IAD Orca.
    """
    try:
        webbrowser.open("https://iad-f-orca.amazon.com")
        return True
    except Exception as e:
        logging.error(f"Failed to launch VPN authentication: {e}")
        return False


def get_connected_vpn():
    """
    Retrieve the current VPN connection details based on the OS.
    """
    current_os = platform.system()

    if current_os == "Linux":
        try:
            result = subprocess.run(["nmcli", "con", "show", "--active"], capture_output=True, text=True)
            active_connections = result.stdout.splitlines()
            vpn_connections = [line for line in active_connections if "vpn" in line.lower()]
            return vpn_connections[0] if vpn_connections else None
        except Exception as e:
            print(f"Error retrieving VPN details on Linux: {e}")
            return None

    elif current_os == "Windows":
        try:
            # First, check if Cisco AnyConnect is active
            cisco_status = get_cisco_anyconnect_status()
            if "Connected" in cisco_status:
                return cisco_status

            # If Cisco AnyConnect is not active, fallback to checking using PowerShell
            result = subprocess.run(["powershell", "-Command", "Get-VpnConnection"], capture_output=True, text=True)
            if "Name" in result.stdout:
                return result.stdout.strip()
            return None
        except Exception as e:
            print(f"Error retrieving VPN details on Windows: {e}")
            return None

    elif current_os == "Darwin":
        try:
            result = subprocess.run(["scutil", "--nc", "list"], capture_output=True, text=True)
            active_connections = result.stdout.splitlines()
            vpn_connections = [line for line in active_connections if "Connected" in line]
            return vpn_connections[0] if vpn_connections else None
        except Exception as e:
            print(f"Error retrieving VPN details on macOS: {e}")
            return None
    else:
        print(f"Unsupported operating system: {current_os}")
        return None


def show_vpn_settings():
    """
    Display VPN settings for the current VPN connection.
    """
    vpn_settings = load_vpn_settings()
    current_vpn = get_connected_vpn()

    print("Your VPN Settings:")
    if vpn_settings:
        for key, value in vpn_settings.items():
            print(f"{key}: {value}")

    if current_vpn:
        print("\nActive VPN Connection Details:")
        print(current_vpn)
    else:
        print("\nNo active VPN connection detected.")


if __name__ == "__main__":
    show_vpn_settings()
