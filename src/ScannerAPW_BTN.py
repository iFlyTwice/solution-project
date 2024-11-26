import customtkinter as ctk
from tkinter import messagebox
import threading
import subprocess
import os
import logging
from vpn_settings import get_cisco_anyconnect_status

class PasscodeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Passcode Finder")
        self.geometry("600x700")
        self.resizable(False, False)

        # Main Container Frame with padding
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(padx=40, pady=30, fill="both", expand=True)

        # VPN Status Label at the top
        self.vpn_status_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.vpn_status_frame.pack(fill="x", pady=(0, 15))

        self.vpn_status_label = ctk.CTkLabel(
            self.vpn_status_frame,
            text="Checking VPN status...",
            font=("Helvetica", 14, "bold"),
            text_color="gray"
        )
        self.vpn_status_label.pack(side="left")

        self.vpn_indicator = ctk.CTkLabel(
            self.vpn_status_frame,
            text="●",  # Dot indicator
            font=("Helvetica", 20, "bold"),
            text_color="gray"
        )
        self.vpn_indicator.pack(side="left", padx=5)

        # Input Fields
        self.serial_label = ctk.CTkLabel(
            self.main_frame,
            text="Serial Number:",
            font=("Helvetica", 14, "bold")
        )
        self.serial_label.pack(pady=(0, 5))
        self.serial_entry = ctk.CTkEntry(
            self.main_frame,
            width=400,
            height=40,
            font=("Helvetica", 14)
        )
        self.serial_entry.pack(pady=(0, 15))

        self.region_label = ctk.CTkLabel(
            self.main_frame,
            text="Region:",
            font=("Helvetica", 14, "bold")
        )
        self.region_label.pack(pady=(0, 5))
        self.region_menu = ctk.CTkComboBox(
            self.main_frame,
            values=["us-east-1", "us-west-2", "ap-northeast-1", "ap-south-1", "eu-west-1"],
            width=400,
            height=40,
            font=("Helvetica", 14),
            dropdown_font=("Helvetica", 14)
        )
        self.region_menu.set("us-east-1")
        self.region_menu.pack(pady=(0, 15))

        # PIN Input Field
        self.pin_label = ctk.CTkLabel(
            self.main_frame,
            text="PIN:",
            font=("Helvetica", 14, "bold")
        )
        self.pin_label.pack(pady=(0, 5))
        self.pin_entry = ctk.CTkEntry(
            self.main_frame,
            width=400,
            height=40,
            font=("Helvetica", 14),
            show="*"
        )
        self.pin_entry.pack(pady=(0, 5))

        # Show/Hide PIN Button
        self.show_pin_button = ctk.CTkButton(
            self.main_frame,
            text="Show PIN",
            command=self.toggle_pin_visibility,
            width=150,
            height=35,
            font=("Helvetica", 12),
            fg_color="#666666",
            hover_color="#555555"
        )
        self.show_pin_button.pack(pady=(0, 15))

        # Output Area
        self.output_label = ctk.CTkLabel(
            self.main_frame,
            text="Output:",
            font=("Helvetica", 14, "bold")
        )
        self.output_label.pack(pady=(0, 5))
        self.output_textbox = ctk.CTkTextbox(
            self.main_frame,
            width=400,
            height=150,
            font=("Helvetica", 13),
            state="disabled"
        )
        self.output_textbox.pack(pady=(0, 15))

        # Buttons Frame
        self.buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.buttons_frame.pack(pady=10)

        # Find Passcode Button
        self.get_passcode_button = ctk.CTkButton(
            self.buttons_frame,
            text="Find Passcode",
            command=self.get_passcode,
            width=250,
            height=50,
            font=("Helvetica", 18, "bold"),
            fg_color="#2B7DE9",
            hover_color="#1B6ED9"
        )
        self.get_passcode_button.pack(pady=10)

        # Clear Button
        self.clear_button = ctk.CTkButton(
            self.buttons_frame,
            text="Clear",
            command=self.clear_fields,
            width=150,
            height=40,
            font=("Helvetica", 14),
            fg_color="#666666",
            hover_color="#555555"
        )
        self.clear_button.pack(pady=5)

        # Start VPN status checking
        self.check_vpn_status()
        # Schedule periodic VPN status checks
        self.after(5000, self.schedule_vpn_check)  # Check every 5 seconds

    def display_output(self, message):
        def update_output():
            self.output_textbox.configure(state="normal")
            self.output_textbox.delete("1.0", "end")
            self.output_textbox.insert("end", message)
            self.output_textbox.configure(state="disabled")
            self.output_textbox.see("end")
        
        if threading.current_thread() is threading.main_thread():
            update_output()
        else:
            self.after(0, update_output)

    def toggle_pin_visibility(self):
        if self.pin_entry.cget("show") == "":
            self.pin_entry.configure(show="*")
            self.show_pin_button.configure(text="Show PIN")
        else:
            self.pin_entry.configure(show="")
            self.show_pin_button.configure(text="Hide PIN")

    def run_commands(self):
        try:
            # Get PIN
            pin = self.pin_entry.get().strip()
            if not pin:
                self.display_output("Error: Please enter your PIN")
                return

            # Run mwinit -o headlessly
            self.display_output("Running mwinit -o...")
            
            # Create a temporary file to store the PIN
            pin_file = os.path.join(os.path.expanduser("~"), ".mwinit_pin_temp")
            with open(pin_file, "w") as f:
                f.write(pin)

            mwinit_process = subprocess.Popen(
                ["mwinit", "-o", "-f", pin_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                cwd=os.path.expanduser("~"),
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            stdout, stderr = mwinit_process.communicate()
            
            # Securely delete the temporary PIN file
            if os.path.exists(pin_file):
                os.remove(pin_file)

            if stderr:
                self.display_output(f"Mwinit Error: {stderr.decode()}")
                return
                
            # Get serial and region
            serial = self.serial_entry.get().strip()
            region = self.region_menu.get()
            
            # Now run the get_passcode script
            self.display_output(f"Getting passcode for serial: {serial}, region: {region}")
            
            # Run get_passcode_v2.py
            downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
            process = subprocess.Popen(
                ["python", "get_passcode_v2.py", "-s", serial, "-r", region],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=downloads_path,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            stdout, stderr = process.communicate()
            
            if stderr:
                self.display_output(f"Error: {stderr}")
            else:
                self.display_output(stdout.strip())

        except Exception as e:
            self.display_output(f"Error: {str(e)}")
        finally:
            self.get_passcode_button.configure(state="normal")
            # Ensure PIN file is deleted even if an error occurs
            if os.path.exists(pin_file):
                os.remove(pin_file)

    def get_passcode(self):
        # Disable the button while processing
        self.get_passcode_button.configure(state="disabled")
        
        try:
            serial = self.serial_entry.get().strip()
            if not serial:
                messagebox.showerror("Error", "Please enter a serial number")
                self.get_passcode_button.configure(state="normal")
                return

            # Run commands in a separate thread
            thread = threading.Thread(target=self.run_commands)
            thread.daemon = True
            thread.start()

        except Exception as e:
            self.display_output(f"Error: {str(e)}")
            self.get_passcode_button.configure(state="normal")

    def clear_fields(self):
        """Clear all input fields and output"""
        self.serial_entry.delete(0, 'end')
        self.region_menu.set("us-east-1")
        self.pin_entry.delete(0, 'end')
        self.output_textbox.configure(state="normal")
        self.output_textbox.delete("1.0", "end")
        self.output_textbox.configure(state="disabled")

    def check_vpn_status(self):
        """Check VPN connection status and update the indicator."""
        try:
            is_connected, status = get_cisco_anyconnect_status()
            if is_connected:
                self.vpn_status_label.configure(
                    text="VPN Connected",
                    text_color="green"
                )
                self.vpn_indicator.configure(text_color="green")
            else:
                self.vpn_status_label.configure(
                    text="VPN Disconnected",
                    text_color="red"
                )
                self.vpn_indicator.configure(text_color="red")
        except Exception as e:
            self.vpn_status_label.configure(
                text="VPN Status Error",
                text_color="orange"
            )
            self.vpn_indicator.configure(text_color="orange")
            logging.error(f"Error checking VPN status: {e}")

    def schedule_vpn_check(self):
        """Schedule the next VPN status check."""
        self.check_vpn_status()
        self.after(5000, self.schedule_vpn_check)  # Check every 5 seconds

if __name__ == "__main__":
    app = PasscodeApp()
    app.mainloop()
