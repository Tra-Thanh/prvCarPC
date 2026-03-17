from __future__ import annotations

import can


def open_bus(
    *,
    interface: str = "virtual",
    channel: str = "vcan0",
    bitrate: int | None = None,
    receive_own_messages: bool = False,
) -> can.BusABC:
    """
    Open a CAN bus using python-can.

    - interface=virtual: cross-platform simulation bus (no kernel vcan needed)
    - interface=socketcan: Linux real CAN (e.g. can0)
    """
    kwargs: dict[str, object] = {
        "interface": interface,
        "channel": channel,
        "receive_own_messages": receive_own_messages,
    }
    if bitrate is not None:
        kwargs["bitrate"] = bitrate
    return can.Bus(**kwargs)  # type: ignore[arg-type]

