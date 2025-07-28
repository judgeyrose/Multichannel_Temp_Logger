# MultiChannelLogger

A Python application for logging temperature data from multiple thermocouple channels via Arduino serial communication.

## Overview

This project reads temperature data from up to 3 thermocouple sensors connected to an Arduino and logs the data to a CSV file with timestamps. It's designed for continuous monitoring and data collection applications.

## Features

- **Multi-channel support**: Logs data from up to 3 thermocouple sensors
- **Real-time logging**: Continuously reads and logs data with timestamps
- **CSV output**: Saves data in a structured CSV format for easy analysis
- **Serial communication**: Communicates with Arduino via serial port
- **Timestamped files**: Creates uniquely named log files with timestamps

## Requirements

- Python 3.6 or higher
- Arduino with thermocouple sensors
- Serial communication capability

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/MultiChannelLogger.git
   cd MultiChannelLogger
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Hardware Setup

1. Connect your thermocouple sensors to your Arduino
2. Upload the corresponding Arduino sketch to your board
3. Note the COM port your Arduino is connected to

## Configuration

Before running the application, update the serial port configuration in `main.py`:

```python
SERIAL_PORT = 'COM10'  # Change this to match your Arduino's port
BAUD_RATE = 9600
```

**Port naming conventions:**
- Windows: `COM3`, `COM4`, `COM10`, etc.
- Mac/Linux: `/dev/ttyUSB0`, `/dev/tty.usbmodem141101`, etc.

## Usage

1. Ensure your Arduino is connected and the thermocouple sensors are properly wired
2. Run the application:
   ```bash
   python main.py
   ```

3. The application will:
   - Connect to the Arduino via serial port
   - Create a timestamped CSV file (e.g., `thermocouple_data_20231201_143022.csv`)
   - Begin logging temperature data from all channels
   - Display real-time data in the console

4. To stop logging, press `Ctrl+C`

## Output Format

The CSV file contains the following columns:
- `Timestamp`: Date and time of the reading
- `Temp1`: Temperature reading from channel 1
- `Temp2`: Temperature reading from channel 2  
- `Temp3`: Temperature reading from channel 3

Example output:
```csv
Timestamp,Temp1,Temp2,Temp3
2023-12-01 14:30:22,25.6,26.1,24.9
2023-12-01 14:30:23,25.7,26.2,25.0
```

## Arduino Code

You'll need to upload a corresponding Arduino sketch that:
- Reads from multiple thermocouple sensors
- Outputs comma-separated values via serial
- Sends data in the format: `temp1,temp2,temp3`

## Troubleshooting

**Connection Issues:**
- Verify the correct COM port is specified
- Ensure Arduino is properly connected
- Check that the baud rate matches your Arduino sketch

**Data Issues:**
- Verify thermocouple wiring
- Check Arduino serial output format
- Ensure sensors are properly calibrated

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built for temperature monitoring and data logging applications
- Compatible with various thermocouple sensor types
- Designed for continuous operation and reliable data collection 