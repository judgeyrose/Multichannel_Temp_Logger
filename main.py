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
        self.root.geometry("1200x800")
        
        # Serial connection variables
        self.serial_connection = None
        self.is_logging = False
        self.data_queue = queue.Queue()
        
        # Data storage for plotting
        self.timestamps = []
        self.temp_data = [[], [], []]  # 3 channels
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
        main_frame.rowconfigure(3, weight=1)
        
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
        
        # Logging Settings Frame
        logging_frame = ttk.LabelFrame(main_frame, text="Logging Settings", padding="5")
        logging_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
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
        control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
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
        plot_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(0, weight=1)
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(12, 6), dpi=100)
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
        colors = ['red', 'blue', 'green']
        self.lines = []
        for i in range(3):
            line, = self.ax.plot([], [], color=colors[i], label=f'Channel {i+1}', linewidth=2)
            self.lines.append(line)
        
        self.ax.legend()
        self.fig.tight_layout()
    
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
            
            # Open CSV file
            self.csv_file = open(filename, 'w', newline='')
            self.csv_writer = csv.writer(self.csv_file)
            
            # Write header
            headers = ['Timestamp'] + [f'Temp{i}' for i in range(1, 4)]
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
            if len(values) == 3:
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
                    text=f"Last: {timestamp_str} - {temp_values}"
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
                colors = ['red', 'blue', 'green']
                for i, data in enumerate(self.temp_data):
                    if data and len(data) == len(relative_times):
                        self.ax.plot(relative_times, data, color=colors[i], 
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
            
            # Write header
            writer.writerow(['Timestamp', 'Time_Seconds', 'Temp1', 'Temp2', 'Temp3'])
            
            # Write data
            if self.timestamps:
                start_time = self.timestamps[0]
                for i, timestamp in enumerate(self.timestamps):
                    relative_time = (timestamp - start_time).total_seconds()
                    row = [timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 
                           f"{relative_time:.3f}"]
                    
                    # Add temperature values
                    for channel_data in self.temp_data:
                        if i < len(channel_data):
                            row.append(f"{channel_data[i]:.3f}")
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
                        'Time_Seconds': relative_time,
                        'Temp1': self.temp_data[0][i] if i < len(self.temp_data[0]) else None,
                        'Temp2': self.temp_data[1][i] if i < len(self.temp_data[1]) else None,
                        'Temp3': self.temp_data[2][i] if i < len(self.temp_data[2]) else None
                    }
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
                'channels': 3
            },
            'data': []
        }
        
        if self.timestamps:
            start_time = self.timestamps[0]
            for i, timestamp in enumerate(self.timestamps):
                relative_time = (timestamp - start_time).total_seconds()
                point = {
                    'timestamp': timestamp.isoformat(),
                    'time_seconds': relative_time,
                    'temperatures': [
                        self.temp_data[0][i] if i < len(self.temp_data[0]) else None,
                        self.temp_data[1][i] if i < len(self.temp_data[1]) else None,
                        self.temp_data[2][i] if i < len(self.temp_data[2]) else None
                    ]
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