import customtkinter as ctk
import logging
import os
import subprocess
import sys
import hid
# Add more GUI-related imports if necessary

def create_window_controls(root, on_closing_callback, on_minimize_callback):
    """
    Creates and packs the window control buttons (Minimize and Exit) at the top right.
    Currently not adding buttons to the UI.
    """
    pass  # No buttons will be created

def create_button_frame(root, links, open_link_callback, handle_midway_access_callback, open_manage_zukey_callback, open_general_dashboard_callback, open_scanner_apw_callback=None):
    """
    Creates and packs the button frame with modern styled link buttons.
    """
    # Get compact mode setting from parent's settings
    compact_mode = False
    if hasattr(root, 'master') and hasattr(root.master, 'settings'):
        compact_mode = root.master.settings.settings.get('compact_mode', False)

    # Create main button container with padding
    button_container = ctk.CTkFrame(
        master=root,
        fg_color=("gray95", "gray10"),
        corner_radius=10
    )
    button_container.pack(pady=(20, 10), padx=20, fill="x", expand=False)
    
    # Add header
    header = ctk.CTkLabel(
        button_container,
        text="Quick Links",
        font=("Segoe UI", 20 if not compact_mode else 16, "bold"),
        anchor="w"
    )
    header.pack(fill="x", padx=15, pady=(15 if not compact_mode else 10, 10 if not compact_mode else 5))
    
    # Create grid frame for buttons
    button_frame = ctk.CTkFrame(
        master=button_container,
        fg_color="transparent"
    )
    button_frame.pack(fill="x", expand=True, padx=15, pady=(0, 15 if not compact_mode else 10))
    
    # Configure grid columns to be equal width
    button_frame.grid_columnconfigure(0, weight=1)
    button_frame.grid_columnconfigure(1, weight=1)
    
    # Button configurations with modern styling
    button_configs = {
        "MIDWAY ACCESS": {
            "icon": "",
            "callback": handle_midway_access_callback,
            "color": "#2986cc",  # Blue
            "hover": "#1a5f8c"
        },
        "GENERAL FEATURES": {
            "icon": "",
            "callback": open_general_dashboard_callback,
            "color": "#6aa84f",  # Green
            "hover": "#4c7a39"
        },
        "REPORTS": {
            "icon": "",
            "callback": lambda url=links["REPORTS"], name="REPORTS": open_link_callback(url, name),
            "color": "#e69138",  # Orange
            "hover": "#b67429"
        },
        "MANAGE ZUKEY": {
            "icon": "",
            "callback": open_manage_zukey_callback,
            "color": "#8e7cc3",  # Purple
            "hover": "#6b5d94"
        }
    }
    
    row = 0
    col = 0
    
    # Adjust button dimensions based on compact mode
    button_width = 280 if not compact_mode else 220
    button_height = 45 if not compact_mode else 35
    button_font_size = 14 if not compact_mode else 12
    button_padding = 5 if not compact_mode else 3
    
    # Create buttons with modern styling
    for name, config in button_configs.items():
        # Create button container frame
        button_container_frame = ctk.CTkFrame(
            button_frame,
            fg_color="transparent"
        )
        button_container_frame.grid(row=row, column=col, padx=button_padding, pady=button_padding, sticky="nsew")
        
        # Create the actual button
        button = ctk.CTkButton(
            master=button_container_frame,
            text=f"{config['icon']} {name}",
            command=config['callback'],
            width=button_width,
            height=button_height,
            corner_radius=8 if not compact_mode else 6,
            fg_color=config['color'],
            hover_color=config['hover'],
            font=("Segoe UI", button_font_size, "bold"),
            anchor="center"
        )
        button.pack(expand=True, fill="both")
        
        # Update grid position
        col += 1
        if col > 1:
            col = 0
            row += 1
    
    # Create Scanner APW button in its own container
    scanner_container = ctk.CTkFrame(
        button_container,
        fg_color="transparent"
    )
    scanner_container.pack(fill="x", padx=15, pady=(0, 15 if not compact_mode else 10))
    
    # Store the button command as a reference to be updated later
    button_command = open_scanner_apw_callback if open_scanner_apw_callback else lambda: None
    
    # Add Scanner APW button with modern styling
    scanner_button = ctk.CTkButton(
        scanner_container,
        text="🔍 Scanner APW",
        command=button_command,
        width=button_width,
        height=button_height,
        corner_radius=8 if not compact_mode else 6,
        fg_color="#ff6b6b",  # Distinct red color
        hover_color="#cc5555",
        font=("Segoe UI", button_font_size, "bold"),
        anchor="center"
    )
    scanner_button.pack(expand=True, fill="both")
    
    return button_container

def create_security_keys_list(root, on_key_double_click):
    """
    Creates a modern security keys list view.
    """
    # Create container frame with modern styling
    container = ctk.CTkFrame(
        root,
        fg_color=("gray95", "gray10"),
        corner_radius=10
    )
    container.pack(fill="x", padx=20, pady=(5, 20))
    
    # Add header with modern styling
    header_frame = ctk.CTkFrame(container, fg_color="transparent")
    header_frame.pack(fill="x", padx=15, pady=(10, 5))
    
    header = ctk.CTkLabel(
        header_frame,
        text="Security Keys",
        font=("Segoe UI", 20, "bold"),
        anchor="w"
    )
    header.pack(side="left")
    
    # Create the list view with modern styling
    keys_list = ctk.CTkTextbox(
        container,
        height=100,
        font=("Segoe UI", 12),
        corner_radius=8,
        border_width=1,
        border_color=("gray80", "gray30")
    )
    keys_list.pack(fill="x", padx=15, pady=(0, 10))
    
    # Bind double-click event
    keys_list.bind("<Double-Button-1>", lambda e: on_key_double_click(keys_list))
    
    return keys_list

def update_security_keys_list(textbox, keys):
    """
    Updates the security keys list in the GUI.
    """
    try:
        if not isinstance(textbox, ctk.CTkTextbox):
            logging.error("Invalid textbox widget provided")
            return
            
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        
        if keys:
            for key in keys:
                textbox.insert("end", f"{key}\n")
            logging.info(f"Updated security keys list with: {keys}")
        else:
            textbox.insert("end", "No security keys detected\n")
            logging.info("No security keys to display")
            
        textbox.configure(state="disabled")
        
    except Exception as e:
        logging.error(f"Error updating security keys list: {e}")

def get_connected_keys():
    """
    Gets a list of connected security keys.
    Returns a list of key names.
    """
    try:
        # Initialize an empty list to store detected keys
        connected_keys = []
        
        # Get all HID devices
        devices = hid.enumerate()
        
        # Known security key identifiers
        SECURITY_KEY_IDS = [
            {'name': 'ZUKEY 2', 'vendor_id': 0x1949, 'product_id': 0x0429},  # ZUKEY 2
            {'name': 'YubiKey', 'vendor_id': 0x1050},  # YubiKey
            {'name': 'Google Titan', 'vendor_id': 0x18d1},  # Google Titan
            {'name': 'Feitian', 'vendor_id': 0x096e}  # Feitian
        ]
        
        # Log the number of devices found
        logging.info(f"Found {len(devices)} HID devices")
        
        for device in devices:
            try:
                vendor_id = device.get('vendor_id', 0)
                product_id = device.get('product_id', 0)
                
                # Log each device for debugging
                logging.debug(f"Checking device - VID: 0x{vendor_id:04X}, PID: 0x{product_id:04X}")
                
                # Check for ZUKEY first (exact match)
                if vendor_id == 0x1949 and product_id == 0x0429:
                    key_name = "ZUKEY 2"
                    connected_keys.append(key_name)
                    logging.info(f"ZUKEY detected: {key_name}")
                    continue
                
                # Check other security keys
                for key_id in SECURITY_KEY_IDS:
                    if vendor_id == key_id['vendor_id']:
                        if 'product_id' not in key_id or product_id == key_id['product_id']:
                            manufacturer = device.get('manufacturer_string', '')
                            product = device.get('product_string', '')
                            key_name = f"{manufacturer} {product}".strip() or key_id['name']
                            connected_keys.append(key_name)
                            logging.info(f"Security key detected: {key_name}")
                            break
                
            except Exception as e:
                logging.error(f"Error processing device: {e}")
                continue
        
        # Log the final list of detected keys
        logging.info(f"Detected security keys: {connected_keys}")
        return connected_keys
        
    except Exception as e:
        logging.error(f"Error in get_connected_keys: {e}")
        return []

def set_window_size(root, width=900, height=700):
    """
    Sets the window size and centers it on the screen.
    """
    # Get screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    
    # Calculate center position
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    
    # Set minimum window size
    root.minsize(800, 600)
    
    # Set window geometry
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    # Make window semi-transparent during move/resize
    root.attributes("-alpha", 0.95)

def adjust_color_brightness(hex_color, brightness_offset):
    """
    Adjusts the brightness of a hex color.
    brightness_offset: Negative values make color darker, positive make it lighter
    """
    # Convert hex to RGB
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    # Adjust brightness
    adjusted_rgb = tuple(max(0, min(255, value + brightness_offset)) for value in rgb)
    
    # Convert back to hex
    return '#{:02x}{:02x}{:02x}'.format(*adjusted_rgb)

def toggle_pin_visibility(pin_entry, show_pin_button, pin_visible):
    """
    Toggles the visibility of the PIN entry field.
    
    Args:
        pin_entry (CTkEntry): The PIN entry widget
        show_pin_button (CTkButton): The button to toggle visibility
        pin_visible (bool): Current visibility state
    
    Returns:
        bool: New visibility state
    """
    if pin_visible:
        pin_entry.configure(show="*")
        show_pin_button.configure(text="Show PIN")
        return False
    else:
        pin_entry.configure(show="")
        show_pin_button.configure(text="Hide PIN")
        return True