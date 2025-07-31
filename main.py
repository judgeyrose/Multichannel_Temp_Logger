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

class MultiChannelLoggerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Channel Thermocouple Logger")
        self.root.geometry("1400x900")
        
        # Serial connection variables
        self.serial_connection = None
        self.is_logging = False
        self.data_queue = queue.Queue()
        
        # Logger configuration variables
        self.sample_rate = 1  # Default 1 second
        self.num_channels = 3  # Default 3 channels
        self.num_samples = 10   # Default 10 samples per interval
        
        # Data storage for plotting
        self.timestamps = []
        self.temp_data = [[], [], [], [], [], [], [], [], [], [], [], []]  # 12 channels max
        self.max_data_points = 1000  # Limit data points for performance
        
        # GUI setup
        self.setup_gui()
        self.update_com_ports()
        
        # Start data processing thread
        self.data_thread = threading.Thread(target=self.process_data, daemon=True)
        self.data_thread.start()
        
        # Start plot update
        self.update_plot()
    
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
        ttk.Button(connection_frame, text="Test Connection", command=self.test_connection).grid(row=0, column=3, padx=(0, 10))
        
        # Connection status
        self.connection_status = ttk.Label(connection_frame, text="Not Connected", foreground="red")
        self.connection_status.grid(row=0, column=4, padx=(10, 0))
        
        # Logger Configuration Frame
        config_frame = ttk.LabelFrame(main_frame, text="Logger Configuration", padding="5")
        config_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Sample Rate configuration
        ttk.Label(config_frame, text="Sample Rate (1-255 sec):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.rate_var = tk.StringVar(value="1")
        self.rate_entry = ttk.Entry(config_frame, textvariable=self.rate_var, width=10)
        self.rate_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        ttk.Button(config_frame, text="Set Rate", command=self.set_sample_rate).grid(row=0, column=2, padx=(0, 10))
        
        # Number of Channels configuration
        ttk.Label(config_frame, text="Channels (1-12):").grid(row=0, column=3, sticky=tk.W, padx=(10, 5))
        self.channels_var = tk.StringVar(value="3")
        self.channels_entry = ttk.Entry(config_frame, textvariable=self.channels_var, width=10)
        self.channels_entry.grid(row=0, column=4, sticky=tk.W, padx=(0, 10))
        ttk.Button(config_frame, text="Set Channels", command=self.set_channels).grid(row=0, column=5, padx=(0, 10))
        
        # Number of Samples configuration
        ttk.Label(config_frame, text="Samples (1-20):").grid(row=0, column=6, sticky=tk.W, padx=(10, 5))
        self.samples_var = tk.StringVar(value="1")
        self.samples_entry = ttk.Entry(config_frame, textvariable=self.samples_var, width=10)
        self.samples_entry.grid(row=0, column=7, sticky=tk.W, padx=(0, 10))
        ttk.Button(config_frame, text="Set Samples", command=self.set_samples).grid(row=0, column=8, padx=(0, 10))
        
        # Acquire button
        ttk.Button(config_frame, text="Acquire Data", command=self.acquire_data).grid(row=0, column=9, padx=(10, 0))
        
        # Logging Settings Frame
        logging_frame = ttk.LabelFrame(main_frame, text="Logging Settings", padding="5")
        logging_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Filename configuration
        ttk.Label(logging_frame, text="Filename:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.filename_var = tk.StringVar()
        self.filename_entry = ttk.Entry(logging_frame, textvariable=self.filename_var, width=40)
        self.filename_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Browse button
        ttk.Button(logging_frame, text="Browse", command=self.browse_filename).grid(row=0, column=2, padx=(0, 10))
        
        # Auto-fill filename button
        ttk.Button(logging_frame, text="Auto-fill", command=self.auto_fill_filename).grid(row=0, column=3)
        
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
        
        # Auto-fill filename on startup
        self.auto_fill_filename()
    
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
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"temperature_data_{timestamp}.csv"
        self._export_to_csv(filename)
        messagebox.showinfo("Success", f"Data exported to: {filename}")
    
    def _export_to_excel_direct(self):
        """Export data directly to Excel with default filename"""
        if not self.timestamps:
            messagebox.showwarning("Warning", "No data to export. Start logging first.")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"temperature_data_{timestamp}.xlsx"
        self._export_to_excel(filename)
        messagebox.showinfo("Success", f"Data exported to: {filename}")
    
    def _export_to_json_direct(self):
        """Export data directly to JSON with default filename"""
        if not self.timestamps:
            messagebox.showwarning("Warning", "No data to export. Start logging first.")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"temperature_data_{timestamp}.json"
        self._export_to_json(filename)
        messagebox.showinfo("Success", f"Data exported to: {filename}")
    
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
    
    def send_serial_command(self, command):
        """Send a command to the logger device and return the response"""
        if not self.serial_connection or not self.serial_connection.is_open:
            messagebox.showerror("Error", "No serial connection available")
            return None
        
        try:
            # Send command with newline
            self.serial_connection.write(f"{command}\n".encode('utf-8'))
            self.serial_connection.flush()
            
            # Wait for response
            time.sleep(0.1)
            
            # Read response
            response = ""
            timeout = time.time() + 2.0  # 2 second timeout
            
            while time.time() < timeout:
                if self.serial_connection.in_waiting:
                    line = self.serial_connection.readline().decode('utf-8').strip()
                    if line:
                        response += line + "\n"
                        if line.endswith("OK") or line.endswith("ERROR"):
                            break
                time.sleep(0.01)
            
            return response.strip() if response else None
            
        except Exception as e:
            messagebox.showerror("Serial Error", f"Failed to send command: {str(e)}")
            return None
    
    def set_sample_rate(self):
        """Set the sample rate on the logger device"""
        try:
            rate = int(self.rate_var.get())
            if rate < 1 or rate > 255:
                messagebox.showerror("Error", "Sample rate must be between 1 and 255 seconds")
                return
            
            response = self.send_serial_command(f"RATE {rate}")
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
        try:
            channels = int(self.channels_var.get())
            if channels < 1 or channels > 12:
                messagebox.showerror("Error", "Number of channels must be between 1 and 12")
                return
            
            response = self.send_serial_command(f"CHANNELS {channels}")
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
        try:
            samples = int(self.samples_var.get())
            if samples < 1 or samples > 20:
                messagebox.showerror("Error", "Number of samples must be between 1 and 20")
                return
            
            response = self.send_serial_command(f"SAMPLES {samples}")
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
        response = self.send_serial_command("ACQUIRE")
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
                            
                            # Limit data points
                            if len(self.timestamps) > self.max_data_points:
                                self.timestamps.pop(0)
                                for data in self.temp_data:
                                    if data:
                                        data.pop(0)
                            
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
    
    def update_com_ports(self):
        """Update the list of available COM ports"""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.com_port_combo['values'] = ports
        if ports:
            self.com_port_combo.set(ports[0])
    
    def test_connection(self):
        """Test the serial connection"""
        port = self.com_port_var.get()
        if not port:
            messagebox.showerror("Error", "Please select a COM port")
            return
        
        try:
            # Try to open connection
            test_ser = serial.Serial(port, 9600, timeout=1)
            time.sleep(2)  # Give Arduino time to reset
            
            # Try to read a line
            if test_ser.in_waiting:
                line = test_ser.readline().decode('utf-8').strip()
                if line:
                    messagebox.showinfo("Success", f"Connection successful!\nReceived: {line}")
                    self.connection_status.config(text="Connected", foreground="green")
                else:
                    messagebox.showwarning("Warning", "Connected but no data received")
                    self.connection_status.config(text="Connected (No Data)", foreground="orange")
            else:
                messagebox.showwarning("Warning", "Connected but no data available")
                self.connection_status.config(text="Connected (No Data)", foreground="orange")
            
            test_ser.close()
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
            self.connection_status.config(text="Connection Failed", foreground="red")
    
    def auto_fill_filename(self):
        """Auto-fill filename with timestamp"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"thermocouple_data_{timestamp}.csv"
        self.filename_var.set(filename)
    
    def browse_filename(self):
        """Open file dialog to select save location"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialvalue=self.filename_var.get()
        )
        if filename:
            self.filename_var.set(filename)
    
    def toggle_logging(self):
        """Start or stop logging"""
        if not self.is_logging:
            self.start_logging()
        else:
            self.stop_logging()
    
    def start_logging(self):
        """Start the logging process"""
        port = self.com_port_var.get()
        filename = self.filename_var.get()
        
        if not port:
            messagebox.showerror("Error", "Please select a COM port")
            return
        
        if not filename:
            messagebox.showerror("Error", "Please enter a filename")
            return
        
        try:
            # Open serial connection
            self.serial_connection = serial.Serial(port, 9600, timeout=1)
            time.sleep(2)  # Give Arduino time to reset
            
            # Send START command to begin data acquisition
            response = self.send_serial_command("START")
            if response and "ERROR" in response:
                messagebox.showerror("Error", f"Failed to start logger: {response}")
                self.stop_logging()
                return
            
            # Open CSV file
            self.csv_file = open(filename, 'w', newline='')
            self.csv_writer = csv.writer(self.csv_file)
            
            # Write header with variable number of channels
            headers = ['Timestamp'] + [f'Temp{i}' for i in range(1, self.num_channels + 1)]
            self.csv_writer.writerow(headers)
            
            # Start logging thread
            self.is_logging = True
            self.logging_thread = threading.Thread(target=self.logging_loop, daemon=True)
            self.logging_thread.start()
            
            # Update UI
            self.start_stop_button.config(text="Stop Logging")
            self.status_label.config(text="Logging...")
            self.connection_status.config(text="Connected", foreground="green")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start logging: {str(e)}")
            self.stop_logging()
    
    def stop_logging(self):
        """Stop the logging process"""
        self.is_logging = False
        
        # Close serial connection
        if self.serial_connection:
            self.serial_connection.close()
            self.serial_connection = None
        
        # Close CSV file
        if hasattr(self, 'csv_file'):
            self.csv_file.close()
        
        # Update UI
        self.start_stop_button.config(text="Start Logging")
        self.status_label.config(text="Ready")
        self.connection_status.config(text="Not Connected", foreground="red")
    
    def logging_loop(self):
        """Main logging loop"""
        while self.is_logging and self.serial_connection:
            try:
                if self.serial_connection.in_waiting:
                    line = self.serial_connection.readline().decode('utf-8').strip()
                    if line:
                        # Process the data
                        self.process_line(line)
                        
            except Exception as e:
                print(f"Error in logging loop: {e}")
                break
        
        self.stop_logging()
    
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
                
                # Limit data points for performance
                if len(self.timestamps) > self.max_data_points:
                    self.timestamps.pop(0)
                    for data in self.temp_data:
                        if data:
                            data.pop(0)
                
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
        """Save plot to current directory without dialog"""
        if not self.timestamps:
            messagebox.showwarning("Warning", "No data to save. Start logging first.")
            return
        
        try:
            import os
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"temperature_plot_{timestamp}.png"
            
            # Save to current directory
            self.fig.savefig(filename, dpi=300, bbox_inches='tight')
            
            # Get absolute path
            abs_path = os.path.abspath(filename)
            
            messagebox.showinfo("Save Plot", 
                f"Plot saved successfully!\n\n"
                f"File: {filename}\n"
                f"Location: {os.getcwd()}\n\n"
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
        
        # Generate default filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_filename = f"temperature_data_{timestamp}.csv"
        
        # Open file dialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ],
            initialvalue=default_filename
        )
        
        if filename:
            try:
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

def main():
    root = tk.Tk()
    app = MultiChannelLoggerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()