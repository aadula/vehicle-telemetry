import time
import can

print("Trying to open CAN device using 'gs_usb' interface...")

bus = None

try:
    bus = can.Bus(
        interface="gs_usb",   # gs_usb interface over libusb
        channel=0,            # first CAN channel on the device
        bitrate=500000,       # typical automotive bitrate
    )
    print("✅ CAN bus opened successfully.")
except Exception as e:
    print("❌ Failed to open CAN bus:")
    print(e)
    raise SystemExit(1)

print("Listening for CAN frames for 10 seconds...")

start = time.time()
count = 0

try:
    while time.time() - start < 10:
        msg = bus.recv(timeout=1.0)
        if msg is not None:
            count += 1
            print(f"[{count}] id=0x{msg.arbitration_id:X} dlc={msg.dlc} data={msg.data.hex()}")
finally:
    # Ensure the bus is properly shut down to avoid cleanup errors
    if bus is not None:
        try:
            bus.shutdown()
            print("CAN bus shutdown cleanly.")
        except Exception as e:
            print("Warning during shutdown:", e)

print(f"Done. Received {count} frames.")
