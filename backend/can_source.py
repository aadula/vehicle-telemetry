"""
can_source.py

CAN bus reader for vehicle telemetry using a gs_usb-compatible adapter.

We:
- initialize the CAN bus using the gs_usb interface
- read frames and keep a latest "state" dict
- (later) decode real BMW CAN IDs into rpm, speed, temps, etc.
"""

from typing import Dict, Any
import can

# ---- CAN CONFIG FOR YOUR ADAPTER ----

CAN_INTERFACE = "gs_usb"  # uses libusb + gs_usb backend
CAN_CHANNEL = 0           # first channel on device
BITRATE = 500000          # standard automotive high-speed CAN

# ------------------------------------

_bus = None

_state: Dict[str, Any] = {
    "rpm": 0.0,
    "speed": 0.0,
    "coolant": 0.0,
    "oil": 0.0,
    "boost": 0.0,
    "voltage": 13.8,
}


def init_can():
    """
    Initialize the CAN bus using gs_usb.
    """
    global _bus
    print(
        f"[CAN] Initializing CAN bus using interface={CAN_INTERFACE}, "
        f"channel={CAN_CHANNEL}, bitrate={BITRATE}..."
    )
    _bus = can.Bus(
        interface=CAN_INTERFACE,
        channel=CAN_CHANNEL,
        bitrate=BITRATE,
    )
    print("[CAN] Bus initialized.")


def _decode_frame(msg: can.Message):
    """
    Decode a single CAN frame into _state.

    Right now we just print every frame for sniffing. Once we know
    which IDs correspond to RPM, speed, temps, etc, we will update _state.

    Example stub (not real BMW IDs):

      if msg.arbitration_id == 0x123:
          rpm_raw = (msg.data[0] << 8) | msg.data[1]
          _state["rpm"] = rpm_raw * 0.25
    """
    global _state

    # For now, just log the frame so we can see traffic while sniffing
    print(f"[CAN] id=0x{msg.arbitration_id:X} dlc={msg.dlc} data={msg.data.hex()}")

    # TODO: fill in BMW-specific decode logic here later.


def read_can_sensors(timeout: float = 0.01) -> Dict[str, Any]:
    """
    Read from CAN bus and return the latest sensor values.

    - Reads one frame (if available) and updates _state.
    - Returns _state so the rest of the app sees current values.
    """
    global _bus, _state

    if _bus is None:
        raise RuntimeError("CAN bus not initialized. Call init_can() first.")

    try:
        msg = _bus.recv(timeout=timeout)
    except can.CanError as e:
        print(f"[CAN] Error reading: {e}")
        return dict(_state)

    if msg is not None:
        _decode_frame(msg)

    return dict(_state)
