import serial
import serial.tools.list_ports
import time

BAUD_RATE = 9600


def find_arduino():
    ports = serial.tools.list_ports.comports()

    for port in ports:
        print(f"Found: {port.device} - {port.description}")

        # Basic Arduino detection
        description = (port.description or "").lower()
        manufacturer = (port.manufacturer or "").lower()

        if (
            "arduino" in description
            or "arduino" in manufacturer
            or "usb serial" in description
            or "ch340" in description
        ):
            return port.device

    return None


def main():
    print("Searching for Arduino...")

    while True:
        port = find_arduino()

        if port:
            print(f"Connecting to {port}...")

            try:
                with serial.Serial(port, BAUD_RATE, timeout=1) as ser:
                    print(f"Connected to {port}")
                    print("Waiting for data...\n")

                    while True:
                        line = ser.readline()

                        if line:
                            print(line.decode("utf-8", errors="replace").strip())

            except serial.SerialException as e:
                print(f"Serial connection lost: {e}")

        else:
            print("Arduino not found.")

        time.sleep(2)


if __name__ == "__main__":
    main()