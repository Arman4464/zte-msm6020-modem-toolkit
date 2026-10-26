# ZTE MSM6020 CDMA Modem Hardware Control & Forensic Toolkit

A reverse-engineering, diagnostic, and automation toolkit for legacy **Qualcomm MSM6020** CDMA 1xRTT USB modems (originally distributed by **MTS India / Sistema Shyam TeleServices** as the **MBrowse / AC8720** data card).

The toolkit provides a low-level SCSI pass-through mode-switcher (bypassing ZeroCD storage emulation), a dual-protocol client for both Hayes AT and Qualcomm Binary DIAG (HDLC/CRC-16), and forensic extraction utilities for NVRAM, SMS buffers, and phonebooks.

---

## Hardware Specifications

| Component | Technical Detail |
| :--- | :--- |
| **SoC / Baseband Processor** | Qualcomm MSM6020 (Model 237) |
| **Baseband Kernel** | `RC8A7157*` |
| **Firmware Build Date** | March 17, 2011 @ 09:24:43 |
| **Electronic Serial Number (ESN)** | `0xDD0F85B1` |
| **Radio Standard** | CDMA2000 1xRTT (IS-707-A / IS-95A/B Spread Spectrum) |
| **Supported Band** | CDMA Band Class 0 (800 MHz) |
| **ZeroCD USB Hardware ID** | `USB\VID_19D2&PID_FFF5` (Mass Storage CD-ROM Emulation) |
| **Composite USB Hardware ID** | `USB\VID_19D2&PID_FFFE` (4 Exposed Hardware Interfaces) |
| **RF Port** | TS-9 / CRC-9 micro-coaxial socket with internal mechanical bypass switch |

---

## Exposed Communication Interfaces

When switched into Composite Mode (`0x19D2:0xFFFE`), Windows exposes four communication channels:

```
                  ┌──► MI_00 (COM13) : Hayes AT Command Interface (IS-707-A)
                  ├──► MI_01 (COM14) : ZTE Proprietary Service & Event Dispatch
ZTE Modem (FFFE) ─┼──► MI_02 (COM15) : Voice Engine & Audio Tone Generation
                  └──► MI_03 (COM16) : Qualcomm Binary DIAG Protocol (HDLC / CRC-16)
```

---

## Architecture & Directory Layout

```
zte-modem-toolkit/
├── LICENSE
├── README.md
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── cli.py             # Unified command-line interface
│   ├── modeswitch.py      # SCSI pass-through mode switcher (CDB 9F 03)
│   ├── at_client.py       # Hayes AT client (COM13)
│   ├── diag_client.py     # Qualcomm DIAG HDLC framing & CRC-16 engine (COM16)
│   └── forensic.py        # NVRAM, SMS buffer, and phonebook extractor
└── docs/
    ├── 01_HARDWARE_SPECIFICATION.md
    ├── 02_PROTOCOL_AND_COMMAND_MAP.md
    ├── 03_FORENSIC_AUDIT_REPORT.md
    ├── 04_QUALCOMM_QPST_QXDM_GUIDE.md
    └── 05_RECOMMENDED_USE_CASES.md
```

---

## Installation & Prerequisites

1. **Python 3.8+**
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Ensure the device is connected to a USB port. If the device is in ZeroCD mode (appears as a CD-ROM drive letter `H:`), run the mode switcher.

---

## CLI Usage

### 1. Mode Switch (ZeroCD to Composite Mode)
Sends the vendor-specific SCSI Command Descriptor Block (`0x9F 0x03`) to eject storage emulation and expose the composite modem interfaces:
```bash
py -m src.cli modeswitch --drive H
```

### 2. Device Identification
Queries both the AT interface (`COM13`) and Qualcomm NVRAM (`COM16`) to report hardware, firmware revision, ESN, and carrier profile:
```bash
py -m src.cli info
```

### 3. Transmit Arbitrary Hayes AT Commands
Send raw AT commands to `COM13`:
```bash
py -m src.cli at ATI
py -m src.cli at AT+CSQ
py -m src.cli at AT+CAD?
py -m src.cli at AT$QCMIP?
```

### 4. Query Specific Qualcomm NVRAM Items
Read arbitrary NVRAM items via `COM16` using DIAG Command `0x26`:
```bash
# Read ESN (Item 0)
py -m src.cli nv 0

# Read Carrier Profile / MIN1 (Item 71)
py -m src.cli nv 71

# Read Mobile Directory Number (Item 197)
py -m src.cli nv 197
```

### 5. Automated Forensic Sweep
Extracts standard NVRAM items, scans SMS buffers, and inspects the phonebook:
```bash
py -m src.cli forensic --slots 20
```

---

## Protocol Reference Summary

### Qualcomm DIAG Framing
Packets transmitted over `COM16` are wrapped in an asynchronous HDLC frame:
* **Preamble / Postamble:** `0x7E`
* **Escape Byte:** `0x7D` (following byte XORed with `0x20`)
* **Checksum:** 16-bit CRC-CCITT (polynomial `0x8408` reversed, seed `0xFFFF`, bit-inverted)

### Reverse-Engineered ZTE Subsystem Dispatch (CMD 75 / 0x4B)
* `75, 106, 35`: Read Baseband Hardware Version Code
* `75, 106, 37`: Query R-UIM (SIM) Card Status
* `75, 106, 47`: Read Mobile Directory Number (MDN)
* `75, 107, 4` : Read SMS Message by Index
* `75, 107, 6` : Transmit SMS Message
* `75, 108, 2` : Outbound Voice Dial (Service Option 11)
* `75, 109, 5` : Read Phonebook Record by Index
* `75, 115, 3` : Verify Master Service Programming Code (Default: `000000`)

---

## Technical Documentation

Detailed technical documentation is provided in the [`docs/`](docs/) directory:
* [Hardware Specification](docs/01_HARDWARE_SPECIFICATION.md): Pinout, antenna bypass mechanism, and SoC architecture.
* [Protocol & Command Map](docs/02_PROTOCOL_AND_COMMAND_MAP.md): Detailed packet structures and subsystem tables.
* [Forensic Audit Report](docs/03_FORENSIC_AUDIT_REPORT.md): Data hygiene, NVRAM memory audit, and sanitized storage verification.
* [Qualcomm QPST & QXDM Guide](docs/04_QUALCOMM_QPST_QXDM_GUIDE.md): Setup instructions for EFS Explorer and protocol logging.
* [Recommended Use Cases](docs/05_RECOMMENDED_USE_CASES.md): Private Software-Defined Radio (SDR) lab, embedded communications testing, and firmware reverse engineering.

---

## License

This project is licensed under the [MIT License](LICENSE).
