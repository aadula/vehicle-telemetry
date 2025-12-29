import serial
import time

PORT = "COM5"
BAUD = 115200

def open_with_retry(port: str, baud: int, tries: int = 10, delay_s: float = 0.5):
    last_err = None
    for i in range(tries):
        try:
            ser = serial.Serial(port, baud, timeout=1)
            return ser
        except Exception as e:
            last_err = e
            print(f"[retry {i+1}/{tries}] Could not open {port}: {e}")
            time.sleep(delay_s)
    raise last_err

def main():
    print(f"Opening {PORT} @ {BAUD}...")
    ser = open_with_retry(PORT, BAUD)
    time.sleep(1.5)  # allow ESP32 to finish boot text

    print("Reading... (Ctrl+C to stop)")
    try:
        while True:
            line = ser.readline().decode(errors="ignore").strip()
            if line:
                print(line)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        try:
            ser.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
