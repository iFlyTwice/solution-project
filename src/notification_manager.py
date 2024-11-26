"""
Enhanced notification manager with better error handling, type hints, and class-based structure.
Uses plyer by default with win10toast as fallback on Windows.
"""

from typing import Optional, List, Dict
import logging
import platform
import threading
from datetime import datetime
from plyer import notification
from win10toast import ToastNotifier


class NotificationManager:
    """
    Manages system notifications using plyer with a fallback to win10toast on Windows.
    Maintains a history of notifications and provides thread-safe operations.
    """

    def __init__(self):
        """Initializes the NotificationManager with platform-specific notifiers."""
        self.system = platform.system()
        self.toaster = ToastNotifier() if self.system == "Windows" else None
        self.history: List[Dict[str, str]] = []
        self.history_lock = threading.Lock()
        logging.info("NotificationManager initialized")

    def show_notification(self, title: str, message: str, app_icon: Optional[str] = None, timeout: int = 5) -> None:
        """
        Displays a system notification and records it in history.

        Args:
            title: The title of the notification
            message: The message body of the notification
            app_icon: Path to the icon file (optional)
            timeout: Duration in seconds for which the notification is displayed
        """
        # Record notification in history
        notification_entry = {
            "title": title,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }

        with self.history_lock:
            self.history.append(notification_entry)

        try:
            # Try plyer first
            notification.notify(
                title=title,
                message=message,
                app_icon=app_icon,
                timeout=timeout
            )
            self._update_notification_status(notification_entry, "success")
            logging.info(f"Notification shown using plyer: {title}")

        except Exception as e:
            # Fall back to win10toast on Windows
            if self.system == "Windows" and self.toaster:
                try:
                    threading.Thread(
                        target=self._show_with_win10toast,
                        args=(title, message, timeout, notification_entry),
                        daemon=True
                    ).start()
                except Exception as e:
                    self._update_notification_status(notification_entry, "failed")
                    logging.error(f"Failed to show notification using win10toast: {e}")
            else:
                self._update_notification_status(notification_entry, "failed")
                logging.error(f"No supported notification system available: {e}")

    def _show_with_win10toast(self, title: str, message: str, timeout: int, entry: Dict[str, str]) -> None:
        """Shows a notification using win10toast."""
        try:
            self.toaster.show_toast(title, message, duration=timeout, threaded=True)
            self._update_notification_status(entry, "success")
            logging.info(f"Notification shown using win10toast: {title}")
        except Exception as e:
            self._update_notification_status(entry, "failed")
            logging.error(f"Failed to show notification using win10toast: {e}")

    def _update_notification_status(self, entry: Dict[str, str], status: str) -> None:
        """Updates the status of a notification entry."""
        with self.history_lock:
            entry["status"] = status

    def get_notification_history(self) -> List[Dict[str, str]]:
        """Returns a copy of the notification history."""
        with self.history_lock:
            return list(self.history)

    def clear_notification_history(self) -> None:
        """Clears the notification history."""
        with self.history_lock:
            self.history.clear()
        logging.info("Notification history cleared")

    def get_recent_notifications(self, limit: int = 5) -> List[Dict[str, str]]:
        """Returns the most recent notifications, up to the specified limit."""
        with self.history_lock:
            return list(sorted(
                self.history,
                key=lambda x: x["timestamp"],
                reverse=True
            ))[:limit]

    def get_failed_notifications(self) -> List[Dict[str, str]]:
        """Returns all failed notifications."""
        with self.history_lock:
            return [n for n in self.history if n["status"] == "failed"]


# For backwards compatibility
def show_notification(title: str, message: str, app_icon: Optional[str] = None, timeout: int = 5) -> None:
    """
    Legacy function for backwards compatibility.
    Displays a system notification using the NotificationManager.
    """
    manager = NotificationManager()
    manager.show_notification(title, message, app_icon, timeout)
