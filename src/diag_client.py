import time
import struct
import serial
from typing import Tuple, Optional

class QualcommDiagClient:
    """Client for the binary Qualcomm DIAG protocol over COM16."""

    def __init__(self, port: str = "COM16", baudrate: int = 115200, timeout: float = 0.5):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._ser = None

    def open(self):
        if self._ser is None or not self._ser.is_open:
            self._ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout, write_timeout=1.0)
        return self

    def close(self):
        if self._ser and self._ser.is_open:
            self._ser.close()
            self._ser = None

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @staticmethod
    def calculate_crc16(data: bytes) -> int:
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0x8408
                else:
                    crc >>= 1
        return (~crc) & 0xFFFF

    @classmethod
    def frame_packet(cls, payload: bytes) -> bytes:
        crc = cls.calculate_crc16(payload)
        packet = payload + struct.pack("<H", crc)
        escaped = bytearray()
        for b in packet:
            if b == 0x7E:
                escaped.extend([0x7D, 0x5E])
            elif b == 0x7D:
                escaped.extend([0x7D, 0x5D])
            else:
                escaped.append(b)
        return bytes(escaped) + b"\x7E"

    @staticmethod
    def unescape_packet(raw: bytes) -> bytes:
        out = bytearray()
        i = 0
        while i < len(raw):
            if raw[i] == 0x7E:
                break
            if raw[i] == 0x7D:
                i += 1
                if i < len(raw):
                    out.append(raw[i] ^ 0x20)
            else:
                out.append(raw[i])
            i += 1
        return bytes(out)

    def send_raw_diag(self, payload: bytes, wait_seconds: float = 0.05) -> Optional[bytes]:
        should_close = False
        if self._ser is None or not self._ser.is_open:
            self.open()
            should_close = True

        try:
            self._ser.reset_input_buffer()
            self._ser.write(self.frame_packet(payload))
            time.sleep(wait_seconds)
            resp = self._ser.read_all()
            if not resp:
                return None
            return self.unescape_packet(resp)
        except Exception:
            return None
        finally:
            if should_close:
                self.close()

    def read_nv_item(self, item_id: int) -> Tuple[Optional[int], Optional[bytes]]:
        req = bytes([0x26]) + struct.pack("<H", item_id) + (b"\x00" * 128) + (b"\x00" * 2)
        resp = self.send_raw_diag(req)
        if not resp or len(resp) < 133:
            return None, None
        status = struct.unpack("<H", resp[131:133])[0]
        data = resp[3:131]
        return status, data

    def send_subsys_command(self, subsys_id: int, subcmd_id: int, extra: bytes = b"") -> Optional[bytes]:
        payload = bytes([75, subsys_id, subcmd_id & 0xFF, (subcmd_id >> 8) & 0xFF]) + extra
        return self.send_raw_diag(payload)
