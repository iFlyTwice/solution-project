import functools
import logging
import json
import os
from datetime import datetime
from typing import Optional, Any, Callable

def handle_errors(error_message: str = "An error occurred", log_error: bool = True):
    """
    A decorator for centralized error handling.
    
    Args:
        error_message (str): Custom error message prefix
        log_error (bool): Whether to log the error
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logging.error(f"{error_message}: {str(e)}")
                # If first argument is a class instance with update_notification method, use it
                if args and hasattr(args[0], 'update_notification'):
                    args[0].update_notification(f"{error_message}: {str(e)}", "red")
                raise  # Re-raise the exception for higher-level handling
        return wrapper
    return decorator

class NotificationManager:
    """Manages persistent notifications with different severity levels."""
    
    NOTIFICATION_FILE = "config/notifications.json"
    
    @classmethod
    def save_notification(cls, message: str, level: str = "info") -> None:
        """Save a notification to persistent storage."""
        try:
            notifications = cls.load_notifications()
            notifications.append({
                "message": message,
                "level": level,
                "timestamp": datetime.now().isoformat(),
                "read": False
            })
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(cls.NOTIFICATION_FILE), exist_ok=True)
            
            with open(cls.NOTIFICATION_FILE, 'w') as f:
                json.dump(notifications, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save notification: {e}")

    @classmethod
    def load_notifications(cls) -> list:
        """Load notifications from persistent storage."""
        try:
            if os.path.exists(cls.NOTIFICATION_FILE):
                with open(cls.NOTIFICATION_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Failed to load notifications: {e}")
        return []

    @classmethod
    def mark_as_read(cls, index: int) -> None:
        """Mark a notification as read."""
        try:
            notifications = cls.load_notifications()
            if 0 <= index < len(notifications):
                notifications[index]["read"] = True
                with open(cls.NOTIFICATION_FILE, 'w') as f:
                    json.dump(notifications, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to mark notification as read: {e}")

def cache_resource(cache_key: str):
    """
    A decorator for caching resource loading results.
    
    Args:
        cache_key (str): Key to identify the cached resource
    """
    cache = {}
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if cache_key not in cache:
                cache[cache_key] = func(*args, **kwargs)
            return cache[cache_key]
        return wrapper
    return decorator

@cache_resource("security_key_icons")
def load_security_key_icons() -> dict:
    """Load and cache security key icons."""
    icons = {}
    icon_dir = "resources/icons"
    try:
        if os.path.exists(icon_dir):
            for filename in os.listdir(icon_dir):
                if filename.endswith(('.png', '.ico')):
                    key_name = os.path.splitext(filename)[0]
                    icons[key_name] = os.path.join(icon_dir, filename)
    except Exception as e:
        logging.error(f"Failed to load security key icons: {e}")
    return icons

def check_dependencies() -> tuple[bool, list]:
    """
    Check if all required dependencies are installed.
    
    Returns:
        tuple: (bool: all dependencies met, list: missing dependencies)
    """
    required_packages = [
        'customtkinter',
        'pillow',
        'opencv-python',
        'pyautogui',
        'pystray'
    ]
    
    missing = []
    try:
        import pkg_resources
        installed = {pkg.key for pkg in pkg_resources.working_set}
        missing = [pkg for pkg in required_packages if pkg.lower() not in installed]
    except Exception as e:
        logging.error(f"Failed to check dependencies: {e}")
        return False, required_packages
    
    return len(missing) == 0, missing
