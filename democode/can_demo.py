"""
CAN Demo on Windows - Single file
====================================
Simulate carpc_can_architecture.puml architecture:

    [ECU Simulator] --> virtual CAN bus --> [CANBus] --> [Processor] --> [Storage] --> JSON log

Run on Windows using python-can virtual interface (no SocketCAN, no device required).
Use threading instead of asyncio to avoid compatibility issues on Windows.

Install:
        pip install python-can cantools

Run:
        python demo_can_win.py
"""

import json
import logging
import random
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import can
import cantools

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DBC_PATH = Path(__file__).parent / "dbc/vehicle.dbc"
LOG_PATH = Path(__file__).parent / "can_frames.jsonl"
VIRTUAL_CHANNEL = "carpc_demo"
SEND_INTERVAL = 0.5   # seconds - ECU sends frame every 0.5s
MAX_CYCLES = 20       # number of cycles to send for demo (None = run forever)

# ---------------------------------------------------------------------------
 # Environment switching
# - False (default): Windows, use virtual bus + threading
# - True           : Linux, use SocketCAN (can0) + threading
#   When True: disable ECU Simulator because real vehicle sends frames
USE_SOCKETCAN = True
SOCKETCAN_CHANNEL = "can0"  # interface on Linux

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
log_file_path = Path(__file__).parent / "demo_log.txt"

# Create handlers: console and file
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler(log_file_path, encoding="utf-8")

formatter = logging.Formatter(
    fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)

logger = logging.getLogger("carpc.demo")


 # ===========================================================================
# MODULE 1: CANBus - connect and receive frames (equivalent to carpc_can.can_bus)
# ===========================================================================
class CANBus:
    """
    Connect to CAN bus.
    Automatically select interface based on USE_SOCKETCAN flag:

    USE_SOCKETCAN=False (Windows demo):
        can.Bus(interface="virtual", channel=VIRTUAL_CHANNEL)

    USE_SOCKETCAN=True (Linux production):
        can.Bus(channel="can0", bustype="socketcan")
        → This is exactly the code in can_adapter.py of CarPC-main
    """

    def connect(self) -> can.Bus:
        if USE_SOCKETCAN:
            bus = can.Bus(channel=SOCKETCAN_CHANNEL, bustype="socketcan")
            logger.info(f"[CANBus] Connected to SocketCAN: channel='{SOCKETCAN_CHANNEL}'")
        else:
            bus = can.Bus(interface="virtual", channel=VIRTUAL_CHANNEL)
            logger.info(f"[CANBus] Connected to virtual bus: channel='{VIRTUAL_CHANNEL}'")
        return bus


 # ===========================================================================
# MODULE 2: Processor - decode CAN frame using DBC (carpc_can.processor)
# ===========================================================================
class Processor:
    """
    Receive raw CAN frame, decode signals using DBC file.
    """

    def __init__(self, dbc_path: Path):
        if not dbc_path.exists():
            raise FileNotFoundError(f"DBC file not found: {dbc_path.resolve()}")
        self.db = cantools.database.load_file(str(dbc_path))
        msg_names = [m.name for m in self.db.messages]
        logger.info(f"[Processor] DBC loaded: {len(self.db.messages)} messages -> {msg_names}")

    def process(self, msg: can.Message) -> dict[str, Any] | None:
        """
        Decode a CAN frame.
        Returns a dict with message_name, signals, timestamp.
        Returns None if ID not found in DBC.
        """
        try:
            db_msg = self.db.get_message_by_frame_id(msg.arbitration_id)
            decoded = db_msg.decode(msg.data, decode_choices=True)
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "message_name": db_msg.name,
                "frame_id": hex(msg.arbitration_id),
                "signals": {k: (float(v) if isinstance(v, (int, float)) else str(v))
                            for k, v in decoded.items()},
            }
        except KeyError:
            logger.debug(f"[Processor] ID {hex(msg.arbitration_id)} not found in DBC, skipped.")
            return None
        except Exception as e:
            logger.warning(f"[Processor] Decode error ID {hex(msg.arbitration_id)}: {e}")
            return None


 # ===========================================================================
# MODULE 3: Storage - store signals in memory and JSON log (carpc_can.storage)
# ===========================================================================
class Storage:
    """
    Store decoded signals:
    - In-memory: dict signal_name -> latest value
    - JSON log file: each line is a record (JSONL format)
    """

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self._current: dict[str, Any] = {}   # signal name -> latest value
        self._log_file = open(log_path, "a", encoding="utf-8")
        logger.info(f"[Storage] JSON log: {log_path.resolve()}")

    def append(self, record: dict[str, Any]):
        """Store record in memory and write to JSON log file."""
        # Update in-memory store
        for sig_name, sig_val in record["signals"].items():
            self._current[sig_name] = sig_val

        # Write to JSONL file
        self._log_file.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._log_file.flush()

    def get_current(self, signal_name: str) -> Any:
        return self._current.get(signal_name)

    def get_all_current(self) -> dict[str, Any]:
        return dict(self._current)

    def close(self):
        self._log_file.close()


 # ===========================================================================
# ECU Simulator - simulate vehicle sending CAN frames (replace real vehicle)
# ===========================================================================
class ECUSimulator:
    """
    Simulate ECU broadcasting CAN frames to virtual bus.
    On real vehicle, this part is not needed - CarPC only reads passively.
    """

    def __init__(self, bus: can.Bus, db: cantools.database.Database):
        self.bus = bus
        self.db = db
        self._frame_count = 0

    def _random_vehicle_status(self) -> dict:
        return {
            "VehicleSpeed": round(random.uniform(0, 120), 1),
            "EngineRPM": random.randint(800, 4000),
            "BatteryVoltage": round(random.uniform(11.5, 14.5), 1),
            "IgnitionStatus": 2,   # On
            "GearPosition": random.randint(0, 4),
        }

    def _random_climate(self) -> dict:
        # AmbientTemp: signed 8-bit, factor=0.5, offset=-40
        # Raw max = 127 → physical max = 127*0.5 - 40 = 23.5°C
        return {
            "ACStatus": random.randint(0, 1),
            "FanSpeed": random.randint(1, 8),
            "TargetTempDriver": round(random.uniform(18, 28), 1),
            "TargetTempPassenger": round(random.uniform(18, 28), 1),
            "AmbientTemp": round(random.uniform(-10, 23), 1),
        }

    def _random_dms(self) -> dict:
        return {
            "DriverPresent": 1,
            "DriverAttention": random.randint(1, 3),
            "DrowsinessLevel": random.randint(0, 5),
            "GazeDirection": random.randint(0, 180),
            "HeadPoseYaw": round(random.uniform(-30, 30), 1),
            "HeadPosePitch": round(random.uniform(-15, 15), 1),
            "EyeOpenness": round(random.uniform(60, 100), 1),
        }

    def send_all(self):
        """Send all messages in one cycle."""
        messages_to_send = [
            ("VehicleStatus", self._random_vehicle_status()),
            ("ClimateControl", self._random_climate()),
            ("DMSStatus", self._random_dms()),
        ]
        for msg_name, signals in messages_to_send:
            try:
                db_msg = self.db.get_message_by_name(msg_name)
                data = db_msg.encode(signals)
                frame = can.Message(
                    arbitration_id=db_msg.frame_id,
                    data=data,
                    is_extended_id=False,
                )
                self.bus.send(frame)
            except Exception as e:
                logger.warning(f"[ECU] Send {msg_name} error: {e}")
        self._frame_count += 1


 # ===========================================================================
# MODULE 4: App - orchestrate everything (carpc_can.app)
# ===========================================================================
class App:
    """
    Orchestrate the whole flow using 2 threads (stable on Windows):

    Thread sender  : ECU Simulator sends frames → sender_bus
    Thread receiver: CarPC receives frames ← receiver_bus → decode → storage

    python-can virtual bus: sender_bus and receiver_bus use same channel
    → frames sent by sender are received by receiver.

    When deploying to real Linux:
    - Change CANBus.connect() to use bustype="socketcan", channel="can0"
    - Remove sender_thread (real vehicle sends frames)
    """

    def __init__(self):
        self.processor = Processor(DBC_PATH)
        self.storage   = Storage(LOG_PATH)
        self._sender_bus:   can.Bus | None = None
        self._receiver_bus: can.Bus | None = None
        self._stop = threading.Event()
        self._frame_count = 0

    def _sender_thread(self):
        """ECU thread: periodically send frames to virtual bus."""
        simulator = ECUSimulator(self._sender_bus, self.processor.db)
        logger.info("[ECU] Start sending frames...")
        while not self._stop.is_set():
            if MAX_CYCLES and simulator._frame_count >= MAX_CYCLES:
                logger.info(f"[ECU] Sent {MAX_CYCLES} cycles. Stopping.")
                self._stop.set()
                break
            simulator.send_all()
            time.sleep(SEND_INTERVAL)

    def _receiver_thread(self):
        """CarPC thread: receive frames, decode, store."""
        logger.info("[CarPC] Start receiving frames from virtual bus...")
        while not self._stop.is_set():
            msg = self._receiver_bus.recv(timeout=0.5)
            if msg is None:
                continue
            record = self.processor.process(msg)
            if record:
                self.storage.append(record)
                self._frame_count += 1
                sigs = ", ".join(f"{k}={v}" for k, v in record["signals"].items())
                logger.info(
                    f"[CarPC] #{self._frame_count:03d} "
                    f"{record['message_name']} ({record['frame_id']}): {sigs}"
                )

    def run(self):
        logger.info("=" * 65)
        logger.info("  CarPC CAN Demo - Windows (python-can virtual bus)")
        logger.info(f"  DBC : {DBC_PATH.resolve()}")
        logger.info(f"  Log : {LOG_PATH.resolve()}")
        logger.info("=" * 65)

        # 2 bus instances with same channel: sender sends, receiver receives
        can_bus = CANBus()
        self._receiver_bus = can_bus.connect()

        if USE_SOCKETCAN:
            # Linux/vcan: fake data (dev/test)
            self._sender_bus = can.Bus(channel=SOCKETCAN_CHANNEL, bustype="socketcan")
            t_recv = threading.Thread(target=self._receiver_thread, name="receiver", daemon=True)
            t_send = threading.Thread(target=self._sender_thread,   name="sender",   daemon=True)
            t_recv.start()
            time.sleep(0.05)
            t_send.start()
            logger.info("[App] SocketCAN mode: sending & receiving on can0 (vcan for dev/test)")
            try:
                while not self._stop.is_set():
                    time.sleep(0.1)
            except KeyboardInterrupt:
                logger.info("[App] Stopped by user (Ctrl+C).")
                self._stop.set()
            t_send.join(timeout=2)
            t_recv.join(timeout=2)
            if self._sender_bus:
                self._sender_bus.shutdown()
        else:
            # Windows: use ECU Simulator + virtual bus
            self._sender_bus = can.Bus(interface="virtual", channel=VIRTUAL_CHANNEL)
            t_recv = threading.Thread(target=self._receiver_thread, name="receiver", daemon=True)
            t_send = threading.Thread(target=self._sender_thread,   name="sender",   daemon=True)
            t_recv.start()
            time.sleep(0.05)   # ensure receiver is ready before sender
            t_send.start()
            try:
                while not self._stop.is_set():
                    time.sleep(0.1)
            except KeyboardInterrupt:
                logger.info("[App] Stopped by user (Ctrl+C).")
                self._stop.set()
            t_send.join(timeout=2)
            t_recv.join(timeout=2)
            if self._sender_bus:
                self._sender_bus.shutdown()

        self._receiver_bus.shutdown()
        self.storage.close()
        self._summary()

    def _summary(self):
        logger.info("=" * 65)
        logger.info(f"  Total frames received & decoded : {self._frame_count}")
        logger.info("  Latest signal values:")
        for name, val in self.storage.get_all_current().items():
            logger.info(f"    {name:35s}: {val}")
        logger.info(f"  JSON log : {LOG_PATH.resolve()}")
        logger.info("=" * 65)


# ===========================================================================
# Entry point
# ===========================================================================
if __name__ == "__main__":
    App().run()
