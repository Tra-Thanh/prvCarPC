# Tổng quan về CAN (Controller Area Network)

Controller Area Network (CAN) là một communication protocol được thiết kế để các ECU (Electronic Control Unit) trong xe giao tiếp với nhau mà không cần máy tính trung tâm.

Một CAN network gồm:
- CAN Controller (trong MCU)
- CAN Transceiver (CAN Transceiver là một chip phần cứng dùng để chuyển đổi tín hiệu logic từ CAN controller thành tín hiệu điện trên bus CAN)
- CAN Bus (2 dây vật lý)

Hai dây chính:
- CAN_H
- CAN_L

## CAN Message (CAN Frame)
CAN sẽ truyền dữ liệu bằng frame.

Một CAN frame cơ bản gồm:

| Field | Ý nghĩa |
|-------|--------|
| ID    | Message ID |
| DLC   | Data Length Code   |
| Data  | Data bytes         |
| CRC   | Error checking     |

Một CAN frame đầy đủ gồm:

| Field                 | Ý nghĩa                   | Example                   |   
|-----------------------|---------------------------|---------------------------|
| SOF                   | Start of Frame            | 0                         |
| Arbitration           | CAN ID (Mesage ID)        | 01100100011               |
| Control               | DLC (Data Length Code)    | 00001000                  |
| Data                  | Data (Data bytes)         | 11 22 33 44 55 66 77 88   |
| CRC                   | CRC (Error checking)      | 101010101010101           |
| ACK                   | Acknowledgement           | 1                         |
| EOF                   | Start of Frame            |1111111                    |

- Khi develop hoặc debug CAN, developer không làm việc với CAN frame ở mức bit (SOF, CRC, ACK…). Phần đó do CAN controller xử lý.
- Trong thực tế bạn chỉ thấy CAN ID + DLC + DATA (hex) của Controller Area Network (CAN).
- E.g. can0  123   [8]  11 22 33 44 55 66 77 88
- 1 CAN Frame có thể chứa 5–10 signal khác nhau trong cùng 8 byte.


### CAN ID (Arbitration)
Nó là message identifier.

Ví dụ:
| CAN ID | Meaning         |
|--------|----------------|
| 0x100  | Vehicle Speed  |
| 0x200  | Engine RPM     |
| 0x300  | Gear position  |
- 
### DLC (Control)
- DLC (Data Length Code) là trường trong CAN frame dùng để xác định số byte dữ liệu (data bytes)

### Data field
- CAN thông thường thì có 8 bytes, còn CAN FD thì sẽ có 64 bytes data ứng với mỗi frame.
- Những byte từ frame data này sẽ cần file database để decode để hiểu được các data đó là những giá trị của signal gì.

### CRC
- Các bit kiểm tra lỗi
- CRC giúp ECU nhận biết message có bị lỗi trong quá trình truyền hay không.

### ACK
- Tín hiệu xác nhận message đã được nhận.

## DBC file

DBC file (.dbc) là database mô tả CAN message. File này giúp bạn giải mã đúng các frame CAN theo chuẩn của xe.
- Message ID, Signal name, Start bit, Length, Factor, Offset, Unit.

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
