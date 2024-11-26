import customtkinter as ctk
from Core import QuickLinksApp  # Ensure QuickLinksApp is imported correctly

def set_window_size(root, width_ratio=0.6, height_ratio=0.6):
    """
    Calculates and sets the window size and position based on screen resolution.

    Args:
        root (ctk.CTk): The main window instance.
        width_ratio (float): The ratio of the screen width to set the window width.
        height_ratio (float): The ratio of the screen height to set the window height.
    """
    # Calculate screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Define window size as a percentage of screen size
    window_width = int(screen_width * width_ratio)
    window_height = int(screen_height * height_ratio)

    # Calculate position to center the window
    position_x = (screen_width - window_width) // 2
    position_y = (screen_height - window_height) // 2

    # Set the geometry of the window
    root.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}") 

def create_button_frame(root, links, open_link_callback, handle_midway_access_callback, open_manage_zukey_callback):
    """
    Creates and packs the button frame with link buttons.

    Args:
        root (ctk.CTk): The main window instance.
        links (dict): Dictionary of link names and URLs.
        open_link_callback (function): Callback to open a link.
        handle_midway_access_callback (function): Callback to handle MIDWAY ACCESS.
        open_manage_zukey_callback (function): Callback to open Manage Zukey window.
    """
    button_frame = ctk.CTkFrame(master=root)
    button_frame.pack(pady=20, padx=60, fill="both", expand=True)

    for name, url in links.items():
        if name == "MIDWAY ACCESS":
            button = ctk.CTkButton(
                master=button_frame,
                text=name,
                command=handle_midway_access_callback,
                width=300,
                height=50
            )
        else:
            button = ctk.CTkButton(
                master=button_frame,
                text=name,
                command=lambda url=url, name=name: open_link_callback(url, name),
                width=300,
                height=50
            )
        button.pack(pady=10)
    
    # Add the "Manage Zukey" button
    manage_zukey_button = ctk.CTkButton(
        master=button_frame,
        text="Manage Zukey",
        command=open_manage_zukey_callback,
        width=300,
        height=50
    )
    manage_zukey_button.pack(pady=10)

def create_credentials_frame(root, toggle_pin_visibility_callback):
    """
    Creates and packs the credentials frame with username and PIN entries.

    Args:
        root (ctk.CTk): The main window instance.
        toggle_pin_visibility_callback (function): Callback to toggle PIN visibility.
    
    Returns:
        tuple: (username_entry, pin_entry, show_pin_button)
    """
    credentials_frame = ctk.CTkFrame(master=root)
    credentials_frame.pack(pady=10, padx=20, fill="x", expand=False)

    # Username label and entry
    username_label = ctk.CTkLabel(master=credentials_frame, text="Username:")
    username_label.pack(side="left", padx=10, pady=5)
    username_entry = ctk.CTkEntry(master=credentials_frame, width=200)
    username_entry.pack(side="left", padx=10, pady=5)

    # PIN label and entry
    pin_label = ctk.CTkLabel(master=credentials_frame, text="PIN:")
    pin_label.pack(side="left", padx=10, pady=5)
    pin_entry = ctk.CTkEntry(master=credentials_frame, width=200, show="*")
    pin_entry.pack(side="left", padx=10, pady=5)

    # Show/Hide button for PIN entry
    show_pin_button = ctk.CTkButton(
        master=credentials_frame,
        text="Show",
        width=60,
        height=30,
        command=toggle_pin_visibility_callback
    )
    show_pin_button.pack(side="left", padx=10, pady=5)

    return username_entry, pin_entry, show_pin_button

def toggle_pin_visibility(pin_entry, show_pin_button, pin_visible):
    """
    Toggles the visibility of the PIN entry.

    Args:
        pin_entry (ctk.CTkEntry): The PIN entry widget.
        show_pin_button (ctk.CTkButton): The show/hide button widget.
        pin_visible (bool): Current visibility state of the PIN.
    
    Returns:
        bool: Updated visibility state of the PIN.
    """
    if pin_visible:
        pin_entry.configure(show="*")
        show_pin_button.configure(text="Show")
        return False
    else:
        pin_entry.configure(show="")
        show_pin_button.configure(text="Hide")
        return True

def create_window_controls(root, on_closing_callback, on_minimize_callback):
    """
    Creates and packs the window control buttons (Minimize and Exit) at the top right.

    Args:
        root (ctk.CTk): The main window instance.
        on_closing_callback (function): Callback to handle window closing.
        on_minimize_callback (function): Callback to handle window minimizing.
    """
    window_controls_frame = ctk.CTkFrame(master=root, width=200, height=40)
    window_controls_frame.place(x=root.winfo_width() - 220, y=10)  # Position at top right with some padding

    # Create Minimize Button
    minimize_button = ctk.CTkButton(
        master=window_controls_frame,
        text="-",
        fg_color="yellow",        # Yellow background
        text_color="black",       # Black text
        hover_color="lightyellow",
        command=on_minimize_callback,
        width=20,
        height=20,
        corner_radius=10          # Make it circular
    )
    minimize_button.pack(side="left", padx=5)

    # Create Exit Button
    exit_button = ctk.CTkButton(
        master=window_controls_frame,
        text="X",
        fg_color="red",           # Red background
        text_color="white",       # White text
        hover_color="darkred",
        command=on_closing_callback,
        width=20,
        height=20,
        corner_radius=10          # Make it circular
    )
    exit_button.pack(side="left", padx=5)

def create_security_keys_list(root, on_key_double_click):
    """
    Creates and packs the security keys list view on the right side of the window.

    Args:
        root (ctk.CTk): The main window instance.
        on_key_double_click (function): Callback function to handle double-click events.
    
    Returns:
        ctk.CTkListbox: The listbox widget displaying security keys.
    """
    security_keys_frame = ctk.CTkFrame(master=root)
    security_keys_frame.pack(pady=20, padx=10, fill="y", side="right", expand=False)

    security_keys_label = ctk.CTkLabel(master=security_keys_frame, text="Connected Security Keys:")
    security_keys_label.pack(pady=5)

    # Use a widget that supports double-click events
    security_keys_list = ctk.CTkListbox(master=security_keys_frame, width=200, height=300)
    security_keys_list.pack(pady=5, fill="both", expand=True)

    # Bind the double-click event to the callback function
    security_keys_list.bind("<Double-Button-1>", lambda event: on_key_double_click(security_keys_list))

    return security_keys_list

def update_security_keys_list(security_keys_list, keys):
    """
    Updates the security keys list view with the current connected keys.

    Args:
        security_keys_list (ctk.CTkTextbox): The textbox widget to update.
        keys (list): List of connected security keys.
    """
    security_keys_list.configure(state="normal")
    security_keys_list.delete("1.0", "end")
    for key in keys:
        security_keys_list.insert("end", f"{key}\n")
    security_keys_list.configure(state="disabled")

def on_key_double_click(security_keys_list):
    """
    Handles double-click events on a security key.

    Args:
        security_keys_list (CTkListbox): The listbox widget containing security keys.
    """
    # Get the selected item
    selected_index = security_keys_list.curselection()
    if not selected_index:
        return  # No item selected

    selected_key = security_keys_list.get(selected_index[0])
    logging.info(f"Double-clicked on key: {selected_key}")
    print(f"Double-clicked on key: {selected_key}")

    # Trigger automation process for the selected key
    initiate_reset_security_key(selected_key)  # Adjust to your automation logic

if __name__ == "__main__":
    root = ctk.CTk()
    app = QuickLinksApp(root)
    root.mainloop()