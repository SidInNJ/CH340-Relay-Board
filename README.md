# CH340 USB Relay Board Library

A Python library for controlling CH340-based USB relay boards with 4 or 8 relays.

## Features

- **RelayDriver**: Low-level serial communication with CH340 relay boards
- **RelayController**: High-level relay management with load calculation
- **Manual GUI**: Interactive graphical interface for relay control
- **Test Suite**: Comprehensive testing utilities for relay board verification
- **Auto-configuration**: Supports both 4-relay and 8-relay boards
- **Auto-install**: Automatically installs missing dependencies (pyserial)

## Installation

1. Ensure Python 3.6+ is installed
2. Clone or download this library
3. Import and use:

```python
from relay_lib import RelayDriver, RelayController

# Create driver (auto-detects CH340 device)
relay = RelayDriver()

# Turn on relay 1
relay.relay_on(1)

# Turn off relay 1
relay.relay_off(1)

# Turn off all relays
relay.all_off()
```

## Usage

### Basic Relay Control

```python
from relay_lib import RelayDriver

# Auto-detect and connect
with RelayDriver() as relay:
    # Control individual relays (1-8)
    relay.relay_on(1)
    relay.relay_off(1)
    
    # Control all relays
    relay.all_on()
    relay.all_off()
```

### High-Level Relay Controller

```python
from relay_lib import RelayDriver, RelayController

relay_driver = RelayDriver()
controller = RelayController(relay_driver)

# Enable charging
controller.set_charge(True)

# Set loads
controller.set_load_6ohm(True)
controller.set_load_20ohm(True)

# Calculate total resistance and expected current
resistance = controller.get_total_load_resistance()  # Ohms
current = controller.get_expected_current(voltage=4.2)  # Amps

# Turn everything off
controller.all_off()
```

### Manual GUI

Run the interactive relay control GUI:

```bash
python relay_manual_control.py
```

Features:
- Configure relay board type (4 or 8 relays)
- Set custom names for each relay
- Turn relays on/off individually
- Bulk control (all off)
- Real-time connection status

### Testing

Run the comprehensive test suite:

```bash
# Run all tests
python test_relay.py

# Run specific test
python test_relay.py -t 1

# Interactive mode
python test_relay.py -i

# Specify COM port
python test_relay.py -p COM3
```

## Configuration

Edit `config.json` to:
- Set relay board type (4-relay or 8-relay)
- Configure relay names/functions
- Customize load resistances
- Set other hardware parameters

## Hardware Requirements

- CH340-based USB relay board (4 or 8 channel)
- USB connection to computer
- Python 3.6+

## Protocol Details

- **Baud Rate**: 9600
- **Command Format**: `[START_FLAG] [RELAY_NUM] [STATE] [CHECKSUM]`
- **START_FLAG**: 0xA0
- **STATE_ON**: 0x01
- **STATE_OFF**: 0x00
- **Command Delay**: 50ms between commands

## License

MIT License - Feel free to use and modify for your projects.

## Support

For issues or questions, please refer to the test suite for examples of proper usage.
