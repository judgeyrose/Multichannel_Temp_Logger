import serial
import serial.tools.list_ports
import time
import csv
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import queue
from enum import Enum

class ConnectionState(Enum):
    """Connection state enumeration"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    LOGGING = "logging"

class MultiChannelLoggerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Channel Thermocouple Logger")
        self.root.geometry("1400x900")
        
        # Serial connection variables
        self.serial_connection = None
        self.connection_state = ConnectionState.DISCONNECTED
        self.is_logging = False
        self.data_queue = queue.Queue()
        self.connection_lock = threading.Lock()  # Thread-safe connection operations
        
        # Logger configuration variables
        self.sample_rate = 1  # Default 1 second
        self.num_channels = 3  # Default 3 channels
        self.num_samples = 10   # Default 10 samples per interval
        
        # Save folder configuration
        self.save_folder = "Results"  # Default save folder
        
        # Data storage for plotting
        self.timestamps = []
        self.temp_data = [[], [], [], [], [], [], [], [], [], [], [], []]  # 12 channels max
        # Performance configuration
        # Increase this value for longer logging sessions, but be aware of memory usage
        # 10,000 points = ~2.8 hours at 1s intervals, ~28 hours at 10s intervals
        # 100,000 points = ~28 hours at 1s intervals, ~11.6 days at 10s intervals
        self.max_data_points = 50000  # Limit data points for performance (~13 hrs @ 1s intervals, 5 days @ 10s intervals)
        
        # GUI setup
        self.setup_gui()
        self.update_com_ports()
        
        # Start data processing thread
        self.data_thread = threading.Thread(target=self.process_data, daemon=True)
        self.data_thread.start()
        
        # Start plot update
        self.update_plot()
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_gui(self):
        # Create menu bar
        self.create_menu()
        
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Connection Settings Frame
        connection_frame = ttk.LabelFrame(main_frame, text="Connection Settings", padding="5")
        connection_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # COM Port selection
        ttk.Label(connection_frame, text="COM Port:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.com_port_var = tk.StringVar()
        self.com_port_combo = ttk.Combobox(connection_frame, textvariable=self.com_port_var, width=15)
        self.com_port_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        # Refresh button
        ttk.Button(connection_frame, text="Refresh Ports", command=self.update_com_ports).grid(row=0, column=2, padx=(0, 10))
        
        # Test connection button
        self.test_button = ttk.Button(connection_frame, text="Test Connection", command=self.test_connection)
        self.test_button.grid(row=0, column=3, padx=(0, 10))
        
        # Connection status
        self.connection_status = ttk.Label(connection_frame, text="Not Connected", foreground="red")
        self.connection_status.grid(row=0, column=4, padx=(10, 0))
        
        # Connect/Disconnect button
        self.connect_button = ttk.Button(connection_frame, text="Connect", command=self.toggle_connection)
        self.connect_button.grid(row=0, column=5, padx=(10, 0))
        
        # Logger Configuration Frame
        config_frame = ttk.LabelFrame(main_frame, text="Logger Configuration", padding="5")
        config_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Sample Rate configuration
        ttk.Label(config_frame, text="Sample Rate (1-255 sec):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.rate_var = tk.StringVar(value="1")
        self.rate_entry = ttk.Entry(config_frame, textvariable=self.rate_var, width=10)
        self.rate_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        self.rate_button = ttk.Button(config_frame, text="Set Rate", command=self.set_sample_rate)
        self.rate_button.grid(row=0, column=2, padx=(0, 10))
        
        # Number of Channels configuration
        ttk.Label(config_frame, text="Channels (1-12):").grid(row=0, column=3, sticky=tk.W, padx=(10, 5))
        self.channels_var = tk.StringVar(value="3")
        self.channels_entry = ttk.Entry(config_frame, textvariable=self.channels_var, width=10)
        self.channels_entry.grid(row=0, column=4, sticky=tk.W, padx=(0, 10))
        self.channels_button = ttk.Button(config_frame, text="Set Channels", command=self.set_channels)
        self.channels_button.grid(row=0, column=5, padx=(0, 10))
        
        # Number of Samples configuration
        ttk.Label(config_frame, text="Samples (1-20):").grid(row=0, column=6, sticky=tk.W, padx=(10, 5))
        self.samples_var = tk.StringVar(value="10")
        self.samples_entry = ttk.Entry(config_frame, textvariable=self.samples_var, width=10)
        self.samples_entry.grid(row=0, column=7, sticky=tk.W, padx=(0, 10))
        self.samples_button = ttk.Button(config_frame, text="Set Samples", command=self.set_samples)
        self.samples_button.grid(row=0, column=8, padx=(0, 10))
        
        # Acquire button
        self.acquire_button = ttk.Button(config_frame, text="Acquire Data", command=self.acquire_data)
        self.acquire_button.grid(row=0, column=9, padx=(10, 0))
        
        # Logging Settings Frame
        logging_frame = ttk.LabelFrame(main_frame, text="Logging Settings", padding="5")
        logging_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        logging_frame.columnconfigure(1, weight=1)  # Allow entry fields to expand
        
        # Save folder configuration
        ttk.Label(logging_frame, text="Save Folder:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.save_folder_var = tk.StringVar(value="Results")
        self.save_folder_entry = ttk.Entry(logging_frame, textvariable=self.save_folder_var, width=40)
        self.save_folder_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Browse folder button
        ttk.Button(logging_frame, text="Browse", command=self.browse_save_folder).grid(row=0, column=2, padx=(0, 10))
        
        # Filename configuration
        ttk.Label(logging_frame, text="Filename:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        self.filename_var = tk.StringVar()
        self.filename_entry = ttk.Entry(logging_frame, textvariable=self.filename_var, width=40)
        self.filename_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(5, 0))
        
        # Auto-fill filename button (aligned with Browse button)
        ttk.Button(logging_frame, text="Auto-fill", command=self.auto_fill_filename).grid(row=1, column=2, pady=(5, 0))
        
        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Start/Stop button
        self.start_stop_button = ttk.Button(control_frame, text="Start Logging", command=self.toggle_logging)
        self.start_stop_button.grid(row=0, column=0, padx=(0, 10))
        
        # Clear plot button
        ttk.Button(control_frame, text="Clear Plot", command=self.clear_plot).grid(row=0, column=1, padx=(0, 10))
        
        # Save plot button
        ttk.Button(control_frame, text="Save Plot", command=self.save_plot).grid(row=0, column=2, padx=(0, 10))
        
        # Export data button
        ttk.Button(control_frame, text="Export Data", command=self.export_data).grid(row=0, column=3, padx=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(control_frame, text="Ready")
        self.status_label.grid(row=0, column=4, padx=(10, 0))
        
        # Plot frame
        plot_frame = ttk.LabelFrame(main_frame, text="Real-time Temperature Plot", padding="5")
        plot_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(0, weight=1)
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(14, 7), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, plot_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Setup plot
        self.setup_plot()
        
        # Initialize save folder
        import os
        if not os.path.exists(self.save_folder):
            os.makedirs(self.save_folder)
        
        # Auto-fill filename on startup
        self.auto_fill_filename()
        
        # Initialize UI state based on connection
        self.update_ui_state()
    
    def create_menu(self):
        """Create the application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Plot", command=self.save_plot)
        file_menu.add_command(label="Export Data", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Data menu
        data_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Data", menu=data_menu)
        data_menu.add_command(label="Clear Plot", command=self.clear_plot)
        data_menu.add_command(label="Save Plot", command=self.save_plot)
        data_menu.add_separator()
        data_menu.add_command(label="Export as CSV", command=lambda: self._export_to_csv_direct())
        data_menu.add_command(label="Export as Excel", command=lambda: self._export_to_excel_direct())
        data_menu.add_command(label="Export as JSON", command=lambda: self._export_to_json_direct())
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def _export_to_csv_direct(self):
        """Export data directly to CSV with default filename"""
        if not self.timestamps:
            messagebox.showwarning("Warning", "No data to export. Start logging first.")
            return
        
        import os
        
        # Get save folder
        save_folder = self.get_save_folder()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"temperature_data_{timestamp}.csv"
        filepath = os.path.join(save_folder, filename)
        self._export_to_csv(filepath)
        messagebox.showinfo("Success", f"Data exported to: {save_folder}/{filename}")
    
    def _export_to_excel_direct(self):
        """Export data directly to Excel with default filename"""
        if not self.timestamps:
            messagebox.showwarning("Warning", "No data to export. Start logging first.")
            return
        
        import os
        
        # Get save folder
        save_folder = self.get_save_folder()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"temperature_data_{timestamp}.xlsx"
        filepath = os.path.join(save_folder, filename)
        self._export_to_excel(filepath)
        messagebox.showinfo("Success", f"Data exported to: {save_folder}/{filename}")
    
    def _export_to_json_direct(self):
        """Export data directly to JSON with default filename"""
        if not self.timestamps:
            messagebox.showwarning("Warning", "No data to export. Start logging first.")
            return
        
        import os
        
        # Get save folder
        save_folder = self.get_save_folder()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"temperature_data_{timestamp}.json"
        filepath = os.path.join(save_folder, filename)
        self._export_to_json(filepath)
        messagebox.showinfo("Success", f"Data exported to: {save_folder}/{filename}")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """Multi-Channel Thermocouple Logger

A Python application for logging temperature data from multiple thermocouple channels via Arduino with real-time plotting capabilities.

Features:
• Real-time temperature plotting
• Multi-format data export (CSV, Excel, JSON)
• Plot saving in multiple formats
• COM port configuration and testing
• Professional GUI interface

Version: 2.0
Author: Multi-Channel Logger Team"""
        
        messagebox.showinfo("About", about_text)
    
    def setup_plot(self):
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Temperature (°C)')
        self.ax.set_title('Real-time Temperature Data')
        self.ax.grid(True, alpha=0.3)
        
        # Create line objects for each channel
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan', 'magenta', 'yellow']
        self.lines = []
        for i in range(12):  # Support up to 12 channels
            line, = self.ax.plot([], [], color=colors[i % len(colors)], label=f'Channel {i+1}', linewidth=2)
            self.lines.append(line)
        
        self.ax.legend()
        self.fig.tight_layout()
    
    def is_connected(self):
        """Check if device is connected and connection is valid"""
        with self.connection_lock:
            return (self.connection_state in [ConnectionState.CONNECTED, ConnectionState.LOGGING] and
                    self.serial_connection is not None and
                    self.serial_connection.is_open)
    
    def validate_connection(self, show_error=True):
        """Validate that device is connected before operations"""
        if not self.is_connected():
            if show_error:
                messagebox.showerror("Not Connected", 
                    "Device is not connected. Please connect to the device first.")
            return False
        return True
    
    def send_serial_command(self, command, use_existing_connection=True, timeout=3.0):
        """Send a command to the logger device and return the response with robust error handling"""
        temp_connection = None
        
        # Validate connection if using existing connection
        if use_existing_connection:
            if not self.validate_connection(show_error=False):
                return None
        
        try:
            # Use existing connection if available and requested
            if use_existing_connection and self.serial_connection and self.serial_connection.is_open:
                connection = self.serial_connection
            else:
                # Create temporary connection for configuration commands
                port = self.com_port_var.get()
                if not port:
                    if not use_existing_connection:  # Only show error for explicit temp connections
                        messagebox.showerror("Error", "Please select a COM port")
                    return None
                
                try:
                    temp_connection = serial.Serial(port, 9600, timeout=1)
                    time.sleep(0.5)  # Give Arduino time to reset
                    connection = temp_connection
                except serial.SerialException as e:
                    if not use_existing_connection:
                        messagebox.showerror("Connection Error", 
                            f"Failed to connect to {port}:\n{str(e)}\n\n"
                            f"Please ensure the device is connected and the correct COM port is selected.")
                    return None
                except Exception as e:
                    if not use_existing_connection:
                        messagebox.showerror("Connection Error", f"Failed to connect to {port}: {str(e)}")
                    return None
            
            # Check if connection is still valid
            if not connection.is_open:
                if not use_existing_connection:
                    messagebox.showerror("Connection Error", "Connection is not open")
                return None
            
            # Send command with newline
            try:
                connection.write(f"{command}\n".encode('utf-8'))
                connection.flush()
            except (serial.SerialTimeoutException, serial.SerialException, OSError) as e:
                if not use_existing_connection:
                    messagebox.showerror("Serial Error", 
                        f"Failed to send command:\n{str(e)}\n\n"
                        f"The device may have been disconnected.")
                # Update connection state if using existing connection
                if use_existing_connection:
                    self.set_connection_state(ConnectionState.ERROR)
                return None
            
            # Wait for response with timeout
            time.sleep(0.1)
            
            # Read response with proper timeout handling
            response = ""
            start_time = time.time()
            timeout_end = start_time + timeout
            
            while time.time() < timeout_end:
                try:
                    if connection.in_waiting:
                        line = connection.readline().decode('utf-8', errors='ignore').strip()
                        if line:
                            response += line + "\n"
                            # Check for completion markers
                            if line.endswith("OK") or line.endswith("ERROR") or "ERROR:" in line:
                                break
                    time.sleep(0.01)
                except (serial.SerialException, OSError, UnicodeDecodeError) as e:
                    if not use_existing_connection:
                        messagebox.showerror("Serial Error", 
                            f"Error reading response:\n{str(e)}\n\n"
                            f"The device may have been disconnected.")
                    if use_existing_connection:
                        self.set_connection_state(ConnectionState.ERROR)
                    return None
            
            # Check if we got a timeout
            if not response and time.time() >= timeout_end:
                if not use_existing_connection:
                    messagebox.showwarning("Timeout", 
                        f"No response received from device within {timeout} seconds.\n\n"
                        f"Command: {command}\n"
                        f"Please check the device connection and try again.")
                return None
            
            return response.strip() if response else None
            
        except Exception as e:
            if not use_existing_connection:
                messagebox.showerror("Serial Error", 
                    f"Unexpected error sending command:\n{str(e)}")
            if use_existing_connection:
                self.set_connection_state(ConnectionState.ERROR)
            return None
        finally:
            # Close temporary connection if we created one
            if temp_connection and temp_connection.is_open:
                try:
                    temp_connection.close()
                except:
                    pass
    
    def set_sample_rate(self):
        """Set the sample rate on the logger device"""
        if not self.validate_connection():
            return
        
        try:
            rate = int(self.rate_var.get())
            if rate < 1 or rate > 255:
                messagebox.showerror("Error", "Sample rate must be between 1 and 255 seconds")
                return
            
            response = self.send_serial_command(f"RATE {rate}", use_existing_connection=True)
            if response:
                if "OK" in response:
                    self.sample_rate = rate
                    messagebox.showinfo("Success", f"Sample rate set to {rate} seconds")
                    self.status_label.config(text=f"Rate: {rate}s")
                else:
                    messagebox.showerror("Error", f"Failed to set sample rate: {response}")
            else:
                messagebox.showerror("Error", "No response from device")
                
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for sample rate")
    
    def set_channels(self):
        """Set the number of channels on the logger device"""
        if not self.validate_connection():
            return
        
        try:
            channels = int(self.channels_var.get())
            if channels < 1 or channels > 12:
                messagebox.showerror("Error", "Number of channels must be between 1 and 12")
                return
            
            response = self.send_serial_command(f"CHANNELS {channels}", use_existing_connection=True)
            if response:
                if "OK" in response:
                    self.num_channels = channels
                    messagebox.showinfo("Success", f"Number of channels set to {channels}")
                    self.status_label.config(text=f"Channels: {channels}")
                else:
                    messagebox.showerror("Error", f"Failed to set channels: {response}")
            else:
                messagebox.showerror("Error", "No response from device")
                
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for channels")
    
    def set_samples(self):
        """Set the number of samples to average on the logger device"""
        if not self.validate_connection():
            return
        
        try:
            samples = int(self.samples_var.get())
            if samples < 1 or samples > 20:
                messagebox.showerror("Error", "Number of samples must be between 1 and 20")
                return
            
            response = self.send_serial_command(f"SAMPLES {samples}", use_existing_connection=True)
            if response:
                if "OK" in response:
                    self.num_samples = samples
                    messagebox.showinfo("Success", f"Number of samples set to {samples}")
                    self.status_label.config(text=f"Samples: {samples}")
                else:
                    messagebox.showerror("Error", f"Failed to set samples: {response}")
            else:
                messagebox.showerror("Error", "No response from device")
                
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for samples")
    
    def acquire_data(self):
        """Acquire a single reading from the logger device"""
        if not self.validate_connection():
            return
        
        response = self.send_serial_command("ACQUIRE", use_existing_connection=True)
        if response:
            if "ERROR" in response:
                messagebox.showerror("Error", f"Acquire failed: {response}")
            else:
                # Parse the response for temperature values
                try:
                    # Expected format: "TEMP: val1,val2,val3,..." or similar
                    if "TEMP:" in response or "DATA:" in response:
                        # Extract temperature values
                        parts = response.split(":")
                        if len(parts) > 1:
                            temp_str = parts[1].strip()
                            temp_values = [float(x.strip()) for x in temp_str.split(",")]
                            
                            # Update plot data
                            timestamp = datetime.now()
                            self.timestamps.append(timestamp)
                            
                            # Ensure we have enough channels
                            while len(self.temp_data) < len(temp_values):
                                self.temp_data.append([])
                            
                            # Add temperature values
                            for i, temp in enumerate(temp_values):
                                if i < len(self.temp_data):
                                    self.temp_data[i].append(temp)
                            
                            # Limit data points (optimized for larger datasets)
                            if len(self.timestamps) > self.max_data_points:
                                # Remove oldest 10% of data points for efficiency
                                remove_count = max(1, self.max_data_points // 10)
                                self.timestamps = self.timestamps[remove_count:]
                                for i, data in enumerate(self.temp_data):
                                    if data:
                                        self.temp_data[i] = data[remove_count:]
                            
                            messagebox.showinfo("Acquire Success", 
                                f"Acquired {len(temp_values)} temperature readings:\n" + 
                                "\n".join([f"Channel {i+1}: {temp:.2f}°C" for i, temp in enumerate(temp_values)]))
                            
                            self.status_label.config(text=f"Last Acquire: {len(temp_values)} channels")
                        else:
                            messagebox.showinfo("Acquire Response", response)
                    else:
                        messagebox.showinfo("Acquire Response", response)
                        
                except Exception as e:
                    messagebox.showinfo("Acquire Response", f"Response: {response}\nParse error: {str(e)}")
        else:
            messagebox.showerror("Error", "No response from device")
    
    def set_connection_state(self, state):
        """Update connection state and UI"""
        with self.connection_lock:
            self.connection_state = state
        self.root.after(0, self.update_ui_state)
    
    def update_ui_state(self):
        """Update UI elements based on connection state"""
        is_connected = self.is_connected()
        is_logging = self.is_logging
        
        # Update connection status label
        if self.connection_state == ConnectionState.CONNECTED:
            self.connection_status.config(text="Connected", foreground="green")
            self.connect_button.config(text="Disconnect", state="normal")
        elif self.connection_state == ConnectionState.LOGGING:
            self.connection_status.config(text="Logging", foreground="blue")
            self.connect_button.config(text="Disconnect", state="normal")
        elif self.connection_state == ConnectionState.CONNECTING:
            self.connection_status.config(text="Connecting...", foreground="orange")
            self.connect_button.config(text="Connecting...", state="disabled")
        elif self.connection_state == ConnectionState.ERROR:
            self.connection_status.config(text="Connection Error", foreground="red")
            self.connect_button.config(text="Connect", state="normal")
        else:  # DISCONNECTED
            self.connection_status.config(text="Not Connected", foreground="red")
            self.connect_button.config(text="Connect", state="normal")
        
        # Enable/disable controls based on connection state
        # Configuration controls - only enabled when connected but not logging
        config_enabled = is_connected and not is_logging
        
        # Update entry fields
        entry_state = "normal" if config_enabled else "disabled"
        self.rate_entry.config(state=entry_state)
        self.channels_entry.config(state=entry_state)
        self.samples_entry.config(state=entry_state)
        
        # Update configuration buttons
        button_state = "normal" if config_enabled else "disabled"
        if hasattr(self, 'rate_button'):
            self.rate_button.config(state=button_state)
        if hasattr(self, 'channels_button'):
            self.channels_button.config(state=button_state)
        if hasattr(self, 'samples_button'):
            self.samples_button.config(state=button_state)
        if hasattr(self, 'acquire_button'):
            self.acquire_button.config(state=button_state)
        
        # COM port selection - disabled when connected
        self.com_port_combo.config(state="readonly" if not is_connected else "disabled")
        
        # Test connection button - only when not connected
        if hasattr(self, 'test_button'):
            self.test_button.config(state="normal" if not is_connected else "disabled")
        
        # Start/Stop logging button - enabled when connected (or when logging to allow stop)
        if hasattr(self, 'start_stop_button'):
            if is_logging:
                self.start_stop_button.config(state="normal", text="Stop Logging")
            elif is_connected:
                self.start_stop_button.config(state="normal", text="Start Logging")
            else:
                self.start_stop_button.config(state="disabled", text="Start Logging")
    
    def toggle_connection(self):
        """Connect or disconnect from the device"""
        if self.is_connected():
            self.disconnect_device()
        else:
            self.connect_device()
    
    def connect_device(self):
        """Establish connection to the device"""
        port = self.com_port_var.get()
        if not port:
            messagebox.showerror("Error", "Please select a COM port")
            return
        
        if self.is_connected():
            messagebox.showinfo("Info", "Already connected to device")
            return
        
        self.set_connection_state(ConnectionState.CONNECTING)
        
        try:
            # Try to open connection in a separate thread to avoid blocking UI
            def connect_thread():
                try:
                    with self.connection_lock:
                        if self.serial_connection and self.serial_connection.is_open:
                            self.serial_connection.close()
                        
                        self.serial_connection = serial.Serial(port, 9600, timeout=1)
                        time.sleep(2)  # Give Arduino time to reset
                    
                    # Test the connection
                    test_response = self.send_serial_command("RATE", use_existing_connection=True, timeout=2.0)
                    
                    if test_response is not None:
                        self.set_connection_state(ConnectionState.CONNECTED)
                        self.root.after(0, lambda: messagebox.showinfo("Success", 
                            f"Successfully connected to {port}"))
                    else:
                        # Connection opened but no response
                        with self.connection_lock:
                            if self.serial_connection:
                                self.serial_connection.close()
                                self.serial_connection = None
                        self.set_connection_state(ConnectionState.ERROR)
                        self.root.after(0, lambda: messagebox.showwarning("Warning", 
                            f"Connected to {port} but device did not respond.\n"
                            f"Please check the device and try again."))
                
                except serial.SerialException as e:
                    with self.connection_lock:
                        if self.serial_connection:
                            try:
                                self.serial_connection.close()
                            except:
                                pass
                            self.serial_connection = None
                    self.set_connection_state(ConnectionState.ERROR)
                    self.root.after(0, lambda: messagebox.showerror("Connection Error", 
                        f"Failed to connect to {port}:\n{str(e)}\n\n"
                        f"Please ensure:\n"
                        f"- The device is powered on\n"
                        f"- The correct COM port is selected\n"
                        f"- No other program is using the port"))
                except Exception as e:
                    with self.connection_lock:
                        if self.serial_connection:
                            try:
                                self.serial_connection.close()
                            except:
                                pass
                            self.serial_connection = None
                    self.set_connection_state(ConnectionState.ERROR)
                    self.root.after(0, lambda: messagebox.showerror("Connection Error", 
                        f"Unexpected error connecting to device:\n{str(e)}"))
            
            threading.Thread(target=connect_thread, daemon=True).start()
        
        except Exception as e:
            self.set_connection_state(ConnectionState.ERROR)
            messagebox.showerror("Connection Error", f"Failed to initiate connection: {str(e)}")
    
    def disconnect_device(self):
        """Disconnect from the device"""
        if self.is_logging:
            result = messagebox.askyesno("Logging Active", 
                "Logging is currently active. Stop logging before disconnecting?\n\n"
                "Click Yes to stop logging and disconnect, or No to cancel.")
            if result:
                self.stop_logging()
            else:
                return
        
        with self.connection_lock:
            if self.serial_connection and self.serial_connection.is_open:
                try:
                    self.serial_connection.close()
                except:
                    pass
            self.serial_connection = None
        
        self.set_connection_state(ConnectionState.DISCONNECTED)
        messagebox.showinfo("Disconnected", "Disconnected from device")
    
    def update_com_ports(self):
        """Update the list of available COM ports"""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.com_port_combo['values'] = ports
        if ports and not self.com_port_var.get():
            self.com_port_combo.set(ports[0])
    
    def test_connection(self):
        """Test the serial connection"""
        if self.is_connected():
            messagebox.showinfo("Info", "Already connected to device. Use 'Connect' button to manage connection.")
            return
        
        port = self.com_port_var.get()
        if not port:
            messagebox.showerror("Error", "Please select a COM port")
            return
        
        try:
            # Try to open connection
            test_ser = serial.Serial(port, 9600, timeout=1)
            time.sleep(2)  # Give Arduino time to reset
            
            # Send a simple command to test response
            test_ser.write("RATE\n".encode('utf-8'))
            test_ser.flush()
            time.sleep(0.5)
            
            # Try to read response
            response = ""
            timeout = time.time() + 2.0
            
            while time.time() < timeout:
                if test_ser.in_waiting:
                    line = test_ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        response += line + "\n"
                        if "RATE" in line or "OK" in line or "ERROR" in line:
                            break
                time.sleep(0.01)
            
            test_ser.close()
            
            if response.strip():
                messagebox.showinfo("Success", 
                    f"Connection test successful!\n\n"
                    f"Port: {port}\n"
                    f"Device responded: {response.strip()}\n\n"
                    f"Click 'Connect' to establish a persistent connection.")
            else:
                messagebox.showwarning("Warning", 
                    f"Connected to {port} but no response received.\n\n"
                    f"Please check:\n"
                    f"- Device is powered on\n"
                    f"- Correct COM port selected\n"
                    f"- Device firmware is running")
            
        except serial.SerialException as e:
            messagebox.showerror("Connection Error", 
                f"Failed to connect to {port}:\n{str(e)}\n\n"
                f"Please ensure:\n"
                f"- The device is powered on\n"
                f"- The correct COM port is selected\n"
                f"- No other program is using the port")
        except Exception as e:
            messagebox.showerror("Connection Error", f"Unexpected error: {str(e)}")
    
    def get_save_folder(self):
        """Get the current save folder, creating it if it doesn't exist"""
        import os
        
        # Get folder from entry or use default
        folder = self.save_folder_var.get().strip()
        if not folder:
            folder = "Results"
            self.save_folder_var.set(folder)
        
        # Create folder if it doesn't exist
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create save folder:\n{str(e)}")
                # Fall back to default
                folder = "Results"
                self.save_folder_var.set(folder)
                if not os.path.exists(folder):
                    os.makedirs(folder)
        
        self.save_folder = folder
        return folder
    
    def browse_save_folder(self):
        """Open folder dialog to select save directory"""
        import os
        
        # Get current folder or use default
        current_folder = self.save_folder_var.get().strip()
        if not current_folder or not os.path.exists(current_folder):
            current_folder = os.path.abspath("Results")
            if not os.path.exists(current_folder):
                current_folder = os.getcwd()
        
        # Open folder selection dialog
        folder = filedialog.askdirectory(
            title="Select Save Folder",
            initialdir=current_folder
        )
        
        if folder:
            # Normalize the path
            folder = os.path.normpath(folder)
            self.save_folder_var.set(folder)
            self.save_folder = folder
            
            # Update filename if it exists to use new folder
            current_filename = self.filename_var.get()
            if current_filename:
                # Extract just the filename from the path
                filename_only = os.path.basename(current_filename)
                new_path = os.path.join(folder, filename_only)
                self.filename_var.set(new_path)
    
    def auto_fill_filename(self):
        """Auto-fill filename with timestamp"""
        import os
        
        # Get save folder
        save_folder = self.get_save_folder()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(save_folder, f"thermocouple_data_{timestamp}.csv")
        self.filename_var.set(filename)
    
    def browse_filename(self):
        """Open file dialog to select save location"""
        import os
        
        # Get save folder
        save_folder = self.get_save_folder()
        
        # Get current filename if set
        current_filename = self.filename_var.get()
        initial_value = current_filename if current_filename else ""
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=save_folder,
            initialvalue=initial_value
        )
        if filename:
            self.filename_var.set(filename)
            # Update save folder to match the selected file's directory
            file_folder = os.path.dirname(filename)
            if file_folder:
                self.save_folder_var.set(file_folder)
                self.save_folder = file_folder
    
    def toggle_logging(self):
        """Start or stop logging"""
        if not self.is_logging:
            self.start_logging()
        else:
            self.stop_logging()
    
    def start_logging(self):
        """Start the logging process"""
        if not self.validate_connection():
            return
        
        filename = self.filename_var.get()
        if not filename:
            messagebox.showerror("Error", "Please enter a filename")
            return
        
        try:
            # Send START command to begin data acquisition
            response = self.send_serial_command("START", use_existing_connection=True)
            if response and "ERROR" in response:
                messagebox.showerror("Error", f"Failed to start logger: {response}")
                return
            
            # Open CSV file
            self.csv_file = open(filename, 'w', newline='')
            self.csv_writer = csv.writer(self.csv_file)
            
            # Write header with variable number of channels
            headers = ['Timestamp'] + [f'Temp{i}' for i in range(1, self.num_channels + 1)]
            self.csv_writer.writerow(headers)
            
            # Start logging thread
            self.is_logging = True
            self.set_connection_state(ConnectionState.LOGGING)
            self.logging_thread = threading.Thread(target=self.logging_loop, daemon=True)
            self.logging_thread.start()
            
            # Update UI
            self.start_stop_button.config(text="Stop Logging")
            self.status_label.config(text="Logging...")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start logging: {str(e)}")
            self.stop_logging()
    
    def stop_logging(self):
        """Stop the logging process"""
        self.is_logging = False
        
        # Try to send STOP command if connected
        if self.is_connected():
            try:
                # Some devices might have a STOP command, but we'll just stop reading
                pass
            except:
                pass
        
        # Close CSV file
        if hasattr(self, 'csv_file'):
            try:
                self.csv_file.close()
            except:
                pass
        
        # Update connection state (back to connected if still connected, or disconnected)
        if self.is_connected():
            self.set_connection_state(ConnectionState.CONNECTED)
        else:
            self.set_connection_state(ConnectionState.DISCONNECTED)
        
        # Update UI
        self.start_stop_button.config(text="Start Logging")
        self.status_label.config(text="Ready")
    
    def logging_loop(self):
        """Main logging loop with connection monitoring"""
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        while self.is_logging:
            try:
                # Check if connection is still valid
                if not self.is_connected():
                    self.root.after(0, lambda: messagebox.showerror("Connection Lost", 
                        "Connection to device was lost during logging.\nLogging has been stopped."))
                    break
                
                if self.serial_connection and self.serial_connection.in_waiting:
                    line = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        # Process the data
                        self.process_line(line)
                        consecutive_errors = 0  # Reset error counter on successful read
                else:
                    # Small sleep to prevent busy waiting
                    time.sleep(0.01)
                        
            except (serial.SerialException, OSError, UnicodeDecodeError) as e:
                consecutive_errors += 1
                print(f"Error in logging loop: {e} (consecutive errors: {consecutive_errors})")
                
                if consecutive_errors >= max_consecutive_errors:
                    self.root.after(0, lambda: messagebox.showerror("Connection Error", 
                        f"Multiple connection errors detected.\n"
                        f"Logging has been stopped.\n\n"
                        f"Error: {str(e)}"))
                    break
                time.sleep(0.1)  # Brief pause before retry
            except Exception as e:
                print(f"Unexpected error in logging loop: {e}")
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    break
                time.sleep(0.1)
        
        # Stop logging if loop exits
        if self.is_logging:
            self.root.after(0, self.stop_logging)
    
    def process_line(self, line):
        """Process a line of data from the serial connection"""
        try:
            values = line.split(',')
            # Handle variable number of channels (1 to 12)
            if 1 <= len(values) <= 12:
                timestamp = datetime.now()
                timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                
                # Convert to float and validate
                temp_values = []
                for val in values:
                    try:
                        temp = float(val)
                        temp_values.append(temp)
                    except ValueError:
                        temp_values.append(0.0)
                
                # Write to CSV
                if hasattr(self, 'csv_writer'):
                    self.csv_writer.writerow([timestamp_str] + temp_values)
                    self.csv_file.flush()
                
                # Add to data queue for plotting
                self.data_queue.put((timestamp, temp_values))
                
                # Update status
                self.root.after(0, lambda: self.status_label.config(
                    text=f"Last: {timestamp_str} - {len(temp_values)} channels"
                ))
                
        except Exception as e:
            print(f"Error processing line: {line}, Error: {e}")
    
    def process_data(self):
        """Process data from queue for plotting"""
        while True:
            try:
                timestamp, temp_values = self.data_queue.get(timeout=0.1)
                
                # Add to plot data
                self.timestamps.append(timestamp)
                for i, temp in enumerate(temp_values):
                    if i < len(self.temp_data):
                        self.temp_data[i].append(temp)
                
                # Limit data points for performance (optimized for larger datasets)
                if len(self.timestamps) > self.max_data_points:
                    # Remove oldest 10% of data points for efficiency
                    remove_count = max(1, self.max_data_points // 10)
                    self.timestamps = self.timestamps[remove_count:]
                    for i, data in enumerate(self.temp_data):
                        if data:
                            self.temp_data[i] = data[remove_count:]
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing data: {e}")
    
    def update_plot(self):
        """Update the real-time plot"""
        if self.timestamps and any(self.temp_data):
            # Clear previous plot
            self.ax.clear()
            
            # Setup plot again
            self.setup_plot()
            
            # Convert timestamps to relative time for x-axis
            if self.timestamps:
                start_time = self.timestamps[0]
                relative_times = [(t - start_time).total_seconds() for t in self.timestamps]
                
                # Plot each channel
                colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan', 'magenta', 'yellow']
                for i, data in enumerate(self.temp_data):
                    if data and len(data) == len(relative_times):
                        self.ax.plot(relative_times, data, color=colors[i % len(colors)], 
                                   label=f'Channel {i+1}', linewidth=2)
            
            # Update canvas
            self.canvas.draw()
        
        # Schedule next update
        self.root.after(100, self.update_plot)  # Update every 100ms
    
    def save_plot(self):
        """Save plot to selected save folder without dialog"""
        if not self.timestamps:
            messagebox.showwarning("Warning", "No data to save. Start logging first.")
            return
        
        try:
            import os
            
            # Get save folder
            save_folder = self.get_save_folder()
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"temperature_plot_{timestamp}.png"
            
            # Save to selected folder
            filepath = os.path.join(save_folder, filename)
            self.fig.savefig(filepath, dpi=300, bbox_inches='tight')
            
            # Get absolute path
            abs_path = os.path.abspath(filepath)
            
            messagebox.showinfo("Save Plot", 
                f"Plot saved successfully!\n\n"
                f"File: {filename}\n"
                f"Location: {save_folder}\n"
                f"Full path: {abs_path}\n\n"
                f"Total data points: {len(self.timestamps)}")
            
            print(f"Plot saved: {abs_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save plot: {str(e)}")
            print(f"Save error: {e}")
    
    def export_data(self):
        """Export the current data to various formats"""
        if not self.timestamps:
            messagebox.showwarning("Warning", "No data to export. Start logging first.")
            return
        
        import os
        
        # Get save folder
        save_folder = self.get_save_folder()
        
        # Generate default filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_filename = os.path.join(save_folder, f"temperature_data_{timestamp}.csv")
        
        # Open file dialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ],
            initialdir=save_folder,
            initialvalue=default_filename
        )
        
        if filename:
            try:
                # Update save folder to match the selected file's directory
                file_folder = os.path.dirname(filename)
                if file_folder:
                    self.save_folder_var.set(file_folder)
                    self.save_folder = file_folder
                
                file_ext = filename.lower().split('.')[-1]
                
                if file_ext == 'csv':
                    self._export_to_csv(filename)
                elif file_ext == 'xlsx':
                    self._export_to_excel(filename)
                elif file_ext == 'json':
                    self._export_to_json(filename)
                else:
                    # Default to CSV
                    self._export_to_csv(filename)
                
                messagebox.showinfo("Success", f"Data exported successfully to:\n{filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data: {str(e)}")
    
    def _export_to_csv(self, filename):
        """Export data to CSV format"""
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header with variable number of channels
            header = ['Timestamp', 'Time_Seconds']
            for i in range(1, max(len(self.temp_data), self.num_channels) + 1):
                header.append(f'Temp{i}')
            writer.writerow(header)
            
            # Write data
            if self.timestamps:
                start_time = self.timestamps[0]
                for i, timestamp in enumerate(self.timestamps):
                    relative_time = (timestamp - start_time).total_seconds()
                    row = [timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 
                           f"{relative_time:.3f}"]
                    
                    # Add temperature values
                    for j in range(max(len(self.temp_data), self.num_channels)):
                        if j < len(self.temp_data) and i < len(self.temp_data[j]):
                            row.append(f"{self.temp_data[j][i]:.3f}")
                        else:
                            row.append("")
                    
                    writer.writerow(row)
    
    def _export_to_excel(self, filename):
        """Export data to Excel format"""
        try:
            import pandas as pd
            
            # Prepare data
            data = []
            if self.timestamps:
                start_time = self.timestamps[0]
                for i, timestamp in enumerate(self.timestamps):
                    relative_time = (timestamp - start_time).total_seconds()
                    row = {
                        'Timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                        'Time_Seconds': relative_time
                    }
                    
                    # Add temperature values for variable number of channels
                    for j in range(max(len(self.temp_data), self.num_channels)):
                        if j < len(self.temp_data) and i < len(self.temp_data[j]):
                            row[f'Temp{j+1}'] = self.temp_data[j][i]
                        else:
                            row[f'Temp{j+1}'] = None
                    
                    data.append(row)
            
            # Create DataFrame and save
            df = pd.DataFrame(data)
            df.to_excel(filename, index=False)
            
        except ImportError:
            messagebox.showerror("Error", "Excel export requires pandas. Install with: pip install pandas openpyxl")
            raise
    
    def _export_to_json(self, filename):
        """Export data to JSON format"""
        import json
        
        # Prepare data
        data = {
            'metadata': {
                'export_time': datetime.now().isoformat(),
                'total_points': len(self.timestamps),
                'channels': max(len(self.temp_data), self.num_channels)
            },
            'data': []
        }
        
        if self.timestamps:
            start_time = self.timestamps[0]
            for i, timestamp in enumerate(self.timestamps):
                relative_time = (timestamp - start_time).total_seconds()
                temperatures = []
                
                # Add temperature values for variable number of channels
                for j in range(max(len(self.temp_data), self.num_channels)):
                    if j < len(self.temp_data) and i < len(self.temp_data[j]):
                        temperatures.append(self.temp_data[j][i])
                    else:
                        temperatures.append(None)
                
                point = {
                    'timestamp': timestamp.isoformat(),
                    'time_seconds': relative_time,
                    'temperatures': temperatures
                }
                data['data'].append(point)
        
        # Save to file
        with open(filename, 'w') as jsonfile:
            json.dump(data, jsonfile, indent=2)
    
    def clear_plot(self):
        """Clear the plot data"""
        self.timestamps.clear()
        for data in self.temp_data:
            data.clear()
        
        # Clear the plot
        self.ax.clear()
        self.setup_plot()
        self.canvas.draw()
    
    def on_closing(self):
        """Handle window closing - cleanup connections and stop logging"""
        # Stop logging if active
        if self.is_logging:
            result = messagebox.askyesno("Logging Active", 
                "Logging is currently active. Stop logging and exit?\n\n"
                "Click Yes to stop logging and exit, or No to cancel.")
            if not result:
                return
            self.stop_logging()
        
        # Disconnect from device
        if self.is_connected():
            with self.connection_lock:
                if self.serial_connection and self.serial_connection.is_open:
                    try:
                        self.serial_connection.close()
                    except:
                        pass
                self.serial_connection = None
            self.set_connection_state(ConnectionState.DISCONNECTED)
        
        # Close the window
        self.root.quit()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = MultiChannelLoggerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()