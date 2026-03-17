from __future__ import annotations

import logging
import random
import time

import can
import cantools

logger = logging.getLogger("carpc.sim")


class VirtualVehicle:
    def __init__(
        self,
        *,
        bus: can.BusABC,
        dbc: cantools.database.Database,
        tx_message_name: str = "VehicleStatus",
    ) -> None:
        self._bus = bus
        self._dbc = dbc
        self._msg = dbc.get_message_by_name(tx_message_name)
        self._rpm = 800.0
        self._kph = 0.0

    def _step(self) -> dict[str, float]:
        self._kph = max(0.0, min(240.0, self._kph + random.uniform(-0.5, 1.2)))
        self._rpm = max(700.0, min(6000.0, self._rpm + (self._kph * 8.0) + random.uniform(-50, 50)))
        return {"SpeedKph": self._kph, "EngineRpm": self._rpm}

    def run(self, *, hz: float = 20.0) -> None:
        period = 1.0 / hz
        logger.info("sim_started message=%s", self._msg.name)
        while True:
            signals = self._step()
            data = self._msg.encode(signals)
            msg = can.Message(arbitration_id=self._msg.frame_id, is_extended_id=False, data=data)
            try:
                self._bus.send(msg)
            except Exception as e:
                logger.warning("sim_send_failed err=%s", e)
            time.sleep(period)

