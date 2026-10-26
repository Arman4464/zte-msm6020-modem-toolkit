import json
import time
from typing import Dict, Any
from .diag_client import QualcommDiagClient

def backup_nvram_range(diag_client: QualcommDiagClient, start_id: int = 0, end_id: int = 200, output_file: str = "nvram_backup.json") -> Dict[str, Any]:
    backup_data = {
        "metadata": {
            "device": "ZTE MSM6020 (PID 0xFFFE)",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "range": [start_id, end_id]
        },
        "items": {}
    }
    
    active_count = 0
    print(f"[*] Starting NVRAM sweep across items {start_id} to {end_id}...")
    
    with diag_client:
        for item_id in range(start_id, end_id + 1):
            status, data = diag_client.read_nv_item(item_id)
            if status == 0 and data is not None:
                hex_str = data.hex()
                ascii_str = "".join([chr(b) for b in data if 32 <= b <= 126]).strip()
                backup_data["items"][str(item_id)] = {
                    "hex": hex_str,
                    "ascii": ascii_str
                }
                active_count += 1
                if active_count % 10 == 0:
                    print(f"  [+] Scanned {item_id}/{end_id} - Found {active_count} active NV items...")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, indent=2)

    print(f"[+] NVRAM backup complete! Saved {active_count} active NV items to {output_file}")
    return backup_data
