# Private SDR Cell Tower & Cellular Lab Guide
**Target Device:** ZTE AC8720 / MTS MBrowse USB Modem (Qualcomm MSM6020)  
**Hardware Interface:** External RF Port (TS-9 / CRC-9) & COM Ports  

---

## 1. Overview & Principles of Operation

Although commercial CDMA 800 MHz networks have been decommissioned worldwide, this modem can still be fully utilized in a closed-loop laboratory test bench. By pairing the dongle with a **Software-Defined Radio (SDR)** and open-source base station software, you can create a private, offline cellular network.

In this setup:
* The **SDR** acts as the **Base Station (Tower)**.
* The **ZTE Dongle** acts as the **User Equipment (Client / Phone)**.
* Communication occurs entirely over a shielded coaxial cable.

---

## 2. Hardware Bill of Materials (BOM)

| Item | Specification | Purpose |
| :--- | :--- | :--- |
| **Client Device** | ZTE MSM6020 USB Modem (`0x19D2:0xFFFE`) | Cellular client device under test. |
| **SDR Transceiver** | HackRF One, Nuand bladeRF, or Ettus USRP | Generates and decodes raw RF I/Q samples. |
| **RF Coaxial Cable** | SMA-Male to TS-9 (or CRC-9) male pigtail | Physical RF connection between SDR and dongle. |
| **Inline RF Attenuator** | 20 dB or 30 dB SMA fixed attenuator (50 Ohm) | **Essential:** Protects the receiver from overload/damage. |
| **Host PC** | Linux (Ubuntu/Debian) or WSL2 with USB pass-through | Runs SDR driver and base station stack. |

---

## 3. Physical Wiring Diagram

```
[Host PC]
   ├── USB Port 1 ────► [SDR Transceiver (e.g., bladeRF / HackRF)]
   │                            │ SMA TX/RX Port
   │                            ▼
   │                    [20 dB RF Attenuator]
   │                            │
   │                            ▼ [SMA to TS-9 Coaxial Cable]
   │                            │
   └── USB Port 2 ────► [ZTE Dongle (TS-9 External Antenna Port)]
```

> [!CAUTION]
> **Never connect the SDR directly to the dongle without an inline attenuator.** SDR transmitters output between 0 dBm and +15 dBm. Directly driving this signal into the modem's low-noise amplifier (LNA) can permanently burn out the RF front-end receiver stage.

---

## 4. Software Stack Setup

### A. Base Station Software (OpenBTS-CDMA or Osmocom)
1. **OpenBTS-CDMA:** An open-source implementation of the CDMA2000 radio interface that presents standard GSM/SIP endpoints to the Asterisk PBX switchboard.
2. **Asterisk PBX:** Provides the telephone switching logic, dial plans, voicemail, and extensions.

### B. Configuration Parameters
Configure your base station to transmit on CDMA Band Class 0 (800 MHz):
* **Band:** US Cellular / Indian CDMA Band Class 0 (Downlink: 869–894 MHz, Uplink: 824–849 MHz)
* **Channel (ARFCN):** 283 (Downlink: 878.49 MHz, Uplink: 833.49 MHz)
* **SID (System ID):** `00001`
* **NID (Network ID):** `00001`
* **MCC / MNC:** `404 / 00` (or custom private test network)

---

## 5. Execution & Verification Workflow

1. **Initialize the SDR Base Station:**
   Start the OpenBTS service. The SDR will begin transmitting the pilot and sync channels over the cable.
2. **Verify Signal on the Dongle:**
   On the Windows host, query `COM13` using the Python toolkit:
   ```bash
   py -m src.cli at AT+CSQ
   ```
   *Expected Response:* `+CSQ: 31, 99` (indicates maximum received signal strength indicator).
3. **Check Cellular Registration:**
   ```bash
   py -m src.cli at AT+CAD?
   ```
   *Expected Response:* `1` (indicates active cellular connection established).

---

## 6. Functional Capabilities

### 1. Inbound & Outbound Voice Calls
* **Inbound Call:** From the PC terminal running Asterisk, dial the extension assigned to the dongle:
  ```bash
  asterisk -rx "channel originate Local/1001@default application Playback hello-world"
  ```
  The dongle will emit `RING` on `COM13`. Transmit `ATA` to connect the call. Audio is decoded on the Voice Port (`COM15`).
* **Outbound Call:** Transmit `ATD1000;` on `COM13` to dial out through the private PBX.

### 2. SMS Remote Command & Control
* Transmit SMS messages from the tower to the dongle using standard CDMA short message formats (`+CMTI` notifications).
* Transmit SMS from the dongle via `AT+CMGS` to trigger automated scripts or webhooks on the host PC.

### 3. Protocol Analysis with QXDM / Wireshark
* Bind **QXDM** to `COM16` (or pipe SDR baseband traces into **Wireshark**).
* Inspect raw CDMA IS-707 signaling, Walsh code orthogonal channel assignments, and authentication exchanges.

---

## 7. Legal and Regulatory Notice
The 800 MHz frequency band is government-licensed spectrum globally. Transmitting over the air with an antenna on licensed spectrum without an experimental radio license violates telecommunications law (FCC, TRAI, ITU). 

**Always conduct laboratory testing via a shielded coaxial cable with appropriate attenuation.** When wired directly, 100% of the electromagnetic radiation is contained within the cable shielding, making the setup completely compliant and safe from causing radio interference.
