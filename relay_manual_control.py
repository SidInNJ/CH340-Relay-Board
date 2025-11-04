"""
Manual Relay Control GUI
Simple interface to control relays 1-4 individually
"""

import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk
import threading
import json
from pathlib import Path

# Auto-install missing modules (pyserial is imported via relay_driver)
# The relay_driver module will handle installing pyserial if needed
from relay_driver import RelayDriver, list_available_ports


class ConfigurationWindow:
    """Configuration window for relay settings"""
    
    def __init__(self, parent, config, on_save_callback, parent_gui=None):
        self.config = config
        self.on_save = on_save_callback
        self.parent_gui = parent_gui
        
        # Create toplevel window
        self.window = tk.Toplevel(parent)
        self.window.title("Relay Configuration")
        self.window.geometry("600x500")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="Relay Board Configuration", 
                 font=('Arial', 14, 'bold')).pack(pady=(0, 10))
        
        # Board type
        type_frame = ttk.LabelFrame(main_frame, text="Board Type", padding="10")
        type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(type_frame, text="Relay Board Type:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.board_type_var = tk.StringVar(value=self.config['hardware']['relay_board_type'])
        board_combo = ttk.Combobox(type_frame, textvariable=self.board_type_var, 
                                   values=['4-relay', '8-relay'], 
                                   state='readonly', width=15)
        board_combo.grid(row=0, column=1, sticky=tk.W, padx=10)
        board_combo.bind('<<ComboboxSelected>>', self.on_board_type_changed)
        
        # Relay names
        names_frame = ttk.LabelFrame(main_frame, text="Relay Names", padding="10")
        names_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Headers
        ttk.Label(names_frame, text="Relay", font=('Arial', 9, 'bold')).grid(
            row=0, column=0, padx=5, pady=5)
        ttk.Label(names_frame, text="Name/Function", font=('Arial', 9, 'bold')).grid(
            row=0, column=1, padx=5, pady=5)
        
        self.relay_name_vars = {}
        self.relay_name_entries = {}
        
        for i in range(1, 9):
            relay_num = i
            ttk.Label(names_frame, text=f"Relay {relay_num}:").grid(
                row=i, column=0, sticky=tk.W, padx=5, pady=2)
            
            name_var = tk.StringVar(value=self.config['hardware'].get(f'relay{relay_num}_function', f'Relay {relay_num}'))
            name_entry = ttk.Entry(names_frame, textvariable=name_var, width=40)
            name_entry.grid(row=i, column=1, padx=5, pady=2)
            
            self.relay_name_vars[relay_num] = name_var
            self.relay_name_entries[relay_num] = name_entry
        
        # Update enabled state based on board type
        self.on_board_type_changed()
        
        # Buttons
        button_frame = ttk.Frame(self.window, padding="10")
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Button(button_frame, text="Save Configuration", 
                  command=self.save_config, width=20).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=self.window.destroy, width=15).pack(side=tk.RIGHT, padx=5)
    
    def on_board_type_changed(self, event=None):
        """Handle relay board type change"""
        relay_count = 4 if self.board_type_var.get() == '4-relay' else 8
        
        for i in range(1, 9):
            if i <= relay_count:
                self.relay_name_entries[i].config(state='normal')
            else:
                self.relay_name_entries[i].config(state='disabled')
                # Restore the original name from config instead of setting to 'Unused'
                original_name = self.config['hardware'].get(f'relay{i}_function', f'Relay {i}')
                self.relay_name_vars[i].set(original_name)
    
    def check_relay_state_compatibility(self):
        """Check if switching board type is safe given current relay states"""
        new_board_type = self.board_type_var.get()
        new_relay_count = 4 if new_board_type == '4-relay' else 8
        
        # If switching to 4-relay, check if any relays 5-8 are on
        if new_relay_count == 4:
            relays_on_in_range = [r for r in range(5, 9) if self.parent_gui.relay_states.get(r, False)]
            if relays_on_in_range:
                result = messagebox.askyesno(
                    "Relays Active",
                    f"Relays {relays_on_in_range} are currently ON.\n\n"
                    "Switching to 4-relay board will turn them off.\n\n"
                    "Continue?"
                )
                if result:
                    # Turn off relays 5-8
                    for relay_num in range(5, 9):
                        try:
                            self.parent_gui.relay_driver.relay_off(relay_num)
                            self.parent_gui.relay_states[relay_num] = False
                        except:
                            pass
                    return True
                else:
                    # Revert selection
                    old_board_type = self.config['hardware']['relay_board_type']
                    self.board_type_var.set(old_board_type)
                    self.on_board_type_changed()
                    return False
        return True
    
    def save_config(self):
        """Save configuration and close window"""
        try:
            # Check relay state compatibility if board type changed
            if self.board_type_var.get() != self.config['hardware']['relay_board_type']:
                if not self.check_relay_state_compatibility():
                    return
            
            # Update hardware section
            new_board_type = self.board_type_var.get()
            self.config['hardware']['relay_board_type'] = new_board_type
            
            # Determine relay count for new board type
            new_relay_count = 4 if new_board_type == '4-relay' else 8
            
            # Only save relay names for relays within the current board type
            # Don't overwrite names for relays beyond the current board type
            for i in range(1, 9):
                if i <= new_relay_count:
                    # Save the name for active relays
                    self.config['hardware'][f'relay{i}_function'] = self.relay_name_vars[i].get()
                # For relays beyond the board type, keep their existing names in config
                # (don't save "Unused" over them)
            
            # Save to file
            with open('config.json', 'w') as f:
                json.dump(self.config, f, indent=2)
            
            messagebox.showinfo("Success", "Configuration saved successfully!")
            
            # Call callback
            if self.on_save:
                self.on_save(self.config)
            
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration:\n{str(e)}")


class RelayManualControlGUI:
    """GUI for manual relay control"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Manual Relay Control")
        
        # Load configuration
        self.config = self.load_config()
        
        # Determine relay count from config
        self.relay_count = 4 if self.config['hardware']['relay_board_type'] == '4-relay' else 8
        
        # Set window size based on relay count
        height = 250 + (self.relay_count * 35)
        self.root.geometry(f"500x{height}")
        
        self.relay_driver = None
        self.relay_states = {i: False for i in range(1, self.relay_count + 1)}
        
        self._setup_ui()
        self._connect_relay()
    
    def load_config(self):
        """Load configuration from JSON file"""
        config_path = Path("config.json")
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            # Default config if file doesn't exist
            return {
                'hardware': {
                    'relay_board_type': '4-relay',
                    'relay1_function': 'Relay 1',
                    'relay2_function': 'Relay 2',
                    'relay3_function': 'Relay 3',
                    'relay4_function': 'Relay 4',
                    'relay5_function': 'Relay 5',
                    'relay6_function': 'Relay 6',
                    'relay7_function': 'Relay 7',
                    'relay8_function': 'Relay 8',
                }
            }
        
    def _setup_ui(self):
        """Setup user interface"""
        # Clear any existing widgets first
        for widget in self.root.winfo_children():
            widget.destroy()
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Manual Relay Control",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 10))
        
        # Board info
        board_info_text = f"Board Type: {self.config['hardware']['relay_board_type'].upper()} ({self.relay_count} relays)"
        board_info_label = ttk.Label(
            main_frame,
            text=board_info_text,
            font=("Arial", 9)
        )
        board_info_label.grid(row=1, column=0, columnspan=4, pady=(0, 5))
        
        # Connection status
        self.status_label = tk.Label(
            main_frame,
            text="DISCONNECTED",
            font=("Arial", 10, "bold"),
            fg="gray"
        )
        self.status_label.grid(row=2, column=0, columnspan=4, pady=(0, 10))
        
        # Headers
        ttk.Label(main_frame, text="Relay", font=("Arial", 10, "bold")).grid(
            row=3, column=0, padx=5, pady=5
        )
        ttk.Label(main_frame, text="State", font=("Arial", 10, "bold")).grid(
            row=3, column=1, padx=5, pady=5
        )
        ttk.Label(main_frame, text="Control", font=("Arial", 10, "bold")).grid(
            row=3, column=2, columnspan=2, padx=5, pady=5
        )
        
        # Create relay controls
        self.state_labels = {}
        self.on_buttons = {}
        self.off_buttons = {}
        
        for relay_num in range(1, self.relay_count + 1):
            row = relay_num + 3
            
            # Get relay name from config
            relay_name = self.config['hardware'].get(f'relay{relay_num}_function', f'Relay {relay_num}')
            
            # Relay label with name
            ttk.Label(
                main_frame,
                text=f"{relay_name}",
                font=("Arial", 10)
            ).grid(row=row, column=0, padx=5, pady=3, sticky=tk.W)
            
            # State indicator
            self.state_labels[relay_num] = tk.Label(
                main_frame,
                text="OFF",
                font=("Arial", 10, "bold"),
                fg="red",
                width=8
            )
            self.state_labels[relay_num].grid(row=row, column=1, padx=5, pady=3)
            
            # ON button
            self.on_buttons[relay_num] = ttk.Button(
                main_frame,
                text="ON",
                width=8,
                command=lambda r=relay_num: self._turn_on_relay(r)
            )
            self.on_buttons[relay_num].grid(row=row, column=2, padx=2, pady=3)
            
            # OFF button
            self.off_buttons[relay_num] = ttk.Button(
                main_frame,
                text="OFF",
                width=8,
                command=lambda r=relay_num: self._turn_off_relay(r)
            )
            self.off_buttons[relay_num].grid(row=row, column=3, padx=2, pady=3)
        
        # Bottom buttons frame
        bottom_row = self.relay_count + 4
        
        # All Off button
        all_off_btn = ttk.Button(
            main_frame,
            text="ALL OFF",
            command=self._all_off,
            style="Danger.TButton"
        )
        all_off_btn.grid(row=bottom_row, column=0, columnspan=2, pady=(15, 5), sticky=(tk.W, tk.E), padx=5)
        
        # Configuration button
        config_btn = ttk.Button(
            main_frame,
            text="⚙ Configuration",
            command=self.open_configuration,
            width=20
        )
        config_btn.grid(row=bottom_row, column=2, columnspan=2, pady=(15, 5), sticky=(tk.W, tk.E), padx=5)
        
        # Configure styles
        style = ttk.Style()
        style.configure("Danger.TButton", foreground="red", font=("Arial", 10, "bold"))
    
    def open_configuration(self):
        """Open configuration window"""
        ConfigurationWindow(self.root, self.config, self.on_config_saved, parent_gui=self)
    
    def on_config_saved(self, new_config):
        """Handle configuration save and refresh GUI"""
        self.config = new_config
        self.refresh_gui()
        messagebox.showinfo("Success", "Configuration updated successfully!")
    
    def refresh_gui(self):
        """Refresh GUI with new configuration"""
        # Check if relay count changed
        new_relay_count = 4 if self.config['hardware']['relay_board_type'] == '4-relay' else 8
        
        if new_relay_count != self.relay_count:
            # Relay count changed, need to rebuild UI
            # Preserve relay states for relays that will still exist
            old_relay_states = self.relay_states.copy()
            self.relay_count = new_relay_count
            
            # Disconnect from relay board if connected
            if self.relay_driver:
                try:
                    self.relay_driver.disconnect()
                except:
                    pass
            
            # Clear old widgets
            for widget in self.root.winfo_children():
                widget.destroy()
            
            # Rebuild UI with preserved states
            self.relay_states = {}
            for i in range(1, self.relay_count + 1):
                # Preserve state if it existed before, otherwise default to False
                self.relay_states[i] = old_relay_states.get(i, False)
            
            self._setup_ui()
            self._connect_relay()
            
            # Update relay state indicators to show current states
            self._update_relay_indicators()
        else:
            # Only relay names changed, update labels
            for relay_num in range(1, self.relay_count + 1):
                relay_name = self.config['hardware'].get(f'relay{relay_num}_function', f'Relay {relay_num}')
                # Find and update the label widget for this relay
                # The label is in the main frame at row (relay_num + 3), column 0
                main_frame = self.root.winfo_children()[0]
                label_widget = main_frame.grid_slaves(row=relay_num + 3, column=0)[0]
                label_widget.config(text=relay_name)
    
    def _update_relay_indicators(self):
        """Update relay state indicators to show current on/off status"""
        for relay_num in range(1, self.relay_count + 1):
            if self.relay_states.get(relay_num, False):
                self.state_labels[relay_num].config(text="ON", fg="green")
            else:
                self.state_labels[relay_num].config(text="OFF", fg="red")
        
    def _connect_relay(self):
        """Connect to relay board"""
        try:
            self.relay_driver = RelayDriver(auto_connect=True)
            self.status_label.config(text="CONNECTED", fg="green")
            self._enable_controls(True)
        except Exception as e:
            self.status_label.config(text="CONNECTION FAILED", fg="red")
            messagebox.showerror(
                "Connection Error",
                f"Failed to connect to relay board:\n{str(e)}\n\nAvailable ports:\n" +
                "\n".join(list_available_ports())
            )
            self._enable_controls(False)
    
    def _enable_controls(self, enabled: bool):
        """Enable or disable relay controls"""
        state = "normal" if enabled else "disabled"
        for relay_num in range(1, self.relay_count + 1):
            self.on_buttons[relay_num].config(state=state)
            self.off_buttons[relay_num].config(state=state)
    
    def _turn_on_relay(self, relay_num: int):
        """Turn on specified relay"""
        if not self.relay_driver:
            messagebox.showerror("Error", "Not connected to relay board")
            return
        
        try:
            self.relay_driver.relay_on(relay_num)
            self.relay_states[relay_num] = True
            self.state_labels[relay_num].config(text="ON", fg="green")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to turn on relay {relay_num}:\n{str(e)}")
    
    def _turn_off_relay(self, relay_num: int):
        """Turn off specified relay"""
        if not self.relay_driver:
            messagebox.showerror("Error", "Not connected to relay board")
            return
        
        try:
            self.relay_driver.relay_off(relay_num)
            self.relay_states[relay_num] = False
            self.state_labels[relay_num].config(text="OFF", fg="red")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to turn off relay {relay_num}:\n{str(e)}")
    
    def _all_off(self):
        """Turn off all relays"""
        if not self.relay_driver:
            messagebox.showerror("Error", "Not connected to relay board")
            return
        
        try:
            # Turn off each relay individually to ensure all are off
            for relay_num in range(1, self.relay_count + 1):
                self.relay_driver.relay_off(relay_num)
                self.relay_states[relay_num] = False
                self.state_labels[relay_num].config(text="OFF", fg="red")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to turn off relays:\n{str(e)}")
    
    def _on_closing(self):
        """Handle window closing"""
        if self.relay_driver:
            try:
                # Safety: Turn off all relays before closing
                self.relay_driver.all_off()
            except:
                pass
            self.relay_driver.disconnect()
        self.root.destroy()
    
    def run(self):
        """Run the GUI"""
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.mainloop()


def main():
    """Main entry point"""
    app = RelayManualControlGUI()
    app.run()


if __name__ == "__main__":
    main()
