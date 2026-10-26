# Communication & Protocol Reference Map
**Target Architecture:** ZTE MSM6020 CDMA Modem Interface  
**Protocol Family:** Hayes AT (IS-707-A) & Qualcomm Binary DIAG (HDLC-Framed)  

---

## 1. Active COM Port Assignments

| Windows COM Port | Hardware Endpoint | Driver Service | Protocol & Primary Use |
| :--- | :--- | :--- | :--- |
| **`COM13`** | `MI_00` | `ztud_mdm.sys` | **Hayes AT Command Interface:** Connection dialer, basic queries, carrier network status. |
| **`COM14`** | `MI_01` | `ztud_vb.sys` | **ZTE Service Port:** Event dispatching, status notifications. |
| **`COM15`** | `MI_02` | `ztud_vb.sys` | **ZTE Voice Port:** Audio stream management, voice call handling (`ATA`, `ATD`, `ATH`), DTMF tone generation (`VTS`, `ZTONE`). |
| **`COM16`** | `MI_03` | `ztud_vb.sys` | **Qualcomm DIAG Port:** Binary HDLC packet stream for NVRAM access, calibration, and QPST integration. |

---

## 2. Qualcomm DIAG Framing & CRC-16 CCITT

All packets over `COM16` follow the Qualcomm asynchronous HDLC framing standard:
```
[ Payload Bytes ... ] [ CRC-16 LSB ] [ CRC-16 MSB ] [ 0x7E Delimiter ]
```

### CRC-16 Algorithm (Polynomial `0x8408` Reversed):
```python
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
```
* **Byte Stuffing:** Any payload byte matching `0x7E` is escaped to `0x7D 0x5E`. Any byte matching `0x7D` is escaped to `0x7D 0x5D`.

---

## 3. Reverse-Engineered ZTE Subsystem Dispatch Table

Extracted directly from the embedded ZTE baseband configuration (`.config.xml`):

### Subsystem Dispatch Format:
`CMD 75 (0x4B)` + `Subsystem ID (uint8)` + `Subcommand ID (uint16 LE)` + `Optional Parameters`

| Subsystem Name | Subsys ID | Subcmd ID | Function Description |
| :--- | :---: | :---: | :--- |
| **`CSQ`** | `106` | `9` | Read cellular RF signal strength |
| **`CCLK`** | `106` | `1` | Read baseband network real-time clock |
| **`HWVER`** | `106` | `35` | Read baseband hardware version code |
| **`RUIM`** | `106` | `37` | Read R-UIM card insertion & initialization status |
| **`MEID`** | `106` | `46` | Read Mobile Equipment Identifier |
| **`MDN`** | `106` | `47` | Read Mobile Directory Number (Phone Number) |
| **`SID`** | `106` | `30` | Read CDMA System ID |
| **`BatteryLevel`** | `106` | `58` | Read power level / charging state |
| **`CMGS`** | `107` | `6` | Transmit CDMA SMS message packet |
| **`CMGR`** | `107` | `4` | Read stored SMS message from slot index |
| **`CMGD`** | `107` | `5` | Delete SMS message from slot index |
| **`CPMS`** | `107` | `2` | Select preferred SMS storage partition |
| **`ATH`** | `108` | `1` | Terminate active voice call |
| **`ATD`** | `108` | `2` | Dial outbound voice call (Service Option 11) |
| **`ATA`** | `108` | `3` | Answer incoming voice call |
| **`ZTONE`** | `108` | `6` | Generate dual-tone multi-frequency (DTMF) tone |
| **`CPBS`** | `109` | `2` | Select active phonebook storage |
| **`CPBR`** | `109` | `5` | Read contact record at index |
| **`CPBW`** | `109` | `6` | Write contact record at index |
| **`WritePRL`** | `113` | `3` | Flash Preferred Roaming List (PRL) into NVRAM |
| **`ChangeMode`**| `114` | `15` | Toggle offline/online radio operating modes |
| **`VerifySPC`** | `115` | `3` | Verify 6-digit Master Service Programming Code |
| **`WriteNv`** | `115` | `1` | Write raw NVRAM parameter block |
| **`NV`** | `115` | `5` | Read raw NVRAM parameter block |

---

## 4. Key Qualcomm Standard NVRAM Items

Read via DIAG Command `0x26` (`DIAG_NV_READ_F`):
* **Item `0` (`NV_ESN_I`):** Electronic Serial Number (`0xDD0F85B1`).
* **Item `71` (`NV_MIN1_I`):** Mobile Identification Number 1 (`"MTS India"`).
* **Item `85` (`NV_SEC_CODE_I`):** 6-digit Security Programming Code (`"000000"`).
* **Item `197` (`NV_DIR_NUMBER_I`):** Assigned phone directory number.
* **Item `284` (`NV_ROAMING_LIST_683_I`):** IS-683 PRL binary roaming data.
* **Item `465` (`NV_PAP_USER_I`):** PPP authentication username.
* **Item `466` (`NV_PAP_PASSWORD_I`):** PPP authentication password.
