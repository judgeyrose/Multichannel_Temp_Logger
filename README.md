# Multi-Channel Thermocouple Logger

A Python application for logging temperature data from multiple thermocouple channels via Arduino with a modern GUI interface and real-time plotting capabilities.

## Features

- **Modern GUI Interface**: Easy-to-use graphical interface built with tkinter
- **COM Port Configuration**: Automatic detection and selection of available COM ports
- **Connection Testing**: Built-in connection test to verify Arduino communication
- **Real-time Plotting**: Live temperature graphs for all channels using matplotlib
- **Flexible File Management**: Custom filename selection with auto-fill timestamp option
- **Multi-threaded Operation**: Non-blocking GUI with background data processing
- **Data Validation**: Robust error handling and data validation
- **Performance Optimized**: Efficient plotting with configurable data point limits

## Requirements

- Python 3.7+
- Arduino with thermocouple sensors
- Serial communication capability

## Installation

1. Clone or download this repository
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the Application**:
   ```bash
   python main.py
   ```

2. **Configure Connection**:
   - Select your Arduino's COM port from the dropdown
   - Click "Refresh Ports" if your port isn't listed
   - Click "Test Connection" to verify communication

3. **Set Logging Parameters**:
   - Use "Auto-fill" to generate a timestamped filename
   - Or click "Browse" to choose a custom location
   - Modify the filename as needed

4. **Start Logging**:
   - Click "Start Logging" to begin data collection
   - Watch real-time temperature plots update
   - Monitor status in the bottom status bar

5. **Control Options**:
   - "Stop Logging" to end data collection
   - "Clear Plot" to reset the graph
   - Close the application to exit

## GUI Components

### Connection Settings
- **COM Port Selection**: Dropdown with available serial ports
- **Refresh Ports**: Update the list of available ports
- **Test Connection**: Verify Arduino communication
- **Connection Status**: Visual indicator of connection state

### Logging Settings
- **Filename Entry**: Custom filename with timestamp auto-fill
- **Browse Button**: File dialog for save location
- **Auto-fill Button**: Generate timestamped filename

### Controls
- **Start/Stop Logging**: Toggle data collection
- **Clear Plot**: Reset the real-time graph
- **Status Display**: Current operation status

### Real-time Plot
- **Multi-channel Display**: Separate colored lines for each thermocouple
- **Time-based X-axis**: Relative time from start of logging
- **Temperature Y-axis**: Temperature values in Celsius
- **Auto-scaling**: Dynamic axis adjustment
- **Legend**: Channel identification

## Data Format

The application expects Arduino data in CSV format:
```
temperature1,temperature2,temperature3
```

Example:
```
23.5,24.1,22.8
```

## Output Files

Data is saved to CSV files with the following format:
```csv
Timestamp,Temp1,Temp2,Temp3
2024-01-15 14:30:25,23.5,24.1,22.8
2024-01-15 14:30:26,23.6,24.2,22.9
```

## Arduino Code Requirements

Your Arduino should send data in the following format:
```cpp
// Example Arduino code structure
void loop() {
  float temp1 = readThermocouple1();
  float temp2 = readThermocouple2();
  float temp3 = readThermocouple3();
  
  Serial.print(temp1);
  Serial.print(",");
  Serial.print(temp2);
  Serial.print(",");
  Serial.println(temp3);
  
  delay(1000); // Adjust as needed
}
```

## Troubleshooting

### Connection Issues
- Ensure Arduino is connected and powered
- Check COM port selection
- Verify Arduino code is running
- Try "Test Connection" button

### No Data Display
- Check Arduino serial output format
- Verify baud rate (9600)
- Ensure Arduino is sending data

### Performance Issues
- Reduce `max_data_points` in code for better performance
- Close other applications using serial ports
- Check system resources

## Technical Details

- **Serial Communication**: 9600 baud rate
- **Data Processing**: Multi-threaded with queue-based communication
- **Plot Updates**: 100ms refresh rate
- **Data Storage**: Rolling buffer with configurable size
- **Error Handling**: Comprehensive exception handling and user feedback

## License

This project is open source and available under the MIT License. 