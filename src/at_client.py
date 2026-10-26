import time
import serial

class ModemATClient:
    """Client for Hayes AT commands over COM13 (Modem Interface)."""

    def __init__(self, port: str = "COM13", baudrate: int = 115200, timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

    def send_command(self, command: str, wait_seconds: float = 0.2) -> str:
        with serial.Serial(self.port, self.baudrate, timeout=self.timeout) as ser:
            ser.write(command.strip().encode("ascii") + b"\r\n")
            time.sleep(wait_seconds)
            response = ser.read_all().decode("ascii", errors="replace").strip()
            return response

    def get_device_info(self) -> dict:
        info = {
            "identification": self.send_command("ATI"),
            "serial_number": self.send_command("AT+GSN"),
            "power_status": self.send_command("AT+CBC"),
            "signal_quality": self.send_command("AT+CSQ"),
            "call_active_data": self.send_command("AT+CAD?"),
            "mobile_ip": self.send_command("AT$QCMIP?")
        }
        return info
