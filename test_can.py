import time

from gs_usb.gs_usb import GsUsb
from gs_usb.gs_usb_frame import GsUsbFrame

def main():
    print("Scanning for gs_usb / CANable devices...")
    devs = GsUsb.scan()
    if not devs:
        print("No gs_usb devices found.")
        return

    dev = devs[0]
    print(f"Found device: {dev}")

    # Configure bitrate (500 kbit/s, typical for automotive powertrain CAN)
    if not dev.set_bitrate(500000):
        print("Failed to set bitrate to 500000")
        return

    # Start CAN interface
    dev.start()
    print("Device started. Listening for CAN frames... (Ctrl+C to stop)")

    try:
        frame = GsUsbFrame()
        while True:
            # timeout = 1 second
            if dev.read(frame, 1.0):
                print("RX:", frame)
            else:
                # no frame in 1s, just loop
                pass
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        dev.stop()
        print("Stopped device.")

if __name__ == "__main__":
    main()
