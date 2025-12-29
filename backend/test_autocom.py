from sources.esp32_serial import open_serial_with_retry

ser = open_serial_with_retry()
print("✅ Opened:", ser.port)
ser.close()
print("✅ Closed")
