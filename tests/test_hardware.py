

import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.hardware import HardwareController


try:
    import board
    import neopixel
    from colorsys import hsv_to_rgb
    NEOPIXEL_AVAILABLE = True
except ImportError:
    NEOPIXEL_AVAILABLE = False
    print("NeoPixel libraries not available. Install with:")
    print("sudo pip3 install adafruit-circuitpython-neopixel")


def test_team_leader_setup():
    """Test using the same approach as your team leader"""
    if not NEOPIXEL_AVAILABLE:
        print("❌ NeoPixel libraries not installed")
        return False
    
    try:
        print("🏮 Testing Smart Lamp with Team Leader's NeoPixel Setup")
        print("=" * 50)
        
        # Test 1: Basic NeoPixel setup (same as your leader's code)
        print("Test 1: Basic NeoPixel Setup...")
        LED_COUNT = 30
        LED_PIN = board.D18
        LED_BRIGHTNESS = 0.5
        
        strip = neopixel.NeoPixel(
            LED_PIN, 
            LED_COUNT, 
            brightness=LED_BRIGHTNESS,
            auto_write=False,
            pixel_order=neopixel.GRB
        )
        
        print(f"✅ NeoPixel strip initialized: {LED_COUNT} pixels on GPIO 18")
        
        # Test 2: Basic colors
        print("\nTest 2: Basic Colors...")
        colors = [
            ("Red", (255, 0, 0)),
            ("Green", (0, 255, 0)),
            ("Blue", (0, 0, 255)),
            ("White", (255, 255, 255))
        ]
        
        for color_name, (r, g, b) in colors:
            print(f"  Setting {color_name}...")
            strip.fill((r, g, b))
            strip.show()
            time.sleep(1)
        
        # Test 3: Rainbow effect (from your leader's code)
        print("\nTest 3: Rainbow Effect...")
        
        def wheel(pos):
            """Generate rainbow colors (same function as your leader's)"""
            if pos < 85:
                return (pos * 3, 255 - pos * 3, 0)
            elif pos < 170:
                pos -= 85
                return (255 - pos * 3, 0, pos * 3)
            else:
                pos -= 170
                return (0, pos * 3, 255 - pos * 3)
        
        # Quick rainbow cycle
        for j in range(0, 256, 8):  # Faster for testing
            for i in range(len(strip)):
                pixel_index = (i * 256 // len(strip)) + j
                strip[i] = wheel(pixel_index & 255)
            strip.show()
            time.sleep(0.05)
        
        print("✅ Rainbow effect completed")
        
        # Test 4: Smart Lamp Hardware Controller
        print("\nTest 4: Smart Lamp Hardware Controller...")
        hw = HardwareController()
        
        print("  Testing lamp controls...")
        hw.turn_on_leds(255, 180, 100)  # Warm orange
        time.sleep(2)
        
        hw.set_led_strip(100, 255, 100)  # Green strip
        time.sleep(2)
        
        hw.rainbow_cycle(wait_ms=50, cycles=1)  # Rainbow effect
        
        hw.turn_off_all_leds()
        
        print("✅ Hardware controller test completed")
        
        # Test 5: Cleanup
        print("\nTest 5: Cleanup...")
        strip.fill((0, 0, 0))
        strip.show()
        hw.cleanup()
        
        print("✅ All tests passed!")
        print("\n🎉 Smart Lamp is compatible with team leader's setup!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    print("🏮 Smart Lamp - Team Leader Compatibility Test")
    print("=" * 50)
    
    if not NEOPIXEL_AVAILABLE:
        print("\n📦 Required Installation:")
        print("sudo pip3 install adafruit-circuitpython-neopixel")
        print("sudo pip3 install adafruit-blinka")
        return
    
    print("Press Ctrl+C to exit at any time")
    print()
    
    try:
        success = test_team_leader_setup()
        
        if success:
            print("\n✅ SUCCESS: Smart Lamp is ready to work with your team leader's setup!")
            print("\nNext steps:")
            print("1. Run: python main.py")
            print("2. Open web interface: http://localhost:8501")
            print("3. Enjoy your Smart Lamp! 🏮")
        else:
            print("\n❌ Some tests failed. Please check the error messages above.")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        # Try to turn off LEDs
        try:
            if NEOPIXEL_AVAILABLE:
                strip = neopixel.NeoPixel(board.D18, 30, auto_write=False)
                strip.fill((0, 0, 0))
                strip.show()
        except:
            pass

if __name__ == '__main__':
    main()