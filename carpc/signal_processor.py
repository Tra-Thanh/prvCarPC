from __future__ import annotations

import time
from dataclasses import dataclass

import can
import cantools

from .model import RawFrame, SignalSample


@dataclass(frozen=True)
class ProcessResult:
    raw: RawFrame
    signals: list[SignalSample]


class DbcSignalProcessor:
    def __init__(self, *, dbc: cantools.database.Database, channel: str) -> None:
        self._dbc = dbc
        self._channel = channel

    def process(self, msg: can.Message) -> ProcessResult:
        ts = float(getattr(msg, "timestamp", None) or time.time())
        raw = RawFrame(
            ts_unix=ts,
            arbitration_id=int(msg.arbitration_id),
            is_extended_id=bool(msg.is_extended_id),
            dlc=int(msg.dlc),
            data=bytes(msg.data),
            channel=self._channel,
        )

        try:
            decoded = self._dbc.decode_message(msg.arbitration_id, bytes(msg.data))
            message = self._dbc.get_message_by_frame_id(msg.arbitration_id)
        except Exception:
            return ProcessResult(raw=raw, signals=[])

        signals: list[SignalSample] = []
        for sig in message.signals:
            if sig.name not in decoded:
                continue
            v = decoded[sig.name]
            try:
                fv = float(v)
            except Exception:
                continue
            signals.append(
                SignalSample(
                    ts_unix=ts,
                    message_name=message.name,
                    signal_name=sig.name,
                    value=fv,
                    unit=sig.unit,
                    channel=self._channel,
                )
            )

        return ProcessResult(raw=raw, signals=signals)

