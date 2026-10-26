# In-Depth Guide: Qualcomm Diagnostic Tools (QPST & QXDM)
**Subject:** What Are QPST & QXDM, and What Can You Do With This Modem?  

---

## 1. What Are QPST and QXDM?

Qualcomm chips power a massive percentage of the world's cellular hardware (from vintage 3G dongles to modern Snapdragon 5G smartphones). 

Because cellular basebands are complex real-time systems, Qualcomm created two legendary proprietary engineering suites to interface with them over the **Diagnostics (DIAG) COM Port** (`COM16` on your device):

1. **QPST (Qualcomm Product Support Tool):**
   * A suite of administrative, flashing, and configuration utilities designed for factory line provisioning, calibration, firmware flashing, and filesystem access.
2. **QXDM (Qualcomm Extensible Diagnostic Monitor):**
   * A real-time protocol analyzer and network packet sniffer. It captures, decodes, and logs every single radio frequency (RF) frame and baseband message flowing between the modem chip and cell towers.

---

## 2. What Specific Tools Are Inside QPST, and What Do They Do?

When you install QPST and point it to **`COM16`**, it launches an array of specialized tools:

```
                  ┌──► EFS Explorer ────────► Browse & edit internal RTOS filesystem
                  ├──► Service Programming ─► Modify NAM, MDN, MIN, SID/NID & PRL
QPST Tool Suite ──┼──► Software Download ───► Dump / flash firmware & backup QCN
                  ├──► Memory Debugger ─────► Dump raw RAM & baseband registers
                  └──► RF NV Manager ───────► Edit RF calibration curves & power tables
```

### A. QPST EFS Explorer (The "Windows Explorer" for the Modem)
* **What it is:** The Qualcomm MSM6020 runs an embedded real-time operating system (REX RTOS). Inside its flash memory is a structured hierarchical filesystem called **EFS2** (Embedded File System).
* **What you can do:**
  * Open EFS Explorer and see folders like `/nv`, `/policyman`, `/sms`, `/security`, `/data`.
  * Drag and drop files to download the internal configuration or upload custom scripts.
  * Recover hidden logs, crash dumps, or factory calibration tables.

### B. QPST Service Programming (NAM & Network Editor)
* **What it is:** The graphical editor for cellular network parameters.
* **What you can do:**
  * Change the phone number (MDN) and subscriber identity (MIN/IMSI).
  * Flash new **PRL (Preferred Roaming List)** files to reprogram which radio frequencies the modem scans for.
  * Adjust Mobile IP (MIP) settings, AAA authentication servers, and Home Agent addresses.

### C. QPST Software Download & QCN Backup / Restore
* **What it is:** The firmware flashing and non-volatile backup engine.
* **What you can do:**
  * **Dump a QCN File:** Create an exact snapshot file (`.qcn`) of the modem's entire non-volatile memory, including RF calibration tables unique to that specific circuit board.
  * **Hex / Memory Dumper:** Extract the binary partition images from flash memory for reverse engineering.

---

## 3. What Does QXDM Do?

While QPST manages files and configuration, **QXDM is a live protocol analyzer**:
* **Baseband Packet Sniffing:** When the modem attempts to communicate with a cellular tower, QXDM displays live decoded trace logs of:
  * Layer 1 (Physical RF power, signal-to-noise ratio, pilot channel acquisition)
  * Layer 2 (MAC layer frames, channel multiplexing)
  * Layer 3 (Signaling messages, authentication handshakes, SMS PDU transfers)
* **Command Dispatch:** You can send low-level raw hex diagnostic packets directly to the baseband CPU with zero abstraction.

---

## 4. Summary: How to Connect QPST to Your Drive
1. Install QPST on your PC.
2. Open **QPST Configuration**.
3. Click **Add New Port**, uncheck *"Show Serial and USB/QC Diagnostic ports only"*, and select **`COM16`** (labeled `ZTE Diagnostics Port`).
4. The phone status indicator will turn green, reporting:
   * **Phone:** `MSM6020`
   * **State:** `Enabled` / `Active`
5. Open **EFS Explorer** from the QPST Start Menu to begin exploring the modem's internal filesystem!
