import serial
import time
import csv
from datetime import datetime

# Configure serial port - adjust COM port as needed
# On Windows it will be 'COM3', 'COM4', etc.
# On Mac/Linux it will be '/dev/ttyUSB0', '/dev/tty.usbmodem141101', etc.
SERIAL_PORT = 'COM10'  # Change this to match your Arduino's port
BAUD_RATE = 9600

# Create a timestamped filename
filename = f"thermocouple_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

# Open serial connection
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
print(f"Connected to {SERIAL_PORT} at {BAUD_RATE} baud")
time.sleep(2)  # Give Arduino time to reset after serial connection

try:
    with open(filename, 'w', newline='') as csvfile:
        # Create CSV writer
        csvwriter = csv.writer(csvfile)

        # Write header row
        headers = ['Timestamp'] + [f'Temp{i}' for i in range(1, 4)]  # Adjusted for 3 channels
        csvwriter.writerow(headers)

        print(f"Logging data to {filename}...")
        print("Press Ctrl+C to stop logging.")

        while True:
            # Read a line from serial
            if ser.in_waiting:
                line = ser.readline().decode('utf-8').strip()
                if line:  # Only process non-empty lines
                    # Get current timestamp
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    # Split the CSV values from Arduino
                    try:
                        # print(f"Raw line: {line}")
                        values = line.split(',')
                        if len(values) == 3:  # Adjusted to expect 3 values
                            # Map values directly to Temp1, Temp2, and Temp3
                            row = [timestamp] + values

                            # Write to CSV
                            csvwriter.writerow(row)
                            csvfile.flush()  # Ensure data is written to disk

                            # Print the actual data with timestamp
                            print(f"{timestamp}: {line}")
                        else:
                            print(f"Warning: Expected 3 values, but got {len(values)}: {line}")
                    except Exception as e:
                        print(f"Error processing line: {line}")
                        print(f"Error details: {e}")

            # Small delay to prevent CPU overuse
            time.sleep(0.1)

except KeyboardInterrupt:
    print("\nLogging stopped by user")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    ser.close()
    print("Serial connection closed")