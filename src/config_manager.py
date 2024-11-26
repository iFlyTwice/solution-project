import os
import json
import logging
from pathlib import Path

class ConfigManager:
    # Get the user's home directory for config storage
    USER_HOME = os.path.expanduser('~')
    CONFIG_DIR = os.path.join(USER_HOME, '.quick_links_dashboard')
    CONFIG_FILE = os.path.join(CONFIG_DIR, "window_states.json")
    
    WINDOW_DEFAULTS = {
        "main_window": {
            "geometry": "800x600+100+100",
            "always_on_top": False
        },
        "settings_window": {
            "geometry": "400x300+200+200"
        },
        "notification_popover": {
            "x": 240,
            "y": 100
        },
        "manage_zukey_window": {
            "geometry": "800x600+100+100"
        }
    }
    
    @classmethod
    def ensure_config_dir(cls):
        """Ensure the config directory exists."""
        try:
            if not os.path.exists(cls.CONFIG_DIR):
                os.makedirs(cls.CONFIG_DIR, exist_ok=True)
                logging.info(f"Created config directory: {cls.CONFIG_DIR}")
            return True
        except Exception as e:
            logging.error(f"Failed to create config directory: {e}", exc_info=True)
            return False
    
    @classmethod
    def save_window_state(cls, window_id: str, state: dict):
        """Save window state to config file."""
        try:
            if not cls.ensure_config_dir():
                logging.error("Cannot save window state: config directory creation failed")
                return
                
            config = cls.load_config()
            
            # Validate state before saving
            if not isinstance(state, dict):
                logging.error(f"Invalid state format for {window_id}: {state}")
                return
                
            # Merge with existing state to preserve other fields
            if window_id in config:
                config[window_id].update(state)
            else:
                config[window_id] = state
            
            # Use atomic write operation
            temp_file = cls.CONFIG_FILE + '.tmp'
            try:
                with open(temp_file, 'w') as f:
                    json.dump(config, f, indent=4)
                os.replace(temp_file, cls.CONFIG_FILE)
                logging.info(f"Saved window state for {window_id}: {state}")
            except Exception as e:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                raise
                
        except Exception as e:
            logging.error(f"Failed to save window state for {window_id}: {e}", exc_info=True)
    
    @classmethod
    def load_config(cls):
        """Load configuration from file or return defaults."""
        try:
            if os.path.exists(cls.CONFIG_FILE):
                try:
                    with open(cls.CONFIG_FILE, 'r') as f:
                        config = json.load(f)
                except json.JSONDecodeError as e:
                    logging.error(f"Invalid JSON in config file: {e}")
                    return cls.WINDOW_DEFAULTS.copy()
                except Exception as e:
                    logging.error(f"Error reading config file: {e}")
                    return cls.WINDOW_DEFAULTS.copy()
                    
                # Validate and merge with defaults
                if not isinstance(config, dict):
                    logging.error("Invalid config format")
                    return cls.WINDOW_DEFAULTS.copy()
                    
                # Merge with defaults to ensure all required fields exist
                result = cls.WINDOW_DEFAULTS.copy()
                for window_id, state in config.items():
                    if isinstance(state, dict):
                        if window_id in result:
                            result[window_id].update(state)
                        else:
                            result[window_id] = state
                return result
                
        except Exception as e:
            logging.error(f"Failed to load config: {e}", exc_info=True)
        
        return cls.WINDOW_DEFAULTS.copy()
    
    @classmethod
    def get_window_state(cls, window_id: str):
        """Get saved window state or default values for a specific window.
        
        Args:
            window_id (str): Identifier for the window (e.g., 'main_window')
            
        Returns:
            dict: Window state configuration
        """
        config = cls.load_config()
        return config.get(window_id, cls.WINDOW_DEFAULTS.get(window_id, {}))
