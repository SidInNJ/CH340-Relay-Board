"""
Test script for CH340 USB Relay Board
Verifies relay operations and helps debug communication
"""

import time
import sys
from .relay_driver import RelayDriver, list_available_ports


def print_header(text: str):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def test_port_detection():
    """Test 1: Detect available COM ports"""
    print_header("TEST 1: Port Detection")
    ports = list_available_ports()
    
    if not ports:
        print("❌ No COM ports found!")
        return False
    
    print("✓ Available COM ports:")
    for port in ports:
        print(f"  - {port}")
    return True


def test_connection(port: str = None):
    """Test 2: Connect to relay board"""
    print_header("TEST 2: Connection Test")
    
    try:
        if port:
            print(f"Attempting to connect to {port}...")
            relay = RelayDriver(port=port, auto_connect=True)
        else:
            print("Auto-detecting CH340 device...")
            relay = RelayDriver(auto_connect=True)
        
        print(f"✓ Successfully connected to {relay.port}")
        relay.disconnect()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def test_individual_relays(port: str = None):
    """Test 3: Test each relay individually"""
    print_header("TEST 3: Individual Relay Test")
    
    try:
        with RelayDriver(port=port) as relay:
            print(f"Connected to {relay.port}\n")
            
            for relay_num in range(1, 5):
                print(f"Testing Relay {relay_num}...")
                
                # Turn ON
                print(f"  → Turning ON relay {relay_num}")
                relay.relay_on(relay_num)
                time.sleep(1)  # Visual confirmation time
                
                # Turn OFF
                print(f"  → Turning OFF relay {relay_num}")
                relay.relay_off(relay_num)
                time.sleep(0.5)
                
                print(f"  ✓ Relay {relay_num} test complete")
            
            print("\n✓ All individual relay tests passed")
            return True
            
    except Exception as e:
        print(f"❌ Individual relay test failed: {e}")
        return False


def test_all_relays(port: str = None):
    """Test 4: Test all relays together"""
    print_header("TEST 4: All Relays Test")
    
    try:
        with RelayDriver(port=port) as relay:
            print(f"Connected to {relay.port}\n")
            
            # Turn all ON
            print("Turning ON all relays...")
            relay.all_on()
            time.sleep(2)
            print("✓ All relays should be ON")
            
            # Turn all OFF
            print("\nTurning OFF all relays...")
            relay.all_off()
            time.sleep(1)
            print("✓ All relays should be OFF")
            
            return True
            
    except Exception as e:
        print(f"❌ All relays test failed: {e}")
        return False


def test_status_query(port: str = None):
    """Test 5: Query relay status"""
    print_header("TEST 5: Status Query Test")
    
    try:
        with RelayDriver(port=port) as relay:
            print(f"Connected to {relay.port}\n")
            
            # Turn on relay 1 and 3
            print("Setting up test pattern (Relay 1 & 3 ON)...")
            relay.all_off()
            time.sleep(0.2)
            relay.relay_on(1)
            relay.relay_on(3)
            
            # Query status
            print("\nQuerying status...")
            status = relay.query_status()
            
            if status:
                print(f"✓ Status response received: {status.hex(' ').upper()}")
                print(f"  Raw bytes: {[hex(b) for b in status]}")
            else:
                print("⚠ No status response (this may be normal for some boards)")
            
            # Clean up
            relay.all_off()
            return True
            
    except Exception as e:
        print(f"❌ Status query test failed: {e}")
        return False


def test_rapid_switching(port: str = None):
    """Test 6: Rapid switching with timing"""
    print_header("TEST 6: Rapid Switching Test")
    
    try:
        with RelayDriver(port=port) as relay:
            print(f"Connected to {relay.port}\n")
            print("Testing rapid switching (50ms delay enforced)...")
            
            start_time = time.time()
            cycles = 10
            
            for i in range(cycles):
                relay.relay_on(1)
                relay.relay_off(1)
            
            elapsed = time.time() - start_time
            expected_min = cycles * 2 * 0.05  # 2 commands per cycle, 50ms each
            
            print(f"✓ Completed {cycles} ON/OFF cycles")
            print(f"  Time elapsed: {elapsed:.2f}s")
            print(f"  Expected minimum: {expected_min:.2f}s")
            print(f"  Average per command: {(elapsed/(cycles*2))*1000:.1f}ms")
            
            if elapsed >= expected_min * 0.9:  # Allow 10% tolerance
                print("  ✓ Timing delay working correctly")
            else:
                print("  ⚠ Commands may be too fast")
            
            relay.all_off()
            return True
            
    except Exception as e:
        print(f"❌ Rapid switching test failed: {e}")
        return False


def interactive_mode(port: str = None):
    """Interactive mode for manual testing"""
    print_header("INTERACTIVE MODE")
    print("Commands:")
    print("  1-4: Toggle relay 1-4")
    print("  on [num]: Turn on relay")
    print("  off [num]: Turn off relay")
    print("  all on: Turn on all relays")
    print("  all off: Turn off all relays")
    print("  status: Query status")
    print("  quit: Exit")
    print()
    
    try:
        with RelayDriver(port=port) as relay:
            print(f"✓ Connected to {relay.port}\n")
            
            relay_states = [False] * 4  # Track states for toggle
            
            while True:
                try:
                    cmd = input("relay> ").strip().lower()
                    
                    if cmd == 'quit' or cmd == 'exit':
                        break
                    elif cmd in ['1', '2', '3', '4']:
                        num = int(cmd)
                        relay_states[num-1] = not relay_states[num-1]
                        relay.set_relay(num, relay_states[num-1])
                        print(f"Relay {num}: {'ON' if relay_states[num-1] else 'OFF'}")
                    elif cmd.startswith('on '):
                        num = int(cmd.split()[1])
                        relay.relay_on(num)
                        relay_states[num-1] = True
                        print(f"Relay {num}: ON")
                    elif cmd.startswith('off '):
                        num = int(cmd.split()[1])
                        relay.relay_off(num)
                        relay_states[num-1] = False
                        print(f"Relay {num}: OFF")
                    elif cmd == 'all on':
                        relay.all_on()
                        relay_states = [True] * 4
                        print("All relays: ON")
                    elif cmd == 'all off':
                        relay.all_off()
                        relay_states = [False] * 4
                        print("All relays: OFF")
                    elif cmd == 'status':
                        status = relay.query_status()
                        if status:
                            print(f"Status: {status.hex(' ').upper()}")
                        else:
                            print("No status response")
                    elif cmd == 'help':
                        print("Commands: 1-4, on [num], off [num], all on, all off, status, quit")
                    else:
                        print("Unknown command. Type 'help' for commands.")
                        
                except KeyboardInterrupt:
                    print("\nExiting...")
                    break
                except Exception as e:
                    print(f"Error: {e}")
            
            # Clean up
            relay.all_off()
            print("\n✓ All relays turned off")
            
    except Exception as e:
        print(f"❌ Interactive mode failed: {e}")


def run_all_tests(port: str = None):
    """Run all automated tests"""
    print("\n" + "="*60)
    print("  CH340 USB RELAY BOARD - TEST SUITE")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Port Detection", test_port_detection()))
    results.append(("Connection", test_connection(port)))
    results.append(("Individual Relays", test_individual_relays(port)))
    results.append(("All Relays", test_all_relays(port)))
    results.append(("Status Query", test_status_query(port)))
    results.append(("Rapid Switching", test_rapid_switching(port)))
    
    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"  {test_name:.<40} {status}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠ Some tests failed. Check connections and protocol.")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test CH340 USB Relay Board")
    parser.add_argument('-p', '--port', help='COM port (e.g., COM3)', default=None)
    parser.add_argument('-i', '--interactive', action='store_true', 
                       help='Run in interactive mode')
    parser.add_argument('-t', '--test', type=int, choices=range(1, 7),
                       help='Run specific test (1-6)')
    
    args = parser.parse_args()
    
    try:
        if args.interactive:
            interactive_mode(args.port)
        elif args.test:
            tests = [
                test_port_detection,
                lambda: test_connection(args.port),
                lambda: test_individual_relays(args.port),
                lambda: test_all_relays(args.port),
                lambda: test_status_query(args.port),
                lambda: test_rapid_switching(args.port)
            ]
            tests[args.test - 1]()
        else:
            run_all_tests(args.port)
            
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
