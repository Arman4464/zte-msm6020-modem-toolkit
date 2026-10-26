# Hardware Specification & Architecture Report
**Device:** MTS MBrowse USB Cellular Data Card  
**Manufacturer:** ZTE Corporation  
**Baseband SoC:** Qualcomm MSM6020 (Model 237)  
**Investigation Date:** October 2026  

---

## 1. Physical Layout & Components
* **Enclosure:** Compact USB stick dongle with protective USB-A cap and sliding casing.
* **Branding:** MTS (Sistema Shyam TeleServices Limited) "MBrowse" logo.
* **USB Interface:** USB 2.0 Full-Speed / High-Speed Type-A connector.
* **External RF Port:** Micro-coaxial RF port (TS-9 / CRC-9 form factor) located on the chassis.
  * *Function:* An internal mechanical bypass switch. When an external antenna plug is inserted, it lifts the internal spring contact from the printed PCB trace antenna and routes RF energy exclusively through the external high-gain antenna.
* **Cellular SIM/R-UIM:** Internal R-UIM (Removable User Identity Module) card slot under the sliding cover.
* **MicroSD Storage:** None (hardware channels dedicated solely to telecom interfaces).

---

## 2. Chipset & Baseband Details
* **Processor SoC:** Qualcomm MSM6020 (Model 237)
* **Radio Standards:** CDMA2000 1xRTT (TIA/EIA/IS-707-A, IS-95A/B, Spread Spectrum)
* **Frequency Bands:** CDMA Band Class 0 (800 MHz cellular band)
* **Power Source:** Direct 5V USB VBUS (`AT+CBC: 1, 0` - 100% bus powered, 0% internal battery)
* **Baseband Kernel Version:** `RC8A7157*`
* **Firmware Build Timestamp:** March 17, 2011 @ 09:24:43 (Qualcomm Baseband Core: April 16, 2007 @ 13:00:00)

---

## 3. Dual-Mode USB Descriptor Architecture (ZeroCD)

The device features two operational modes toggled by microcontroller firmware:

### Mode 1: Initial Mass Storage Mode (Virtual CD-ROM)
When first connected to any USB port, the device defaults to:
* **USB Vendor ID (VID):** `0x19D2` (ZTE Corporation)
* **USB Product ID (PID):** `0xFFF5` (ZTE ZeroCD Mode)
* **Device Class:** `0x08` (Mass Storage) / SCSI CD-ROM emulation
* **Volume Name:** `MBrowse USB Mode` (~7.18 MB ISO filesystem)
* **Files:** `Setup.exe` (Inno Setup 5.2.3 package containing 32/64-bit drivers and MBrowse dashboard), `Autorun.inf`, `Autorun.ico`.

### Mode 2: Switched Composite Modem Mode
Triggered by sending the ZTE vendor SCSI command payload (`9F 03 00 00 00 00`) via `IOCTL_SCSI_PASS_THROUGH_DIRECT`:
* **USB Vendor ID (VID):** `0x19D2` (ZTE Corporation)
* **USB Product ID (PID):** `0xFFFE` (ZTE Composite Telecom Mode)
* **Device Class:** `0x00` (Composite device handled by `usbccgp.sys`)
* **Hardware Interfaces:**
  1. `MI_00`: Modem Port (Mapped to `COM13`)
  2. `MI_01`: Service Port (Mapped to `COM14`)
  3. `MI_02`: Voice Audio Port (Mapped to `COM15`)
  4. `MI_03`: Qualcomm DIAG Port (Mapped to `COM16`)
