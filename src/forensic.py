import struct
from typing import Dict, Any, List
from .diag_client import QualcommDiagClient

class ForensicScanner:
    """Forensic memory, NVRAM, and buffer extraction engine."""

    STANDARD_NV_ITEMS = {
        0: "Electronic Serial Number (ESN)",
        71: "Mobile Identification Number 1 (MIN1)",
        72: "Mobile Identification Number 2 (MIN2)",
        85: "Service Programming Code (SPC)",
        163: "International Mobile Subscriber Identity (IMSI)",
        178: "Last Dialed Digits",
        197: "Mobile Directory Number (MDN)",
        257: "Home System/Network ID (SID/NID)",
        284: "Preferred Roaming List ID (PRL ID)",
        465: "PPP Dial-Up Authentication User",
        466: "PPP Dial-Up Authentication Password",
        2954: "Mobile Equipment Identifier (MEID)"
    }

    def __init__(self, diag_client: QualcommDiagClient):
        self.client = diag_client

    def dump_nvram(self) -> Dict[int, Dict[str, Any]]:
        results = {}
        for item_id, desc in self.STANDARD_NV_ITEMS.items():
            status, data = self.client.read_nv_item(item_id)
            if status == 0 and data is not None:
                ascii_val = "".join([chr(b) for b in data if 32 <= b <= 126]).strip()
                results[item_id] = {
                    "description": desc,
                    "status": "OK",
                    "hex": data[:16].hex(),
                    "ascii": ascii_val
                }
            else:
                results[item_id] = {
                    "description": desc,
                    "status": f"ERR_{status}" if status is not None else "NO_RESPONSE",
                    "hex": None,
                    "ascii": None
                }
        return results

    def scan_sms_storage(self, max_slots: int = 20) -> List[Dict[str, Any]]:
        messages = []
        for slot in range(1, max_slots + 1):
            # Subsystem 107 (SMS), Subcommand 4 (CMGR)
            resp = self.client.send_subsys_command(107, 4, bytes([slot, 0]))
            if resp and len(resp) > 6:
                payload = resp[6:]
                is_empty = all(b == 0 for b in payload)
                if not is_empty:
                    text = "".join([chr(b) for b in payload if 32 <= b <= 126]).strip()
                    messages.append({"slot": slot, "empty": False, "text": text, "hex": payload[:32].hex()})
                else:
                    messages.append({"slot": slot, "empty": True, "text": None, "hex": None})
        return messages

    def scan_phonebook(self, max_slots: int = 20) -> List[Dict[str, Any]]:
        contacts = []
        for slot in range(1, max_slots + 1):
            # Subsystem 109 (Phonebook), Subcommand 5 (CPBR)
            resp = self.client.send_subsys_command(109, 5, struct.pack("<H", slot))
            if resp and len(resp) > 10:
                payload = resp[6:]
                clean = "".join([chr(b) for b in payload if 32 <= b <= 126]).strip()
                contacts.append({"slot": slot, "empty": len(clean) == 0, "text": clean if clean else None})
        return contacts
