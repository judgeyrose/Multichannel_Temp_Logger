# Multi-Channel Thermocouple Logger

A Python application for logging temperature data from multiple thermocouple channels via Arduino with a modern GUI interface, real-time plotting capabilities, and comprehensive serial communication protocol.

## Features

- **Modern GUI Interface**: Easy-to-use graphical interface built with tkinter
- **Serial Communication Protocol**: Comprehensive command set for embedded device control
- **COM Port Configuration**: Automatic detection and selection of available COM ports
- **Connection Testing**: Built-in connection test to verify device communication
- **Real-time Plotting**: Live temperature graphs for all channels using matplotlib
- **Flexible File Management**: Custom filename selection with auto-fill timestamp option
- **Multi-threaded Operation**: Non-blocking GUI with background data processing
- **Data Validation**: Robust error handling and data validation
- **Performance Optimized**: Efficient plotting with configurable data point limits
- **Variable Channel Support**: Support for 1-12 thermocouple channels
- **Configurable Sampling**: Adjustable sample rates and averaging

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
   - Select your device's COM port from the dropdown
   - Click "Refresh Ports" if your port isn't listed
   - Click "Test Connection" to verify communication

3. **Configure Logger Settings**:
   - **Sample Rate**: Set time between samples (1-255 seconds)
   - **Channels**: Set number of thermocouple channels (1-12)
   - **Samples**: Set number of readings to average (1-20)
   - Click respective "Set" buttons to configure the device

4. **Set Logging Parameters**:
   - Use "Auto-fill" to generate a timestamped filename
   - Or click "Browse" to choose a custom location
   - Modify the filename as needed

5. **Start Logging**:
   - Click "Start Logging" to begin data collection
   - Watch real-time temperature plots update
   - Monitor status in the bottom status bar

6. **Control Options**:
   - "Acquire Data" for immediate single reading
   - "Stop Logging" to end data collection
   - "Clear Plot" to reset the graph
   - Close the application to exit

## GUI Components

### Connection Settings
- **COM Port Selection**: Dropdown with available serial ports
- **Refresh Ports**: Update the list of available ports
- **Test Connection**: Verify device communication
- **Connection Status**: Visual indicator of connection state

### Logger Configuration
- **Sample Rate**: Set time between samples (1-255 seconds)
- **Channels**: Set number of thermocouple channels (1-12)
- **Samples**: Set number of readings to average (1-20)
- **Acquire Data**: Take immediate single reading

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

## Serial Communication Protocol

The application uses a comprehensive serial communication protocol to control the embedded logger device. See `SERIAL_COMMANDS.md` for complete protocol documentation.

### Key Commands
- **START**: Begin continuous data acquisition
- **RATE <1-255>**: Set sample rate in seconds
- **CHANNELS <1-12>**: Set number of thermocouple channels
- **SAMPLES <1-20>**: Set number of readings to average
- **ACQUIRE**: Take immediate single reading

### Data Format

The application expects device data in CSV format:
```
temperature1,temperature2,temperature3,...
```

Example:
```
23.5,24.1,22.8,25.3
```

## Output Files

Data is saved to CSV files with the following format:
```csv
Timestamp,Temp1,Temp2,Temp3
2024-01-15 14:30:25,23.5,24.1,22.8
2024-01-15 14:30:26,23.6,24.2,22.9
```

## Embedded Device Requirements

Your embedded device should implement the serial communication protocol defined in `SERIAL_COMMANDS.md`. The device should:

1. **Respond to Commands**: Handle START, RATE, CHANNELS, SAMPLES, and ACQUIRE commands
2. **Send Data**: Output temperature values in comma-delimited format
3. **Validate Parameters**: Ensure parameters are within specified ranges
4. **Provide Error Handling**: Respond with appropriate error messages

### Example Device Response Format
```
RATE 5
RATE OK

CHANNELS 4
CHANNELS OK

START
START OK

25.6,30.2,22.8,28.4
25.7,30.1,22.9,28.3
...

ACQUIRE
TEMP: 25.6,30.2,22.8,28.4
```

## Testing

Use the included test script to verify your embedded device communication:

```bash
python test_serial.py
```

This script will test all serial commands and help identify any communication issues.

## Troubleshooting

### Connection Issues
- Ensure device is connected and powered
- Check COM port selection
- Verify device firmware is running
- Try "Test Connection" button
- Run `test_serial.py` to debug communication

### No Data Display
- Check device serial output format
- Verify baud rate (9600)
- Ensure device is responding to commands
- Check command responses in `test_serial.py`

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