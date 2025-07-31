# Serial Communication Protocol for Multi-Channel Thermocouple Logger

This document outlines the serial communication protocol between the Python GUI application and the embedded logger device.

## Communication Parameters
- **Baud Rate**: 9600
- **Data Bits**: 8
- **Parity**: None
- **Stop Bits**: 1
- **Flow Control**: None

## Command Structure

All commands are sent as ASCII strings terminated with a newline character (`\n`). Responses should also be terminated with a newline.

### 1. START Command
**Purpose**: Begin continuous data acquisition at the configured sample rate.

**Command**: `START`
**Response**: 
- Success: `START OK`
- Error: `START ERROR: <error_message>`

**Behavior**: 
- Starts continuous sampling at the configured rate
- Sends temperature data in the format: `temp1,temp2,temp3,...` (comma-delimited)
- Number of values corresponds to the configured number of channels
- Each value is the average of the configured number of samples

### 2. RATE Command
**Purpose**: Set the sample rate (time between samples).

**Command**: `RATE <value>`
**Parameters**: 
- `<value>`: Integer between 1 and 255 (seconds)

**Response**:
- Success: `RATE OK`
- Error: `RATE ERROR: <error_message>`

**Examples**:
- `RATE 5` - Set 5 second intervals
- `RATE 60` - Set 1 minute intervals

### 3. CHANNELS Command
**Purpose**: Set the number of thermocouple channels to read.

**Command**: `CHANNELS <value>`
**Parameters**:
- `<value>`: Integer between 1 and 12

**Response**:
- Success: `CHANNELS OK`
- Error: `CHANNELS ERROR: <error_message>`

**Examples**:
- `CHANNELS 3` - Read 3 thermocouples
- `CHANNELS 8` - Read 8 thermocouples

### 4. SAMPLES Command
**Purpose**: Set the number of readings to average for each sample interval.

**Command**: `SAMPLES <value>`
**Parameters**:
- `<value>`: Integer between 1 and 20

**Response**:
- Success: `SAMPLES OK`
- Error: `SAMPLES ERROR: <error_message>`

**Examples**:
- `SAMPLES 1` - No averaging (single reading)
- `SAMPLES 10` - Average 10 readings per interval

### 5. ACQUIRE Command
**Purpose**: Take a single reading immediately and return the values.

**Command**: `ACQUIRE`
**Response**:
- Success: `TEMP: <temp1>,<temp2>,<temp3>,...`
- Error: `ACQUIRE ERROR: <error_message>`

**Format**:
- Temperature values are comma-delimited
- Number of values matches the configured number of channels
- Each value is the average of the configured number of samples
- Values are in degrees Celsius (floating point)

**Example Response**: `TEMP: 25.6,30.2,22.8`

## Data Format

### Continuous Data (START mode)
When START command is active, the device continuously sends data in this format:
```
temp1,temp2,temp3,...
```

### Single Reading (ACQUIRE mode)
When ACQUIRE command is used, the device responds with:
```
TEMP: temp1,temp2,temp3,...
```

## Error Handling

All commands should respond with either:
- `OK` for success
- `ERROR: <description>` for failure

Common error scenarios:
- Invalid parameter values
- Hardware communication errors
- Thermocouple connection issues
- Memory/storage issues

## Implementation Notes

### Default Values
- Sample Rate: 1 second
- Channels: 3
- Samples: 1

### Validation
- Rate: 1-255 seconds
- Channels: 1-12
- Samples: 1-20

### Timing
- Device should respond within 2 seconds to any command
- Continuous data should be sent at the exact configured interval
- ACQUIRE command should respond immediately

### Data Precision
- Temperature values should be floating point
- Precision: 2 decimal places recommended
- Range: -200°C to +1370°C (typical thermocouple range)

## Example Communication Sequence

```
PC -> Device: RATE 5
Device -> PC: RATE OK

PC -> Device: CHANNELS 4
Device -> PC: CHANNELS OK

PC -> Device: SAMPLES 3
Device -> PC: SAMPLES OK

PC -> Device: START
Device -> PC: START OK

Device -> PC: 25.6,30.2,22.8,28.4
Device -> PC: 25.7,30.1,22.9,28.3
Device -> PC: 25.5,30.3,22.7,28.5
...

PC -> Device: ACQUIRE
Device -> PC: TEMP: 25.6,30.2,22.8,28.4
```

## Testing Commands

For testing purposes, you can implement these additional commands:

### STATUS Command
**Command**: `STATUS`
**Response**: `STATUS: Rate=<rate>,Channels=<channels>,Samples=<samples>,Active=<true/false>`

### STOP Command
**Command**: `STOP`
**Response**: `STOP OK`
**Purpose**: Stop continuous data acquisition

### RESET Command
**Command**: `RESET`
**Response**: `RESET OK`
**Purpose**: Reset device to default settings 