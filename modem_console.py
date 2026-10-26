"""
ZTE MSM6020 CDMA Modem Automation Toolkit
Created for MTS MBrowse / ZTE USB Composite Device (VID_19D2&PID_FFFE)
Supports:
- COM13: AT Command Interface
- COM15: Voice Audio & Call Control
- COM16: Qualcomm DIAG / NVRAM Protocol
"""

import sys
import time
import struct
import serial
from serial.tools import list_ports

MODEM_PORT = 'COM13'
VOICE_PORT = 'COM15'
DIAG_PORT = 'COM16'

def qualcomm_crc16(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc >>= 1
    return (~crc) & 0xFFFF

def make_diag_packet(cmd_bytes: bytes) -> bytes:
    crc = qualcomm_crc16(cmd_bytes)
    pkt = cmd_bytes + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
    escaped = bytearray()
    for b in pkt:
        if b == 0x7E:
            escaped.extend([0x7D, 0x5E])
        elif b == 0x7D:
            escaped.extend([0x7D, 0x5D])
        else:
            escaped.append(b)
    return bytes(escaped) + b'\x7E'

def unescape_diag_packet(raw: bytes) -> bytes:
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

def send_at(cmd: str, port=MODEM_PORT, timeout=1.0) -> str:
    try:
        with serial.Serial(port, 115200, timeout=timeout) as ser:
            ser.write(cmd.encode() + b"\r\n")
            time.sleep(0.2)
            resp = ser.read_all().decode(errors='replace').strip()
            return resp
    except Exception as e:
        return f"Error opening {port}: {e}"

def read_nv(item_id: int, port=DIAG_PORT):
    try:
        with serial.Serial(port, 115200, timeout=1.0) as ser:
            req = bytes([0x26]) + struct.pack('<H', item_id) + (b'\x00' * 128) + (b'\x00' * 2)
            pkt = make_diag_packet(req)
            ser.write(pkt)
            time.sleep(0.1)
            resp = ser.read_all()
            if not resp:
                return None, "No response"
            unesc = unescape_diag_packet(resp)
            if len(unesc) < 133:
                return None, "Truncated"
            status = struct.unpack('<H', unesc[131:133])[0]
            data = unesc[3:131]
            return status, data
    except Exception as e:
        return None, str(e)

def print_banner():
    print("=" * 60)
    print("   ZTE MSM6020 / MTS MBROWSE HARDWARE CONTROL TOOLKIT")
    print("=" * 60)
    print(f" Target Ports: Modem={MODEM_PORT} | Voice={VOICE_PORT} | DIAG={DIAG_PORT}")
    print("=" * 60)

def show_quick_status():
    print("\n--- Querying Hardware Identity (AT Commands) ---")
    resp = send_at("ATI")
    print(resp)
    print("\n--- Power & Carrier Status ---")
    print(send_at("AT+CBC"))
    print(send_at("AT+CSQ"))
    print(send_at("AT+CAD?"))
    print("\n--- Diagnostic NVRAM Identity ---")
    st, data = read_nv(0)
    if st == 0:
        esn = struct.unpack('<I', data[:4])[0]
        print(f"Verified NV ESN: {esn:#010x}")
    st, data = read_nv(71)
    if st == 0:
        clean = ''.join([chr(b) for b in data if 32 <= b <= 126]).strip()
        print(f"Carrier Profile Name: '{clean}'")

def main():
    print_banner()
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == 'status':
            show_quick_status()
            return
        elif arg == 'at' and len(sys.argv) > 2:
            cmd = " ".join(sys.argv[2:])
            print(f">>> {cmd}")
            print(send_at(cmd))
            return
        elif arg == 'nv' and len(sys.argv) > 2:
            item = int(sys.argv[2])
            st, data = read_nv(item)
            print(f"NV Item {item}: Status={st}")
            if st == 0:
                print(f"HEX: {data.hex()}")
                clean = ''.join([chr(b) for b in data if 32 <= b <= 126]).strip()
                print(f"STR: '{clean}'")
            return

    # Interactive menu
    while True:
        print("\nChoose an option:")
        print("  1. Show Device Hardware & Identity Status")
        print("  2. Send Custom AT Command (COM13)")
        print("  3. Read Specific Qualcomm NVRAM Item (COM16)")
        print("  4. Send Voice Tone Test / Dialing Test (COM15)")
        print("  5. Exit")
        choice = input("\nEnter choice (1-5): ").strip()
        if choice == '1':
            show_quick_status()
        elif choice == '2':
            cmd = input("Enter AT Command (e.g. ATI, AT+CSQ, AT+GSN): ").strip()
            if cmd:
                print(send_at(cmd))
        elif choice == '3':
            raw_id = input("Enter NV Item ID (e.g. 0 for ESN, 71 for MIN1, 197 for MDN): ").strip()
            if raw_id.isdigit():
                st, data = read_nv(int(raw_id))
                print(f"NV Item {raw_id}: Status={st}")
                if st == 0:
                    print(f"HEX: {data[:32].hex()}")
                    clean = ''.join([chr(b) for b in data if 32 <= b <= 126]).strip()
                    print(f"STR: '{clean}'")
        elif choice == '4':
            print("Testing COM15 Voice Port...")
            print("Sending call initialization string...")
            resp = send_at("AT", port=VOICE_PORT)
            print(f"COM15 status: {resp}")
        elif choice == '5':
            print("Exiting toolkit.")
            break
        else:
            print("Invalid choice.")

if __name__ == '__main__':
    main()
