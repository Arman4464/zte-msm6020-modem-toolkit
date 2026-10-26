import ctypes
from ctypes import wintypes
import time

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 1
FILE_SHARE_WRITE = 2
OPEN_EXISTING = 3
IOCTL_SCSI_PASS_THROUGH_DIRECT = 0x04D014

class SCSI_PASS_THROUGH_DIRECT(ctypes.Structure):
    _fields_ = [
        ("Length", wintypes.USHORT),
        ("ScsiStatus", ctypes.c_ubyte),
        ("PathId", ctypes.c_ubyte),
        ("TargetId", ctypes.c_ubyte),
        ("Lun", ctypes.c_ubyte),
        ("CdbLength", ctypes.c_ubyte),
        ("SenseInfoLength", ctypes.c_ubyte),
        ("DataIn", ctypes.c_ubyte),
        ("DataTransferLength", wintypes.ULONG),
        ("TimeOutValue", wintypes.ULONG),
        ("DataBuffer", ctypes.c_void_p),
        ("SenseInfoOffset", wintypes.ULONG),
        ("Cdb", ctypes.c_ubyte * 16),
    ]

def switch_to_modem_mode(drive_letter: str = "H") -> bool:
    """
    Sends the ZTE vendor-specific SCSI Command Descriptor Block (CDB 9F 03)
    to transition the device from ZeroCD Mass Storage (PID 0xFFF5) to
    Composite Modem Mode (PID 0xFFFE).
    """
    kernel32 = ctypes.windll.kernel32
    target_path = rf"\\.\{drive_letter.rstrip(':')}:"
    
    handle = kernel32.CreateFileW(
        target_path,
        GENERIC_READ | GENERIC_WRITE,
        FILE_SHARE_READ | FILE_SHARE_WRITE,
        None,
        OPEN_EXISTING,
        0,
        None
    )
    
    if handle == -1:
        return False

    buf = ctypes.create_string_buffer(192)
    sptd = SCSI_PASS_THROUGH_DIRECT()
    sptd.Length = ctypes.sizeof(SCSI_PASS_THROUGH_DIRECT)
    sptd.CdbLength = 6
    sptd.SenseInfoLength = 0
    sptd.DataIn = 1  # SCSI_IOCTL_DATA_IN
    sptd.DataTransferLength = 192
    sptd.TimeOutValue = 5
    sptd.DataBuffer = ctypes.cast(buf, ctypes.c_void_p)
    sptd.SenseInfoOffset = 0
    
    # ZTE mode-switch command: 0x9F 0x03
    sptd.Cdb[0] = 0x9F
    sptd.Cdb[1] = 0x03
    
    bytes_ret = wintypes.DWORD(0)
    res = kernel32.DeviceIoControl(
        handle,
        IOCTL_SCSI_PASS_THROUGH_DIRECT,
        ctypes.byref(sptd),
        ctypes.sizeof(sptd),
        ctypes.byref(sptd),
        ctypes.sizeof(sptd),
        ctypes.byref(bytes_ret),
        None
    )
    
    kernel32.CloseHandle(handle)
    time.sleep(2.0)
    return True
