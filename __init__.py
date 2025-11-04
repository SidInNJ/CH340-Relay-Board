"""
Relay Library - Generic CH340 USB Relay Board Control
MIT License - Feel free to use and modify for your projects

This library provides:
- RelayDriver: Low-level relay board communication
- RelayController: High-level relay control with load management
- Manual GUI: Interactive relay control interface
- Test utilities: Comprehensive relay board testing
"""

from .relay_driver import RelayDriver, list_available_ports
from .relay_controller import RelayController

__version__ = "1.0.0"
__all__ = ["RelayDriver", "RelayController", "list_available_ports"]
