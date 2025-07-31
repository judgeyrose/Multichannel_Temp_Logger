#!/usr/bin/env python3
"""
Simple Serial Communication Test Script for Multi-Channel Thermocouple Logger

This script helps test the serial communication protocol with the embedded logger device.
Run this script to verify that your embedded firmware is responding correctly to commands.
"""

import serial
import serial.tools.list_ports
import time
import sys

def list_ports():
    """List all available COM ports"""
    ports = [port.device for port in serial.tools.list_ports.comports()]
    print("Available COM ports:")
    for port in ports:
        print(f"  {port}")
    return ports

def test_connection(port, baudrate=9600):
    """Test basic connection to the device"""
    try:
        ser = serial.Serial(port, baudrate, timeout=2)
        time.sleep(2)  # Give device time to reset
        
        print(f"Connected to {port} at {baudrate} baud")
        
        # Test if device is responding
        if ser.in_waiting:
            print("Device is sending data:")
            while ser.in_waiting:
                line = ser.readline().decode('utf-8').strip()
                if line:
                    print(f"  Received: {line}")
        
        ser.close()
        return True
        
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

def send_command(ser, command, expected_response=None):
    """Send a command and wait for response"""
    print(f"Sending: {command}")
    
    # Send command
    ser.write(f"{command}\n".encode('utf-8'))
    ser.flush()
    
    # Wait for response
    time.sleep(0.5)
    
    # Read response
    response = ""
    timeout = time.time() + 3.0
    
    while time.time() < timeout:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8').strip()
            if line:
                response += line + "\n"
                print(f"Received: {line}")
                if line.endswith("OK") or line.endswith("ERROR"):
                    break
        time.sleep(0.01)
    
    if not response:
        print("No response received")
        return False
    
    if expected_response and expected_response not in response:
        print(f"Unexpected response. Expected '{expected_response}' but got '{response}'")
        return False
    
    return True

def test_commands(port):
    """Test all the serial commands"""
    try:
        ser = serial.Serial(port, 9600, timeout=2)
        time.sleep(2)  # Give device time to reset
        
        print(f"\nTesting commands on {port}...")
        
        # Test RATE command
        print("\n1. Testing RATE command:")
        send_command(ser, "RATE 5", "OK")
        
        # Test CHANNELS command
        print("\n2. Testing CHANNELS command:")
        send_command(ser, "CHANNELS 4", "OK")
        
        # Test SAMPLES command
        print("\n3. Testing SAMPLES command:")
        send_command(ser, "SAMPLES 3", "OK")
        
        # Test ACQUIRE command
        print("\n4. Testing ACQUIRE command:")
        send_command(ser, "ACQUIRE", "TEMP:")
        
        # Test START command
        print("\n5. Testing START command:")
        send_command(ser, "START", "OK")
        
        # Wait for some data
        print("\n6. Waiting for continuous data (5 seconds):")
        start_time = time.time()
        while time.time() - start_time < 5:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8').strip()
                if line and not line.endswith("OK") and not line.endswith("ERROR"):
                    print(f"  Data: {line}")
            time.sleep(0.1)
        
        ser.close()
        print("\nTest completed!")
        
    except Exception as e:
        print(f"Test failed: {e}")

def main():
    """Main function"""
    print("Multi-Channel Thermocouple Logger - Serial Communication Test")
    print("=" * 60)
    
    # List available ports
    ports = list_ports()
    
    if not ports:
        print("No COM ports found!")
        return
    
    # Ask user to select port
    if len(ports) == 1:
        selected_port = ports[0]
        print(f"Using only available port: {selected_port}")
    else:
        print("\nSelect a COM port:")
        for i, port in enumerate(ports):
            print(f"  {i+1}. {port}")
        
        try:
            choice = int(input("Enter port number: ")) - 1
            if 0 <= choice < len(ports):
                selected_port = ports[choice]
            else:
                print("Invalid choice!")
                return
        except ValueError:
            print("Invalid input!")
            return
    
    # Test connection
    if not test_connection(selected_port):
        print("Cannot establish connection. Check your device and try again.")
        return
    
    # Test commands
    test_commands(selected_port)

if __name__ == "__main__":
    main() 