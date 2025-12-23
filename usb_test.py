import usb.core
import usb.util

print("Scanning USB devices...")

try:
    devices = list(usb.core.find(find_all=True))
except Exception as e:
    print("Error while accessing USB:", e)
    raise

if not devices:
    print("No USB devices found.")
else:
    print(f"Found {len(devices)} USB devices:")
    for dev in devices:
        vid = hex(dev.idVendor)
        pid = hex(dev.idProduct)
        print(f" - VID={vid}, PID={pid}")
