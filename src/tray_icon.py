import threading
import logging
import pystray
from PIL import Image
import os

def setup_tray_icon(show_callback, exit_callback):
    """
    Sets up the system tray icon.

    Args:
        show_callback (function): Callback to show the main window.
        exit_callback (function): Callback to exit the application.
    """
    icon_path = "icon.png"  # Ensure this path is correct
    if not os.path.exists(icon_path):
        logging.warning(f"Tray icon file {icon_path} not found.")
        return None

    image = Image.open(icon_path)
    menu = pystray.Menu(
        pystray.MenuItem('Show', show_callback),
        pystray.MenuItem('Exit', exit_callback)
    )
    tray_icon_obj = pystray.Icon("QuickLinksApp", image, "Quick Links Dashboard", menu)
    threading.Thread(target=tray_icon_obj.run, daemon=True).start()
    logging.info("System tray icon setup complete.")
    return tray_icon_obj 