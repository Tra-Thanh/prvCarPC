# Overview of CAN (Controller Area Network)

Controller Area Network (CAN) is a communication protocol designed for ECUs (Electronic Control Units) in vehicles to communicate with each other without a central computer.

A CAN network consists of:
- CAN Controller (in MCU)
- CAN Transceiver (CAN Transceiver is a hardware chip used to convert logical signals from the CAN controller into electrical signals on the CAN bus)
- CAN Bus (2 physical wires)

Two main wires:
- CAN_H
- CAN_L

## CAN Message (CAN Frame)
CAN transmits data using frames.

A basic CAN frame consists of:

| Field | Meaning |
|-------|---------|
| ID    | Message ID |
| DLC   | Data Length Code   |
| Data  | Data bytes         |
| CRC   | Error checking     |

A full CAN frame consists of:

| Field                 | Meaning                   | Example                   |   
|-----------------------|---------------------------|---------------------------|
| SOF                   | Start of Frame            | 0                         |
| Arbitration           | CAN ID (Message ID)       | 01100100011               |
| Control               | DLC (Data Length Code)    | 00001000                  |
| Data                  | Data (Data bytes)         | 11 22 33 44 55 66 77 88   |
| CRC                   | CRC (Error checking)      | 101010101010101           |
| ACK                   | Acknowledgement           | 1                         |
| EOF                   | End of Frame              |1111111                    |

- When developing or debugging CAN, developers do not work with CAN frames at the bit level (SOF, CRC, ACK...). That part is handled by the CAN controller.
- In practice, you only see the CAN ID + DLC + DATA (hex) of the Controller Area Network (CAN).
- E.g. can0  123   [8]  11 22 33 44 55 66 77 88
- 1 CAN Frame can contain 5–10 different signals within the same 8 bytes.

### CAN ID (Arbitration)
It is the message identifier.

Example:
| CAN ID | Meaning         |
|--------|-----------------|
| 0x100  | Vehicle Speed  |
| 0x200  | Engine RPM     |
| 0x300  | Gear position  |

### DLC (Control)
- DLC (Data Length Code) is a field in the CAN frame used to determine the number of data bytes.

### Data field
- Standard CAN has 8 bytes, while CAN FD can have up to 64 bytes of data per frame.
- These data bytes from the frame need a database file to decode to understand what signal values they represent.

### CRC
- Error checking bits
- CRC helps the ECU detect if the message was corrupted during transmission.

### ACK
- Acknowledgement signal that the message has been received.

## DBC file

DBC file (.dbc) is a database describing CAN messages. This file helps you correctly decode CAN frames according to the vehicle's standard.
- Message ID, Signal name, Start bit, Length, Factor, Offset, Unit.

Example:
- Raw frame:
    - ID: 0x100
    - DATA: 0A 3C
- DBC decode:
    - VehicleSpeed = 60 km/h

---

## Question
Is this DBC file provided by the customer (OEM, vehicle manufacturer)? If not, who is responsible for providing and updating the DBC file?

## Testing CAN frame decoding with DBC
You can use cantools to load the DBC file and test decoding a simulated frame:

```python
import cantools

# Load DBC file
db = cantools.database.load_file('vehicle.dbc')

# Simulate a CAN frame (ID: 256, data: 0x0A 0x00 0x64 0x00 0x01 0x03 0x00 0x00)
frame_id = 256
data = bytes([0x0A, 0x00, 0x64, 0x00, 0x01, 0x03, 0x00, 0x00])

# Find message by ID
msg = db.get_message_by_frame_id(frame_id)

# Decode
decoded = msg.decode(data)
print(decoded)  # {'VehicleSpeed': ..., 'EngineRPM': ..., ...}
```

You can change the data to test decoding other signals based on the DBC structure.

---

# Steps to get frames via CAN

Based on technical_proposal.md, the sequence is as follows:

```
┌─────────────┐    SocketCAN    ┌─────────────┐    Frames    ┌─────────────┐
│  Vehicle    │ ──────────────► │  CAN HW     │ ───────────► │  python-can │
│  CAN Bus    │    Interface    │  Interface  │   (async)    │  Adapter    │
└─────────────┘                 └─────────────┘              └──────┬──────┘
                                                                    │
                                                                    ▼
                                                             ┌─────────────┐
                                                             │  cantools   │
                                                             │  DBC Decode │
                                                             └──────┬──────┘
                                                                    │
                                                                    ▼
                                                             ┌─────────────┐
                                                             │  Signal     │
                                                             │  Store      │
                                                             └─────────────┘
```

## Detailed explanation of each step

### 1. Vehicle CAN Bus
The vehicle has a CAN bus system that transmits data frames between ECUs (e.g., speed, RPM, light status, etc.).

### 2. CAN HW Interface
A hardware device (CAN HW Interface) is needed to connect the CarPC to the vehicle's CAN bus.
- Examples: USB-CAN, onboard CAN, PCIe CAN card, etc.
- This device is plugged into the CarPC.

### 3. SocketCAN Interface
On Linux, install the SocketCAN driver so that the operating system recognizes the CAN HW Interface as a network interface (can0, vcan0, ...).
- SocketCAN allows Python (and other software) to communicate with the CAN HW Interface via standard API.

### 4. python-can Adapter
In the CarPC code, use the python-can library to create a Bus object, connecting to the interface (can0, vcan0, ...).
- python-can will receive CAN frames from SocketCAN, processing them asynchronously (non-blocking).

### 5. cantools + DBC Decode
When a CAN frame is received, use cantools and the DBC file to decode the frame into real signals (speed, rpm, ...).
- DBC helps identify which frame contains which signals and how to decode them into physical values.

### 6. Signal Store
After decoding, store the signals in the Signal Store.
- Signal Store helps store current values, history, and publish/subscribe for other components (WebSocket, trigger engine, ...).

> Note: It is necessary to continuously read data from the CAN bus, polling continuously to receive data from the CAN bus.

---

## On-change mechanism (only send when changed)
Based on technical_proposal.md, there are Signal Store and Trigger Engine:
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │                    CORE LAYER (Vehicle Data Processing)                    │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │  │
│  │  │ Message     │  │ Signal      │  │ Trigger     │  │ State       │       │  │
│  │  │ Decoder     │  │ Store       │  │ Engine      │  │ Manager     │       │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │  │
│  │         │                │                │                │              │  │
│  │         └────────────────┴────────────────┴────────────────┘              │  │
│  │                                   │                                        │  │
│  │                          Internal Event Bus                                │  │
│  └───────────────────────────────────┼───────────────────────────────────────┘  │

- Signal Store stores current and historical values.
- Trigger Engine checks conditions (e.g., on_change, threshold, periodic) and only fires events when necessary.
- Helps reduce network load, clients only receive when truly needed.

---

## Sample code describing the processing flow

```python
import asyncio
import can
import cantools

class CANAdapter:
    def __init__(self, channel, dbc_path, bustype="socketcan"):
        self.channel = channel
        self.bustype = bustype
        self.db = cantools.database.load_file(dbc_path)
        self._bus = None
        self._running = False
        self._callbacks = []

    async def start(self):
        self._bus = can.Bus(channel=self.channel, bustype=self.bustype, fd=True)
        self._running = True
        asyncio.create_task(self._receive_loop())

    async def _receive_loop(self):
        reader = can.AsyncBufferedReader()
        notifier = can.Notifier(self._bus, [reader], loop=asyncio.get_event_loop())
        try:
            while self._running:
                msg = await reader.get_message()
                await self._process_message(msg)
        finally:
            notifier.stop()

    async def _process_message(self, msg):
        try:
            db_msg = self.db.get_message_by_frame_id(msg.arbitration_id)
            decoded = db_msg.decode(msg.data)
            for callback in self._callbacks:
                await callback(db_msg.name, decoded)
        except KeyError:
            pass

    def subscribe(self, callback):
        self._callbacks.append(callback)

    async def stop(self):
        self._running = False
        if self._bus:
            self._bus.shutdown()
```

---

## References
- [python-can docs](https://python-can.readthedocs.io/en/stable/)
- [python-can installation](https://python-can.readthedocs.io/en/stable/installation.html)
- [python-can configuration](https://python-can.readthedocs.io/en/stable/configuration.html)
- [python-can API](https://python-can.readthedocs.io/en/stable/api.html)