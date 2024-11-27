import json
import os
import platform
import subprocess
from pathlib import Path
import logging
import webbrowser
from typing import Dict, Optional, Tuple
import time
import pyautogui
import pywinauto
from pywinauto import Application, timings
from pywinauto.findwindows import ElementNotFoundError
import win32com.client
import pythoncom

def get_vpn_settings() -> Dict:
    """
    Get VPN settings from the settings file.
    Returns an empty dict if the file doesn't exist or can't be read.
    """
    try:
        # First try the home directory
        settings_path = Path.home() / ".vpn_settings.json"
        if settings_path.exists():
            with settings_path.open('r') as f:
                return json.load(f)
        
        # Then try the local directory
        settings_file = os.path.join(os.path.dirname(__file__), "vpn_settings.json")
        if os.path.exists(settings_file):
            with open(settings_file, "r") as f:
                return json.load(f)
        return {}
    except Exception as e:
        logging.error(f"Error reading VPN settings: {e}")
        return {}

def get_vpn_server() -> str:
    """
    Get the configured VPN server from settings.
    Returns the default server if not configured.
    """
    try:
        settings = get_vpn_settings()
        return settings.get('vpn_server', 'iad-f-orca.amazon.com')
    except Exception as e:
        logging.error(f"Error getting VPN server: {e}")
        return 'iad-f-orca.amazon.com'

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

def get_vpncli_path():
    """Get the path to vpncli.exe."""
    possible_paths = [
        r"C:\Program Files (x86)\Cisco\Cisco AnyConnect Secure Mobility Client\vpncli.exe",
        r"C:\Program Files\Cisco\Cisco AnyConnect Secure Mobility Client\vpncli.exe"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def is_vpn_connected() -> bool:
    """
    Check if VPN is connected using direct Cisco AnyConnect CLI command.
    Returns True only if actually connected to VPN.
    """
    vpncli = get_vpncli_path()
    if not vpncli:
        logging.error("Cisco AnyConnect VPN client is not installed")
        return False

    try:
        # Run 'state' command to get connection status
        result = subprocess.run(
            [vpncli, "state"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        output = result.stdout.strip() if result.stdout else result.stderr.strip()
        logging.info(f"VPN CLI Output: {output}")
        
        # Check if connected
        if result.returncode == 0 and "state: Connected" in output:
            logging.info("VPN is connected")
            return True
        else:
            logging.warning(f"VPN is not connected. State: {output}")
            return False
            
    except subprocess.TimeoutExpired:
        logging.error("VPN CLI command timed out")
        return False
    except Exception as e:
        logging.error(f"Error checking VPN status: {str(e)}")
        return False

def get_cisco_anyconnect_status() -> Tuple[bool, str]:
    """
    Get detailed VPN connection status.
    Returns tuple of (is_connected: bool, status_message: str)
    """
    vpncli = get_vpncli_path()
    if not vpncli:
        return False, "Cisco AnyConnect VPN client is not installed"

    try:
        # Get detailed status
        result = subprocess.run(
            [vpncli, "stats"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        output = result.stdout.strip() if result.stdout else result.stderr.strip()
        logging.info(f"VPN Detailed Status: {output}")
        
        # First check basic connection
        if not is_vpn_connected():
            return False, "VPN is not connected"
            
        # If connected, check if it's the right endpoint
        if "iad-f-orca" in output.lower() or "amazon" in output.lower():
            return True, "Connected to Amazon VPN"
        else:
            # We're connected but possibly to a different VPN
            return True, f"Connected to VPN: {output}"
            
    except subprocess.TimeoutExpired:
        return False, "VPN status check timed out"
    except Exception as e:
        return False, f"Error checking VPN status: {str(e)}"

def launch_anyconnect(vpn_server="iad-f-orca.amazon.com"):
    """
    Launch Cisco AnyConnect and connect to the specified VPN server.
    Returns a tuple of (success: bool, message: str)
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

def launch_vpn_auth():
    """
    Launch the Cisco AnyConnect authentication page for IAD Orca.
    Returns True if the browser was opened successfully, False otherwise.
    """
    try:
        webbrowser.open("https://iad-f-orca.amazon.com")
        return True
    except Exception as e:
        logging.error(f"Failed to launch VPN authentication: {e}")
        return False

def get_connected_vpn() -> Optional[str]:
    """
    Retrieve the current VPN connection details based on the OS.
    Returns the VPN connection details if found, None otherwise.
    """
    current_os = platform.system()

    if current_os == "Windows":
        try:
            # First, check if Cisco AnyConnect is active
            is_connected, status = get_cisco_anyconnect_status()
            if is_connected:
                return status

            # If Cisco AnyConnect is not active, fallback to checking using PowerShell
            result = subprocess.run(["powershell", "-Command", "Get-VpnConnection"], 
                                  capture_output=True, text=True)
            if "Name" in result.stdout:
                return result.stdout.strip()
            return None
        except Exception as e:
            logging.error(f"Error retrieving VPN details on Windows: {e}")
            return None
    else:
        logging.warning(f"Unsupported operating system: {current_os}")
        return None

def setup_vpn_preferences():
    """
    Setup Cisco AnyConnect preferences for automatic connection.
    Creates/updates the preferences XML file.
    """
    preferences_dir = os.path.expandvars(r"%ProgramData%\Cisco\Cisco AnyConnect Secure Mobility Client")
    preferences_file = os.path.join(preferences_dir, "preferences.xml")
    
    preferences_content = """<?xml version="1.0" encoding="UTF-8"?>
<AnyConnectPreferences>
    <DefaultUser>%s</DefaultUser>
    <DefaultSecondUser></DefaultSecondUser>
    <ClientCertificateThumbprint></ClientCertificateThumbprint>
    <ServerCertificateThumbprint></ServerCertificateThumbprint>
    <DefaultHostName>iad-f-orca.amazon.com</DefaultHostName>
    <DefaultHostAddress>iad-f-orca.amazon.com</DefaultHostAddress>
    <DefaultGroup>Amazon-MFA</DefaultGroup>
    <ProxyHost></ProxyHost>
    <ProxyPort></ProxyPort>
    <SDITokenType>none</SDITokenType>
    <ControllablePreferences>
        <AutoConnectOnStart>true</AutoConnectOnStart>
        <MinimizeOnConnect>true</MinimizeOnConnect>
        <LocalLanAccess>true</LocalLanAccess>
        <AutoReconnect>true</AutoReconnect>
        <AutoUpdate>true</AutoUpdate>
        <RSASecurIDIntegration>automatic</RSASecurIDIntegration>
        <WindowsLogonEnforcement>SingleLocalLogon</WindowsLogonEnforcement>
        <CertificateStore>All</CertificateStore>
        <CertificateStoreOverride>false</CertificateStoreOverride>
        <ProxySettings>Native</ProxySettings>
        <AllowLocalProxyConnections>true</AllowLocalProxyConnections>
        <AuthenticationTimeout>30</AuthenticationTimeout>
        <AutoCertSelection>true</AutoCertSelection>
        <EnableAutomaticServerSelection>false</EnableAutomaticServerSelection>
    </ControllablePreferences>
</AnyConnectPreferences>""" % os.getenv('USERNAME')

    try:
        # Ensure directory exists
        os.makedirs(preferences_dir, exist_ok=True)
        
        # Write preferences file
        with open(preferences_file, 'w') as f:
            f.write(preferences_content)
        
        logging.info("Successfully configured VPN preferences")
        return True
    except Exception as e:
        logging.error(f"Error setting up VPN preferences: {e}")
        return False

def capture_connect_button():
    """
    Helper function to capture the Connect button image from Cisco AnyConnect UI.
    This should be run once to create the reference image.
    """
    try:
        # Get AnyConnect GUI path
        anyconnect_path = get_anyconnect_path()
        if not anyconnect_path:
            print("Cisco AnyConnect client not found")
            return False

        gui_path = os.path.join(anyconnect_path, "vpnui.exe")
        if not os.path.exists(gui_path):
            print("Cisco AnyConnect UI not found")
            return False

        print("Launching Cisco AnyConnect UI...")
        subprocess.Popen([gui_path])
        time.sleep(2)  # Wait for UI to load

        print("Please position your mouse over the Connect button and press Enter...")
        input()
        
        # Get mouse position
        x, y = pyautogui.position()
        
        # Capture region around the button (adjust size as needed)
        screenshot = pyautogui.screenshot(region=(x-50, y-15, 100, 30))
        
        # Save the image
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        os.makedirs(assets_dir, exist_ok=True)
        image_path = os.path.join(assets_dir, "connect_button.png")
        screenshot.save(image_path)
        
        print(f"Saved connect button image to: {image_path}")
        return True

    except Exception as e:
        print(f"Error capturing button: {str(e)}")
        return False

def connect_to_vpn(vpn_server="iad-f-orca.amazon.com") -> Tuple[bool, str]:
    """
    Connect to VPN using direct COM automation with Cisco AnyConnect API.
    Returns tuple of (success: bool, message: str)
    """
    try:
        # First check if already connected
        if is_vpn_connected():
            return True, "Already connected to VPN"

        logging.info("Initializing COM interface...")
        # Initialize COM in this thread
        pythoncom.CoInitialize()
        
        try:
            # Create ICiscoCertValidationEventHandler interface
            cert_handler = win32com.client.DispatchWithEvents(
                "CiscoAnyConnect.Session",
                ICiscoCertValidationEventHandler
            )
            
            # Create the VPN session object
            vpn = win32com.client.Dispatch("CiscoAnyConnect.Session")
            
            logging.info(f"Connecting to VPN server: {vpn_server}")
            
            # Start connection
            vpn.Connect(
                vpn_server,  # Server address
                True,        # Save credentials
                "",         # Username (empty to use saved)
                "",         # Password (empty to use saved)
                ""         # Second password (empty to use saved)
            )
            
            # Wait for connection
            timeout = 30  # seconds
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                if is_vpn_connected():
                    logging.info("Successfully connected to VPN")
                    return True, "Successfully connected to VPN"
                time.sleep(1)
            
            logging.warning("Connection timeout")
            return False, "Connection timeout - please check your credentials"
            
        except Exception as e:
            logging.error(f"Error in COM automation: {str(e)}")
            return False, f"Error connecting: {str(e)}"
        finally:
            # Clean up COM
            pythoncom.CoUninitialize()
            
    except Exception as e:
        logging.error(f"Error connecting to VPN: {str(e)}")
        return False, f"Error: {str(e)}"

class ICiscoCertValidationEventHandler:
    """Event handler for certificate validation"""
    
    def OnCertificateValidationRequired(self, certThumbprint, certIssuer, certSubject):
        """Automatically accept certificates"""
        logging.info(f"Certificate validation required: {certSubject}")
        return True  # Accept certificate
        
    def OnError(self, errorMessage):
        """Handle errors"""
        logging.error(f"VPN Error: {errorMessage}")
        
    def OnStateChange(self, state):
        """Handle state changes"""
        logging.info(f"VPN State changed: {state}")

def launch_vpn_connection():
    """
    Alternative method using command-line interface if COM automation fails.
    """
    try:
        vpncli = get_vpncli_path()
        if not vpncli:
            return False, "VPN CLI not found"
            
        # Get settings
        from settings_dialog import SettingsDialog
        settings = SettingsDialog(None)
        server = settings.get_vpn_server()
        
        # Start connection process
        process = subprocess.Popen(
            [vpncli, "connect", server],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Monitor output
        while True:
            line = process.stdout.readline()
            if not line:
                break
                
            logging.info(f"VPN: {line.strip()}")
            
            # Handle prompts
            if "accept?" in line.lower():
                process.stdin.write("y\n")
                process.stdin.flush()
            elif "username:" in line.lower():
                # Let the GUI handle credentials
                break
                
        return True, "VPN connection initiated"
        
    except Exception as e:
        logging.error(f"Error launching VPN: {str(e)}")
        return False, str(e)

def connect_to_vpn_with_fallback(vpn_server="iad-f-orca.amazon.com") -> Tuple[bool, str]:
    """
    Try multiple methods to connect to VPN.
    Returns tuple of (success: bool, message: str)
    """
    # First try COM automation
    success, message = connect_to_vpn(vpn_server)
    if success:
        return True, message
        
    logging.warning("COM automation failed, trying CLI method...")
    
    # If COM fails, try CLI method
    success, message = launch_vpn_connection()
    if not success:
        return False, f"All connection attempts failed: {message}"
        
    # Wait for connection
    timeout = 30
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_vpn_connected():
            return True, "Successfully connected to VPN"
        time.sleep(1)
        
    return False, "Connection timeout - please check your credentials"

def connect_vpn():
    """
    Attempts to connect to VPN using COM automation
    """
    try:
        # Get settings
        from settings_dialog import SettingsDialog
        settings = SettingsDialog(None)  # None since we don't need UI parent
        server = settings.get_vpn_server()
        
        import win32com.client
        vpn = win32com.client.Dispatch("Cisco.AnyConnectGui")
        vpn.Connect(server)
        return True
    except Exception as e:
        logging.error(f"Error connecting to VPN: {e}")
        return False

def connect_vpn_cli():
    """
    Fallback method to connect VPN using CLI
    """
    try:
        # Get settings
        from settings_dialog import SettingsDialog
        settings = SettingsDialog(None)
        server = settings.get_vpn_server()
        
        vpncli = r"C:\Program Files (x86)\Cisco\Cisco AnyConnect Secure Mobility Client\vpncli.exe"
        result = subprocess.run([vpncli, "connect", server], 
                              capture_output=True, 
                              text=True)
        return "state: Connected" in result.stdout
    except Exception as e:
        logging.error(f"Error connecting to VPN via CLI: {e}")
        return False

if __name__ == "__main__":
    # Test VPN status
    is_connected, status = get_cisco_anyconnect_status()
    print(f"VPN Status: {status}")
    if not is_connected:
        # Capture the connect button image if it doesn't exist
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        button_image = os.path.join(assets_dir, "connect_button.png")
        if not os.path.exists(button_image):
            print("Connect button image not found. Capturing now...")
            capture_connect_button()
        print("Attempting to launch VPN...")
        success, message = launch_anyconnect()
        print(message)
