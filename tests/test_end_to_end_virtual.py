from __future__ import annotations

import can

from carpc.can_bus import open_bus
from carpc.collector import Collector
from carpc.dbc import load_dbc
from carpc.ecu import build_message_data
from carpc.storage_sqlite import SQLiteStorage


def test_virtual_collect_and_store(tmp_path):
    dbc = load_dbc("examples/example.dbc")
    db_path = str(tmp_path / "carpc.db")
    storage = SQLiteStorage(db_path)
    storage.init_schema()

    bus = open_bus(interface="virtual", channel="vcan0", receive_own_messages=True)
    try:
        msg = dbc.get_message_by_name("VehicleStatus")
        payload = msg.encode({"SpeedKph": 12.34, "EngineRpm": 1500})
        bus.send(can.Message(arbitration_id=msg.frame_id, is_extended_id=False, data=payload))

        Collector(bus=bus, dbc=dbc, channel="vcan0", storage=storage).run(max_seconds=0.5)

        rows = storage._conn.execute("SELECT COUNT(*) FROM raw_frames").fetchone()[0]
        assert rows >= 1
        srows = storage._conn.execute("SELECT COUNT(*) FROM signal_samples").fetchone()[0]
        assert srows >= 1
    finally:
        bus.shutdown()
        storage.close()


def test_ecu_command_encodes():
    dbc = load_dbc("examples/example.dbc")
    frame_id, payload = build_message_data(dbc=dbc, message_name="VehicleCommand", signals={"SetSpeedKph": 42})
    assert frame_id == 257
    decoded = dbc.decode_message(frame_id, payload)
    assert abs(float(decoded["SetSpeedKph"]) - 42) < 0.1

