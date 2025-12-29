import time
import serial

PORT = "COM5"
BAUD = 115200

def main():
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(2)
    print("RAW stream (Ctrl+C to stop):")

    try:
        while True:
            line = ser.readline().decode(errors="ignore").strip()
            if line:
                print(line)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
