"""
CH340 USB Relay Board Driver
Supports 4-channel relay control via serial communication

Protocol:
- Baud rate: 9600
- Command format: [START_FLAG] [RELAY_NUM] [STATE] [CHECKSUM]
- 50ms delay required between commands
"""

import subprocess
import sys
import time
from typing import Optional, List

# Auto-install missing modules
try:
    import serial
    import serial.tools.list_ports
except ModuleNotFoundError as e:
    print(f"Missing module: {e.name}")
    print(f"Installing {e.name}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyserial"])
    import serial
    import serial.tools.list_ports
    print("Installation complete!")


class RelayDriver:
    """Driver for CH340 USB 4-channel relay board"""
    
    # Protocol constants
    START_FLAG = 0xA0
    STATE_OFF = 0x00
    STATE_ON = 0x01
    STATUS_QUERY = 0xFF
    BAUD_RATE = 9600
    COMMAND_DELAY = 0.05  # 50ms delay between commands
    
    def __init__(self, port: Optional[str] = None, auto_connect: bool = True):
        """
        Initialize relay driver
        
        Args:
            port: COM port name (e.g., 'COM3'). If None, will auto-detect CH340
            auto_connect: Automatically connect on initialization
        """
        self.port = port
        self.serial_conn: Optional[serial.Serial] = None
        self.last_command_time = 0
        
        if auto_connect:
            self.connect()
    
    def _find_ch340_port(self) -> Optional[str]:
        """Auto-detect CH340 USB-SERIAL device"""
        ports = serial.tools.list_ports.comports()
        for port in ports:
            # CH340 typically shows up with these identifiers
            if 'CH340' in port.description.upper() or 'USB-SERIAL' in port.description.upper():
                return port.device
        return None
    
    def connect(self) -> bool:
        """
        Connect to the relay board
        
        Returns:
            True if connection successful, False otherwise
        """
        if self.serial_conn and self.serial_conn.is_open:
            return True
        
        # Auto-detect port if not specified
        if not self.port:
            self.port = self._find_ch340_port()
            if not self.port:
                raise ConnectionError("Could not find CH340 device. Please specify port manually.")
        
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.BAUD_RATE,
                timeout=1,
                write_timeout=1
            )
            time.sleep(0.1)  # Allow connection to stabilize
            return True
        except serial.SerialException as e:
            raise ConnectionError(f"Failed to connect to {self.port}: {e}")
    
    def disconnect(self):
        """Close serial connection"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.serial_conn = None
    
    def _calculate_checksum(self, relay_num: int, state: int) -> int:
        """
        Calculate checksum for command
        Checksum = START_FLAG + RELAY_NUM + STATE
        """
        return (self.START_FLAG + relay_num + state) & 0xFF
    
    def _send_command(self, command: bytes):
        """
        Send command to relay board with proper timing
        
        Args:
            command: Bytes to send
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            raise ConnectionError("Not connected to relay board")
        
        # Enforce 50ms delay between commands
        elapsed = time.time() - self.last_command_time
        if elapsed < self.COMMAND_DELAY:
            time.sleep(self.COMMAND_DELAY - elapsed)
        
        self.serial_conn.write(command)
        self.serial_conn.flush()
        self.last_command_time = time.time()
    
    def set_relay(self, relay_num: int, state: bool):
        """
        Set relay state
        
        Args:
            relay_num: Relay number (1-8)
            state: True for ON, False for OFF
        """
        if not 1 <= relay_num <= 8:
            raise ValueError(f"Relay number must be 1-8, got {relay_num}")
        
        state_byte = self.STATE_ON if state else self.STATE_OFF
        checksum = self._calculate_checksum(relay_num, state_byte)
        
        command = bytes([self.START_FLAG, relay_num, state_byte, checksum])
        self._send_command(command)
    
    def relay_on(self, relay_num: int):
        """Turn on specified relay (1-8)"""
        self.set_relay(relay_num, True)
    
    def relay_off(self, relay_num: int):
        """Turn off specified relay (1-8)"""
        self.set_relay(relay_num, False)
    
    def all_on(self):
        """Turn on all relays (1-8)"""
        for i in range(1, 9):
            self.relay_on(i)
    
    def all_off(self):
        """Turn off all relays (1-8)"""
        for i in range(1, 9):
            self.relay_off(i)
    
    def query_status(self) -> Optional[bytes]:
        """
        Query relay status
        
        Returns:
            Status response bytes, or None if no response
        """

        # Was:         
        # if self.serial_conn and self.serial_conn.is_open:
        #   raise ConnectionError("Not connected to relay board")

        if not self.serial_conn or not self.serial_conn.is_open:
            raise ConnectionError("Not connected to relay board")
        
        # Clear input buffer
        self.serial_conn.reset_input_buffer()
        
        # Send status query
        self._send_command(bytes([self.STATUS_QUERY]))
        
        # Wait for response
        time.sleep(0.1)
        if self.serial_conn.in_waiting > 0:
            return self.serial_conn.read(self.serial_conn.in_waiting)
        return None
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
    
    def __del__(self):
        """Cleanup on deletion"""
        self.disconnect()


def list_available_ports() -> List[str]:
    """List all available COM ports"""
    ports = serial.tools.list_ports.comports()
    return [f"{port.device}: {port.description}" for port in ports]
