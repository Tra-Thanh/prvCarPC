from __future__ import annotations

import logging
import time

import can
import cantools

from .signal_processor import DbcSignalProcessor
from .storage_sqlite import SQLiteStorage

logger = logging.getLogger("carpc.collector")


class Collector:
    def __init__(
        self,
        *,
        bus: can.BusABC,
        dbc: cantools.database.Database,
        channel: str,
        storage: SQLiteStorage,
        store_raw: bool = True,
        store_signals: bool = True,
    ) -> None:
        self._bus = bus
        self._storage = storage
        self._store_raw = store_raw
        self._store_signals = store_signals
        self._processor = DbcSignalProcessor(dbc=dbc, channel=channel)

    def run(self, *, max_seconds: float | None = None) -> None:
        started = time.time()
        frames = 0
        sigs = 0
        logger.info("collector_started")
        try:
            while True:
                if max_seconds is not None and (time.time() - started) >= max_seconds:
                    break
                msg = self._bus.recv(timeout=1.0)
                if msg is None:
                    continue
                res = self._processor.process(msg)
                if self._store_raw:
                    self._storage.insert_raw_frame(res.raw)
                if self._store_signals and res.signals:
                    self._storage.insert_signal_samples(res.signals)
                    sigs += len(res.signals)
                frames += 1
                if frames % 200 == 0:
                    logger.info("collector_progress frames=%s signals=%s", frames, sigs)
        finally:
            logger.info("collector_stopped frames=%s signals=%s", frames, sigs)

