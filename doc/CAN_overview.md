# Overview of CAN (Controller Area Network)

Controller Area Network (CAN) is a communication protocol designed for ECUs (Electronic Control Units) in vehicles to communicate with each other without a central computer.

A CAN network consists of:
- CAN Controller (in MCU)
- CAN Transceiver
- CAN Bus (2 physical wires)

Two main wires:
- CAN_H
- CAN_L

## CAN Message (CAN Frame)
CAN transmits data using frames.

A basic CAN frame includes:

| Field | Meaning |
|-------|--------|
| ID    | Message identifier |
| DLC   | Data Length Code   |
| Data  | Data bytes         |
| CRC   | Error checking     |

### CAN ID
This is the message identifier.

Example:
| CAN ID | Meaning         |
|--------|----------------|
| 0x100  | Vehicle Speed  |
| 0x200  | Engine RPM     |
| 0x300  | Gear position  |

### Data field
- Standard CAN has 8 bytes, CAN FD can have up to 64 bytes per frame.
- These bytes need a database file to decode and understand which signals they represent.

## DBC file

DBC file is a database describing CAN messages. This file helps you decode CAN frames according to the vehicle's specification.

Example:
- Raw frame:
    - ID: 0x100
    - DATA: 0A 3C
- DBC decode:
    - VehicleSpeed = 60 km/h

---

## Question
Is the DBC file provided by the customer (OEM, vehicle manufacturer)? If not, who is responsible for providing and updating the DBC file?

## Try decoding a CAN frame using DBC
You can use cantools to load the DBC file and try decoding a simulated frame:

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

You can change the data to try decoding other signals based on the DBC structure.

---

# Steps to acquire CAN frames

According to technical_proposal.md, the sequence is:

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
The vehicle has a CAN bus system, transmitting frames between ECUs (e.g., speed, RPM, light status, etc.).

### 2. CAN HW Interface
You need a hardware device (CAN HW Interface) to connect CarPC to the vehicle's CAN bus.
- Examples: USB-CAN, onboard CAN, PCIe CAN card, etc.
- This device is plugged into CarPC.

### 3. SocketCAN Interface
On Linux, install the SocketCAN driver so the OS recognizes the CAN HW Interface as a network interface (can0, vcan0, ...).
- SocketCAN allows Python (and other software) to communicate with CAN HW Interface via standard API.

### 4. python-can Adapter
In CarPC code, use the python-can library to create a Bus object, connecting to the interface (can0, vcan0, ...).
- python-can receives CAN frames from SocketCAN, processes them asynchronously (non-blocking).

### 5. cantools + DBC Decode
When a CAN frame is received, use cantools and the DBC file to decode the frame into real signals (speed, rpm, ...).
- DBC helps identify which frame contains which signals and how to decode them into physical values.

### 6. Signal Store
After decoding, store the signals in Signal Store.
- Signal Store keeps current values, history, and publishes events to other components (WebSocket, trigger engine, ...).

> Note: You need to continuously read data from the CAN bus, polling to receive data from CAN bus.

---

## Only send when changed (on_change mechanism)
According to technical_proposal.md, there is Signal Store and Trigger Engine:
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

- Signal Store keeps current values and history.
- Trigger Engine checks conditions (e.g., on_change, threshold, periodic) and only sends events when needed.
- Helps reduce network load, clients only receive when necessary.

---

## Sample code for processing flow

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

# Tổng quan về CAN (Controller Area Network)

Controller Area Network (CAN) là một communication protocol được thiết kế để các ECU (Electronic Control Unit) trong xe giao tiếp với nhau mà không cần máy tính trung tâm.

Một CAN network gồm:
- CAN Controller (trong MCU)
- CAN Transceiver
- CAN Bus (2 dây vật lý)

Hai dây chính:
- CAN_H
- CAN_L

## CAN Message (CAN Frame)
CAN sẽ truyền dữ liệu bằng frame.

Một CAN frame cơ bản gồm:

| Field | Ý nghĩa |
|-------|--------|
| ID    | Message identifier |
| DLC   | Data Length Code   |
| Data  | Data bytes         |
| CRC   | Error checking     |

### CAN ID
Nó là message identifier.

Ví dụ:
| CAN ID | Meaning         |
|--------|----------------|
| 0x100  | Vehicle Speed  |
| 0x200  | Engine RPM     |
| 0x300  | Gear position  |

### Data field
- CAN thông thường thì có 8 bytes, còn CAN FD thì sẽ có 64 bytes data ứng với mỗi frame.
- Những byte từ frame data này sẽ cần file database để decode để hiểu được các data đó là những giá trị của signal gì.

## DBC file

DBC file là database mô tả CAN message. File này giúp bạn giải mã đúng các frame CAN theo chuẩn của xe.

Ví dụ:
- Raw frame:
    - ID: 0x100
    - DATA: 0A 3C
- DBC decode:
    - VehicleSpeed = 60 km/h

---

## Question
File DBC này có phải được cung cấp từ khách hàng (OEM, nhà sản xuất xe) không? Nếu không, ai là người chịu trách nhiệm cung cấp và cập nhật file DBC?

## Thử nghiệm decode CAN frame bằng DBC
Bạn có thể dùng cantools để load file DBC và thử decode một frame giả lập:

```python
import cantools

# Load DBC file
db = cantools.database.load_file('vehicle.dbc')

# Giả lập một CAN frame (ID: 256, data: 0x0A 0x00 0x64 0x00 0x01 0x03 0x00 0x00)
frame_id = 256
data = bytes([0x0A, 0x00, 0x64, 0x00, 0x01, 0x03, 0x00, 0x00])

# Tìm message theo ID
msg = db.get_message_by_frame_id(frame_id)

# Decode
decoded = msg.decode(data)
print(decoded)  # {'VehicleSpeed': ..., 'EngineRPM': ..., ...}
```

Bạn có thể thay đổi data để thử decode các tín hiệu khác dựa trên cấu trúc DBC.

---

# Các bước lấy frame qua CAN

Dựa vào technical_proposal.md, sequence như sau:

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

## Giải thích chi tiết từng bước

### 1. Vehicle CAN Bus
Xe có hệ thống CAN bus, truyền các frame dữ liệu giữa các ECU (ví dụ: tốc độ, vòng tua, trạng thái đèn, v.v.).

### 2. CAN HW Interface
Cần một thiết bị phần cứng (CAN HW Interface) để kết nối CarPC với CAN bus của xe.
- Ví dụ: USB-CAN, onboard CAN, PCIe CAN card, v.v.
- Thiết bị này cắm vào CarPC.

### 3. SocketCAN Interface
Trên Linux, cài driver SocketCAN để hệ điều hành nhận diện CAN HW Interface như một network interface (can0, vcan0, ...).
- SocketCAN giúp Python (và các phần mềm khác) giao tiếp với CAN HW Interface qua API chuẩn.

### 4. python-can Adapter
Trong code CarPC, dùng thư viện python-can để tạo đối tượng Bus, kết nối với interface (can0, vcan0, ...).
- python-can sẽ nhận các frame CAN từ SocketCAN, xử lý theo kiểu async (không block).

### 5. cantools + DBC Decode
Khi nhận được frame CAN, dùng cantools và file DBC để giải mã frame thành tín hiệu thực (speed, rpm, ...).
- DBC giúp xác định frame nào chứa tín hiệu gì, cách giải mã ra giá trị vật lý.

### 6. Signal Store
Sau khi giải mã, lưu các tín hiệu vào Signal Store.
- Signal Store giúp lưu giá trị hiện tại, lịch sử, và phát pub/sub cho các thành phần khác (WebSocket, trigger engine, ...).

> Note: Cần phải liên tục đọc dữ liệu từ CAN bus, polling liên tục để nhận được các data từ CAN bus.

---

## Cơ chế chỉ gửi khi thay đổi (on_change)
Dựa trên technical_proposal.md, thì có phần Signal Store và Trigger Engine:
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

- Signal Store lưu giá trị hiện tại và lịch sử.
- Trigger Engine kiểm tra điều kiện (ví dụ: on_change, threshold, periodic) và chỉ bắn event khi cần.
- Giúp giảm tải mạng, client chỉ nhận khi thực sự cần thiết.

---

## Code mẫu mô tả luồng xử lý

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

## Tài liệu tham khảo
- [python-can docs](https://python-can.readthedocs.io/en/stable/)
- [python-can installation](https://python-can.readthedocs.io/en/stable/installation.html)
- [python-can configuration](https://python-can.readthedocs.io/en/stable/configuration.html)
- [python-can API](https://python-can.readthedocs.io/en/stable/api.html)
