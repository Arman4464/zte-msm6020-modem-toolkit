import sys
import argparse
import json
from .modeswitch import switch_to_modem_mode
from .at_client import ModemATClient
from .diag_client import QualcommDiagClient
from .forensic import ForensicScanner
from .nv_backup import backup_nvram_range

def cmd_modeswitch(args):
    print(f"[*] Issuing SCSI mode switch to volume {args.drive}: ...")
    success = switch_to_modem_mode(args.drive)
    if success:
        print("[+] Mode switch signal transmitted successfully.")
    else:
        print("[-] Failed to open or signal target drive. Ensure device is connected in ZeroCD mode.")

def cmd_info(args):
    at = ModemATClient(port=args.modem_port)
    diag = QualcommDiagClient(port=args.diag_port)
    
    print("=" * 60)
    print("  ZTE MSM6020 HARDWARE IDENTIFICATION REPORT")
    print("=" * 60)
    try:
        ati = at.send_command("ATI")
        print("[AT] Device Identification:\n" + ati)
    except Exception as e:
        print(f"[-] AT Port error: {e}")
        
    print("\n[DIAG] Querying Baseband NVRAM...")
    try:
        status, data = diag.read_nv_item(0)
        if status == 0 and data:
            import struct
            esn = struct.unpack("<I", data[:4])[0]
            print(f"[+] NV_ESN (Item 0): {esn:#010x}")
        status, data = diag.read_nv_item(71)
        if status == 0 and data:
            min1 = "".join([chr(b) for b in data if 32 <= b <= 126]).strip()
            print(f"[+] NV_MIN1 / Carrier Profile (Item 71): '{min1}'")
    except Exception as e:
        print(f"[-] DIAG Port error: {e}")

def cmd_at(args):
    at = ModemATClient(port=args.modem_port)
    cmd = " ".join(args.command)
    print(f">>> {cmd}")
    resp = at.send_command(cmd)
    print(resp)

def cmd_forensic(args):
    diag = QualcommDiagClient(port=args.diag_port)
    scanner = ForensicScanner(diag)
    
    print("[*] Initiating Non-Volatile Memory (NVRAM) Dump...")
    nv_data = scanner.dump_nvram()
    for item_id, details in nv_data.items():
        if details["status"] == "OK":
            print(f"  [Item {item_id:4d}] {details['description']:<35} : {details['ascii']} (HEX: {details['hex']})")
        else:
            print(f"  [Item {item_id:4d}] {details['description']:<35} : {details['status']}")

    print("\n[*] Scanning SMS Storage Buffers...")
    sms_list = scanner.scan_sms_storage(max_slots=args.slots)
    populated_sms = [s for s in sms_list if not s["empty"]]
    if populated_sms:
        for s in populated_sms:
            print(f"  [Slot {s['slot']:2d}] '{s['text']}'")
    else:
        print(f"  [+] All scanned slots (1-{args.slots}) are empty.")

    print("\n[*] Scanning Phonebook Records...")
    pb_list = scanner.scan_phonebook(max_slots=args.slots)
    populated_pb = [p for p in pb_list if not p["empty"]]
    if populated_pb:
        for p in populated_pb:
            print(f"  [Slot {p['slot']:2d}] '{p['text']}'")
    else:
        print(f"  [+] All scanned phonebook slots (1-{args.slots}) are empty.")

def cmd_nv(args):
    diag = QualcommDiagClient(port=args.diag_port)
    status, data = diag.read_nv_item(args.item)
    print(f"NV Item {args.item}: Status={status}")
    if status == 0 and data:
        print(f"HEX: {data[:32].hex()}")
        ascii_val = "".join([chr(b) for b in data if 32 <= b <= 126]).strip()
        print(f"ASCII: '{ascii_val}'")

def cmd_backup_nv(args):
    diag = QualcommDiagClient(port=args.diag_port)
    backup_nvram_range(diag, start_id=args.start, end_id=args.end, output_file=args.output)

def main():
    parser = argparse.ArgumentParser(description="ZTE MSM6020 CDMA Modem Hardware Control & Diagnostic Toolkit")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # modeswitch
    p_switch = subparsers.add_parser("modeswitch", help="Trigger SCSI mode-switch from ZeroCD to Composite Mode")
    p_switch.add_argument("--drive", default="H", help="Drive letter of the ZeroCD virtual CD-ROM (default: H)")
    p_switch.set_defaults(func=cmd_modeswitch)

    # info
    p_info = subparsers.add_parser("info", help="Display hardware, baseband, and firmware identification")
    p_info.add_argument("--modem-port", default="COM13")
    p_info.add_argument("--diag-port", default="COM16")
    p_info.set_defaults(func=cmd_info)

    # at
    p_at = subparsers.add_parser("at", help="Send Hayes AT command to modem")
    p_at.add_argument("command", nargs="+", help="AT command to transmit")
    p_at.add_argument("--modem-port", default="COM13")
    p_at.set_defaults(func=cmd_at)

    # forensic
    p_forensic = subparsers.add_parser("forensic", help="Execute complete forensic memory sweep (NVRAM, SMS, Phonebook)")
    p_forensic.add_argument("--diag-port", default="COM16")
    p_forensic.add_argument("--slots", type=int, default=20, help="Number of slots to scan (default: 20)")
    p_forensic.set_defaults(func=cmd_forensic)

    # nv
    p_nv = subparsers.add_parser("nv", help="Read specific Qualcomm NVRAM item")
    p_nv.add_argument("item", type=int, help="NVRAM Item ID (e.g., 0 for ESN, 71 for MIN1, 197 for MDN)")
    p_nv.add_argument("--diag-port", default="COM16")
    p_nv.set_defaults(func=cmd_nv)

    # backup-nv
    p_backup = subparsers.add_parser("backup-nv", help="Backup full NVRAM item range to a JSON file")
    p_backup.add_argument("--diag-port", default="COM16")
    p_backup.add_argument("--start", type=int, default=0, help="Starting NV Item ID (default: 0)")
    p_backup.add_argument("--end", type=int, default=300, help="Ending NV Item ID (default: 300)")
    p_backup.add_argument("--output", default="nvram_backup.json", help="Output JSON filename")
    p_backup.set_defaults(func=cmd_backup_nv)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
