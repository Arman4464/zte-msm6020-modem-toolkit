import time
import struct
import serial
from typing import Tuple, Optional

class QualcommDiagClient:
    """Client for the binary Qualcomm DIAG protocol over COM16."""

    def __init__(self, port: str = "COM16", baudrate: int = 115200, timeout: float = 1.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

    @staticmethod
    def calculate_crc16(data: bytes) -> int:
        """Calculates standard Qualcomm reversed CRC-CCITT (polynomial 0x8408)."""
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
        """Appends CRC-16, escapes reserved bytes (0x7E/0x7D), and adds 0x7E frame delimiter."""
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
        """Strips 0x7E frame delimiter and inverts escaped characters."""
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

    def send_raw_diag(self, payload: bytes, wait_seconds: float = 0.1) -> Optional[bytes]:
        with serial.Serial(self.port, self.baudrate, timeout=self.timeout) as ser:
            ser.write(self.frame_packet(payload))
            time.sleep(wait_seconds)
            resp = ser.read_all()
            if not resp:
                return None
            return self.unescape_packet(resp)

    def read_nv_item(self, item_id: int) -> Tuple[Optional[int], Optional[bytes]]:
        """
        Reads a Qualcomm Non-Volatile RAM (NVRAM) item using DIAG Command 0x26.
        Returns: (status_code, 128_byte_payload)
        """
        # DIAG_NV_READ_F: cmd=0x26, item_id=uint16_le, 128 bytes buffer, 2 bytes status
        req = bytes([0x26]) + struct.pack("<H", item_id) + (b"\x00" * 128) + (b"\x00" * 2)
        resp = self.send_raw_diag(req)
        if not resp or len(resp) < 133:
            return None, None
        status = struct.unpack("<H", resp[131:133])[0]
        data = resp[3:131]
        return status, data

    def send_subsys_command(self, subsys_id: int, subcmd_id: int, extra: bytes = b"") -> Optional[bytes]:
        """Sends a Qualcomm Subsystem Dispatch command (CMD 75 / 0x4B)."""
        payload = bytes([75, subsys_id, subcmd_id & 0xFF, (subcmd_id >> 8) & 0xFF]) + extra
        return self.send_raw_diag(payload)

    def verify_spc(self, spc: str = "000000") -> bool:
        """Verifies the 6-digit Master Service Programming Code via Subsys 115."""
        payload = bytes([75, 115, 3, 0, 65]) + spc.encode("ascii")
        resp = self.send_raw_diag(payload)
        return resp is not None and len(resp) >= 5
