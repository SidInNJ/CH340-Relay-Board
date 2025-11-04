"""
Relay Controller for Battery Test
Maps relay functions to physical relays
"""

from relay_driver import RelayDriver
from typing import Dict


class RelayController:
    """High-level relay control for battery testing"""
    
    # Relay assignments
    RELAY_CHARGE = 1      # Relay 1: Charge enable
    RELAY_LOAD_6OHM = 2   # Relay 2: 6Ω load
    RELAY_LOAD_20OHM = 3  # Relay 3: 20Ω load
    RELAY_LOAD_75OHM = 4  # Relay 4: 75Ω load
    
    def __init__(self, relay_driver: RelayDriver):
        """
        Initialize relay controller
        
        Args:
            relay_driver: RelayDriver instance
        """
        self.driver = relay_driver
        self.states = {
            1: False,
            2: False,
            3: False,
            4: False
        }
    
    def set_charge(self, state: bool):
        """Enable/disable charging"""
        self.driver.set_relay(self.RELAY_CHARGE, state)
        self.states[self.RELAY_CHARGE] = state
    
    def set_load_6ohm(self, state: bool):
        """Enable/disable 6Ω load"""
        self.driver.set_relay(self.RELAY_LOAD_6OHM, state)
        self.states[self.RELAY_LOAD_6OHM] = state
    
    def set_load_20ohm(self, state: bool):
        """Enable/disable 20Ω load"""
        self.driver.set_relay(self.RELAY_LOAD_20OHM, state)
        self.states[self.RELAY_LOAD_20OHM] = state
    
    def set_load_75ohm(self, state: bool):
        """Enable/disable 75Ω load"""
        self.driver.set_relay(self.RELAY_LOAD_75OHM, state)
        self.states[self.RELAY_LOAD_75OHM] = state
    
    def set_all_loads(self, state: bool):
        """Enable/disable all loads"""
        self.set_load_6ohm(state)
        self.set_load_20ohm(state)
        self.set_load_75ohm(state)
    
    def all_off(self):
        """Turn off all relays"""
        self.driver.all_off()
        for relay_num in self.states:
            self.states[relay_num] = False
    
    def get_states(self) -> Dict[int, bool]:
        """Get current relay states"""
        return self.states.copy()
    
    def get_total_load_resistance(self) -> float:
        """
        Calculate total load resistance
        
        Returns:
            Total resistance in ohms (0 if no loads active)
        """
        resistances = []
        if self.states[self.RELAY_LOAD_6OHM]:
            resistances.append(6.0)
        if self.states[self.RELAY_LOAD_20OHM]:
            resistances.append(20.0)
        if self.states[self.RELAY_LOAD_75OHM]:
            resistances.append(75.0)
        
        if not resistances:
            return 0.0
        
        # Parallel resistance: 1/Rtotal = 1/R1 + 1/R2 + 1/R3
        total_inv = sum(1.0/r for r in resistances)
        return 1.0 / total_inv if total_inv > 0 else 0.0
    
    def get_expected_current(self, voltage_v: float) -> float:
        """
        Calculate expected discharge current
        
        Args:
            voltage_v: Battery voltage in volts
            
        Returns:
            Expected current in amps
        """
        resistance = self.get_total_load_resistance()
        if resistance > 0:
            return voltage_v / resistance
        return 0.0
