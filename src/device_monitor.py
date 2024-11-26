import usb.core
import usb.util
import logging
from constants import KNOWN_SECURITY_KEYS
import hid  # 'hid' from pyhidapi

# Remove monitoring functions if they are now handled in Core.py
# def detect_security_keys():
    # ... existing code ... 