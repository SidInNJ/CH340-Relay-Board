"""
Relay Library - Generic CH340 USB Relay Board Control
MIT License - Feel free to use and modify for your projects

This library provides:
- RelayDriver: Low-level relay board communication
- Manual GUI: Interactive relay control interface
- Test utilities: Comprehensive relay board testing

Note: RelayController has been moved to the main battery test scripts
directory as it is test-specific rather than a generic library component.
"""

from .relay_driver import RelayDriver, list_available_ports

__version__ = "1.0.0"
__all__ = ["RelayDriver", "list_available_ports"]
