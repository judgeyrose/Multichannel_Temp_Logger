#!/usr/bin/env python3
"""
Enhanced Serial Communication Test for Multi-Channel Logger
Tests the embedded device's serial communication protocol
"""

import serial
import serial.tools.list_ports
import time
import sys

def list_ports():
    """List all available COM ports"""
    ports = [port.device for port in serial.tools.list_ports.comports()]
    print("Available COM ports:")
    for i, port in enumerate(ports, 1):
        print(f"  {i}. {port}")
    return ports

def test_connection(port, baudrate=9600):
    """Test basic connection to the device"""
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)  # Give device time to reset
        
        # Check if device is responsive
        if ser.in_waiting:
            initial_data = ser.read(ser.in_waiting).decode('utf-8')
            print(f"Initial data: {initial_data}")
        
        ser.close()
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

def send_command(ser, command, expected_response=None, timeout=2):
    """Send a command and return the response"""
    try:
        print(f"Sending: {command}")
        ser.write(f"{command}\n".encode('utf-8'))
        ser.flush()
        
        # Wait for response
        time.sleep(0.1)
        
        response = ""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    response += line + "\n"
                    if line.endswith("OK") or line.endswith("ERROR"):
                        break
            time.sleep(0.01)
        
        response = response.strip()
        print(f"Received: {response}")
        
        if expected_response and expected_response not in response:
            print(f"WARNING: Expected '{expected_response}' but got '{response}'")
        
        return response
    except Exception as e:
        print(f"Error sending command: {e}")
        return None

def test_channel_indexing(port):
    """Test channel indexing behavior"""
    print("\n=== Testing Channel Indexing ===")
    
    try:
        ser = serial.Serial(port, 9600, timeout=1)
        time.sleep(2)
        
        # Test with different channel counts
        test_cases = [1, 2, 3, 4]
        
        for channels in test_cases:
            print(f"\n--- Testing {channels} channel(s) ---")
            
            # Set channels
            response = send_command(ser, f"CHANNELS {channels}", "OK")
            if not response or "OK" not in response:
                print(f"Failed to set {channels} channels")
                continue
            
            # Acquire data
            response = send_command(ser, "ACQUIRE")
            if response and "TEMP:" in response:
                # Parse temperature values
                temp_part = response.split("TEMP:")[1].strip()
                temp_values = [x.strip() for x in temp_part.split(",")]
                
                print(f"Expected {channels} channels, got {len(temp_values)} values:")
                for i, temp in enumerate(temp_values):
                    print(f"  Channel {i+1}: {temp}")
                
                # Check for nan values
                nan_count = sum(1 for temp in temp_values if temp.lower() == 'nan')
                if nan_count > 0:
                    print(f"  WARNING: {nan_count} nan values detected")
        
        ser.close()
        
    except Exception as e:
        print(f"Error testing channel indexing: {e}")

def test_start_command(port):
    """Test START command and continuous data"""
    print("\n=== Testing START Command ===")
    
    try:
        ser = serial.Serial(port, 9600, timeout=1)
        time.sleep(2)
        
        # Configure device
        print("Configuring device...")
        send_command(ser, "RATE 2", "OK")  # 2 second rate
        send_command(ser, "CHANNELS 3", "OK")  # 3 channels
        send_command(ser, "SAMPLES 1", "OK")  # 1 sample
        
        # Send START command
        print("\nSending START command...")
        response = send_command(ser, "START", "OK")
        
        if response and "OK" in response:
            print("START command successful. Waiting for continuous data...")
            
            # Wait for continuous data
            data_count = 0
            start_time = time.time()
            timeout = 10  # Wait up to 10 seconds
            
            while time.time() - start_time < timeout and data_count < 3:
                if ser.in_waiting:
                    line = ser.readline().decode('utf-8').strip()
                    if line and not line.endswith("OK") and not line.endswith("ERROR"):
                        data_count += 1
                        print(f"Data {data_count}: {line}")
                        
                        # Parse the data
                        try:
                            values = [float(x.strip()) for x in line.split(",")]
                            print(f"  Parsed: {len(values)} values: {values}")
                        except ValueError as e:
                            print(f"  Parse error: {e}")
                
                time.sleep(0.1)
            
            if data_count == 0:
                print("WARNING: No continuous data received after START command")
            else:
                print(f"Received {data_count} data points")
        else:
            print("START command failed")
        
        ser.close()
        
    except Exception as e:
        print(f"Error testing START command: {e}")

def test_commands(port):
    """Test all commands systematically"""
    print(f"\nTesting commands on {port}...")
    
    try:
        ser = serial.Serial(port, 9600, timeout=1)
        time.sleep(2)
        
        # Test basic commands
        print("\n1. Testing RATE command:")
        send_command(ser, "RATE 5", "OK")
        
        print("\n2. Testing CHANNELS command:")
        send_command(ser, "CHANNELS 4", "OK")
        
        print("\n3. Testing SAMPLES command:")
        send_command(ser, "SAMPLES 3", "OK")
        
        print("\n4. Testing ACQUIRE command:")
        send_command(ser, "ACQUIRE")
        
        print("\n5. Testing START command:")
        send_command(ser, "START", "OK")
        
        print("\n6. Waiting for continuous data (5 seconds):")
        time.sleep(5)
        
        # Read any available data
        while ser.in_waiting:
            line = ser.readline().decode('utf-8').strip()
            if line:
                print(f"Continuous data: {line}")
        
        ser.close()
        print("\nTest completed!")
        
    except Exception as e:
        print(f"Error during testing: {e}")

def main():
    """Main function for user interaction"""
    print("Multi-Channel Logger Serial Communication Test")
    print("=" * 50)
    
    # List available ports
    ports = list_ports()
    
    if not ports:
        print("No COM ports found!")
        return
    
    # Get user selection
    if len(ports) == 1:
        selected_port = ports[0]
        print(f"\nUsing only available port: {selected_port}")
    else:
        try:
            choice = int(input(f"\nSelect COM port (1-{len(ports)}): ")) - 1
            if 0 <= choice < len(ports):
                selected_port = ports[choice]
            else:
                print("Invalid selection!")
                return
        except ValueError:
            print("Invalid input!")
            return
    
    print(f"\nConnected to {selected_port} at 9600 baud")
    
    # Test connection
    if not test_connection(selected_port):
        print("Connection test failed!")
        return
    
    # Run tests
    test_channel_indexing(selected_port)
    test_start_command(selected_port)
    
    # Ask if user wants to run full test
    try:
        run_full = input("\nRun full command test? (y/n): ").lower().strip()
        if run_full == 'y':
            test_commands(selected_port)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")

if __name__ == "__main__":
    main() 