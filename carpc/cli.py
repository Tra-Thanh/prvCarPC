from __future__ import annotations

import logging

import can
import typer

from .can_bus import open_bus
from .collector import Collector
from .dbc import load_dbc
from .ecu import build_message_data
from .logging_setup import setup_logging
from .sim_vehicle import VirtualVehicle
from .storage_sqlite import SQLiteStorage

app = typer.Typer(add_completion=False, no_args_is_help=True)
db_app = typer.Typer(add_completion=False, no_args_is_help=True)
ecu_app = typer.Typer(add_completion=False, no_args_is_help=True)
sim_app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(db_app, name="db")
app.add_typer(ecu_app, name="ecu")
app.add_typer(sim_app, name="sim")

logger = logging.getLogger("carpc")


@db_app.command("init")
def db_init(db: str = typer.Option("carpc.db", "--db")) -> None:
    setup_logging()
    storage = SQLiteStorage(db)
    storage.init_schema()
    storage.close()
    logger.info("db_initialized path=%s", db)


@app.command("collect")
def collect(
    channel: str = typer.Option("vcan0", "--channel"),
    interface: str = typer.Option("virtual", "--interface"),
    bitrate: int | None = typer.Option(None, "--bitrate"),
    dbc: str = typer.Option(..., "--dbc"),
    db: str = typer.Option("carpc.db", "--db"),
    max_seconds: float | None = typer.Option(None, "--max-seconds"),
    log_level: str = typer.Option("INFO", "--log-level"),
) -> None:
    setup_logging(level=log_level)
    storage = SQLiteStorage(db)
    storage.init_schema()
    database = load_dbc(dbc)
    bus = open_bus(interface=interface, channel=channel, bitrate=bitrate, receive_own_messages=False)
    try:
        Collector(bus=bus, dbc=database, channel=channel, storage=storage).run(max_seconds=max_seconds)
    finally:
        bus.shutdown()
        storage.close()


@app.command("send-raw")
def send_raw(
    channel: str = typer.Option("vcan0", "--channel"),
    interface: str = typer.Option("virtual", "--interface"),
    arbitration_id: int = typer.Option(..., "--id"),
    data_hex: str = typer.Option(..., "--data"),
    log_level: str = typer.Option("INFO", "--log-level"),
) -> None:
    setup_logging(level=log_level)
    data = bytes.fromhex(data_hex.replace("0x", "").replace(" ", ""))
    bus = open_bus(interface=interface, channel=channel, receive_own_messages=False)
    try:
        msg = can.Message(arbitration_id=arbitration_id, is_extended_id=False, data=data)
        bus.send(msg)
        logger.info("sent_raw id=0x%X dlc=%s", arbitration_id, len(data))
    finally:
        bus.shutdown()


@ecu_app.command("set-speed")
def ecu_set_speed(
    channel: str = typer.Option("vcan0", "--channel"),
    interface: str = typer.Option("virtual", "--interface"),
    dbc: str = typer.Option(..., "--dbc"),
    kph: float = typer.Option(..., "--kph"),
    log_level: str = typer.Option("INFO", "--log-level"),
) -> None:
    setup_logging(level=log_level)
    database = load_dbc(dbc)
    frame_id, payload = build_message_data(dbc=database, message_name="VehicleCommand", signals={"SetSpeedKph": kph})
    bus = open_bus(interface=interface, channel=channel, receive_own_messages=False)
    try:
        msg = can.Message(arbitration_id=frame_id, is_extended_id=False, data=payload)
        bus.send(msg)
        logger.info("ecu_set_speed kph=%s id=0x%X", kph, frame_id)
    finally:
        bus.shutdown()


@sim_app.command("run")
def sim_run(
    channel: str = typer.Option("vcan0", "--channel"),
    interface: str = typer.Option("virtual", "--interface"),
    dbc: str = typer.Option(..., "--dbc"),
    log_level: str = typer.Option("INFO", "--log-level"),
) -> None:
    setup_logging(level=log_level)
    database = load_dbc(dbc)
    bus = open_bus(interface=interface, channel=channel, receive_own_messages=True)
    VirtualVehicle(bus=bus, dbc=database).run()

