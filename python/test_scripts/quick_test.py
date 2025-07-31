#!/usr/bin/env python3
import serial
import time
from datetime import datetime

def test_channel_acquire(ser, channels):
    """Test ACQUIRE command with specific number of channels"""
    print(f"\n--- Testing ACQUIRE with {channels} channel(s) ---")
    
    # Set channels
    ser.write(f"CHANNELS {channels}\n".encode())
    time.sleep(0.5)
    
    # Read response
    while ser.in_waiting:
        line = ser.readline().decode('utf-8').strip()
        if line:
            print(f"CHANNELS response: {line}")
    
    # Acquire data
    ser.write(b"ACQUIRE\n")
    time.sleep(0.5)
    
    # Read response
    while ser.in_waiting:
        line = ser.readline().decode('utf-8').strip()
        if line:
            print(f"ACQUIRE response: {line}")
            if "TEMP:" in line:
                # Parse temperature values
                temp_part = line.split("TEMP:")[1].strip()
                temp_values = [x.strip() for x in temp_part.split(",")]
                print(f"  Expected {channels} channels, got {len(temp_values)} values:")
                for i, temp in enumerate(temp_values):
                    print(f"    Channel {i+1}: {temp}")
                
                # Check for nan values
                nan_count = sum(1 for temp in temp_values if temp.lower() == 'nan')
                if nan_count > 0:
                    print(f"  WARNING: {nan_count} nan values detected")

def test_rate_intervals(ser, rate_seconds):
    """Test if data comes at the correct intervals"""
    print(f"\n=== Testing Rate: {rate_seconds} seconds ===")
    
    # Configure device
    print("Configuring device...")
    ser.write(f"RATE {rate_seconds}\n".encode())
    time.sleep(0.5)
    ser.write(b"CHANNELS 3\n")
    time.sleep(0.5)
    ser.write(b"SAMPLES 10\n")  # Fixed at 10 samples
    time.sleep(0.5)
    
    # Clear any responses
    while ser.in_waiting:
        ser.readline()
    
    # Send START command
    print(f"Sending START command...")
    ser.write(b"START\n")
    time.sleep(0.5)
    
    # Wait for START response
    while ser.in_waiting:
        line = ser.readline().decode('utf-8').strip()
        if line:
            print(f"START response: {line}")
    
    # Wait for continuous data and measure intervals
    print(f"Waiting for continuous data (expecting every {rate_seconds} seconds)...")
    data_times = []
    start_time = time.time()
    timeout = rate_seconds * 4 + 2  # Wait for 4 data points + buffer
    
    while time.time() - start_time < timeout and len(data_times) < 4:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8').strip()
            if line and not line.endswith("OK") and not line.endswith("ERROR"):
                current_time = time.time()
                data_times.append(current_time)
                print(f"Data {len(data_times)} at {datetime.fromtimestamp(current_time).strftime('%H:%M:%S.%f')[:-3]}: {line}")
                
                # Parse the data
                try:
                    values = [float(x.strip()) for x in line.split(",")]
                    print(f"  Parsed: {len(values)} values")
                except ValueError as e:
                    print(f"  Parse error: {e}")
        
        time.sleep(0.1)
    
    # Analyze intervals
    if len(data_times) >= 2:
        intervals = []
        for i in range(1, len(data_times)):
            interval = data_times[i] - data_times[i-1]
            intervals.append(interval)
            print(f"Interval {i}: {interval:.2f} seconds")
        
        avg_interval = sum(intervals) / len(intervals)
        print(f"Average interval: {avg_interval:.2f} seconds")
        
        if abs(avg_interval - rate_seconds) < 0.5:
            print(f"✅ Rate working correctly (target: {rate_seconds}s, actual: {avg_interval:.2f}s)")
        else:
            print(f"❌ Rate issue (target: {rate_seconds}s, actual: {avg_interval:.2f}s)")
    else:
        print("❌ Not enough data points received to measure intervals")

def main():
    try:
        # Connect to device
        print("Connecting to COM10...")
        ser = serial.Serial('COM10', 9600, timeout=1)
        time.sleep(2)
        
        print("=== Channel Testing ===")
        # Test different channel configurations
        for channels in [1, 2, 3, 4]:
            test_channel_acquire(ser, channels)
            time.sleep(1)
        
        print("\n=== Rate Testing ===")
        # Test different rates
        for rate in [1, 2, 3]:
            test_rate_intervals(ser, rate)
            time.sleep(2)  # Wait between tests
        
        ser.close()
        print("\nTest completed!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 