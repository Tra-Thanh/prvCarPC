from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RawFrame:
    ts_unix: float
    arbitration_id: int
    is_extended_id: bool
    dlc: int
    data: bytes
    channel: str


@dataclass(frozen=True)
class SignalSample:
    ts_unix: float
    message_name: str
    signal_name: str
    value: float
    unit: str | None
    channel: str

