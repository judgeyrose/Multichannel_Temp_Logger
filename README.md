# MultiChannelLogger

A comprehensive data logging system with both Python-based data collection/visualization and Arduino-based sensor interfacing.

## Project Structure

```
MultiChannelLogger/
├── python/          # Python data collection and visualization
├── arduino/         # Arduino/PlatformIO sensor interfacing
├── README.md        # This file
└── .gitignore       # Git ignore rules
```

## Components

### Python Application (`python/`)
- **Data Collection**: Serial communication with Arduino
- **Data Visualization**: Real-time plotting and analysis
- **Data Storage**: CSV file logging
- **User Interface**: Tkinter-based GUI

### Arduino Application (`arduino/`)
- **Sensor Interface**: Thermocouple and other sensor readings
- **Serial Communication**: Data transmission to Python
- **PlatformIO**: Modern Arduino development environment

## Quick Start

### Python Setup
```bash
cd python
pip install -r requirements.txt
python main.py
```

### Arduino Setup
```bash
cd arduino
# PlatformIO commands will be added here
```

## Documentation

- See `python/README.md` for detailed Python application documentation
- See `python/SERIAL_COMMANDS.md` for serial communication protocol
- Arduino documentation will be added to the `arduino/` directory

## License

This project is licensed under the MIT License - see the `python/LICENSE` file for details. 