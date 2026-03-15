# Định dạng file DBC – Các thành phần và giải thích

File **DBC (Database CAN)** là định dạng văn bản dùng để mô tả **message** và **signal** trên bus CAN. Các công cụ như **CANalyzer**, **Vector**, **cantools**, v.v. dùng DBC để decode/encode dữ liệu CAN.

Dưới đây liệt kê các **thành phần chính** trong file DBC và ý nghĩa của từng phần.

---

## 1. Tổng quan cấu trúc DBC

Một file DBC thường gồm các khối (không bắt buộc phải có đủ tất cả):

| Thành phần        | Từ khóa                           | Mô tả ngắn                                                    |
|-------------------|-----------------------------------|---------------------------------------------------------------|
| Version           | `VERSION`                         | Ghi chú phiên bản DBC                                         |
| New Symbol        | `NS_`                             | Khai báo từ khóa / namespace                                  |
| Bus               | `BS_`                             | Tham số bus (không bắt buộc)                                  |
| Node mạng         | `BU_`                             | Danh sách ECU / node trên mạng                                |
| Message           | `BO_`                             | Định nghĩa message (ID, DLC, tên, node gửi)                   |
| Signal            | `SG_`                             | Định nghĩa signal trong message                               |
| Comment           | `CM_`                             | Comment cho node, message, signal                             |
| Thuộc tính        | `BA_DEF_`, `BA_DEF_DEF_`, `BA_`   | Định nghĩa và gán giá trị thuộc tính                          |
| Mô tả giá trị     | `VAL_`                            | Map giá trị raw → mô tả văn bản (enum)                        |
| Biến môi trường   | `EV_`                             | Biến môi trường (ít dùng trong ứng dụng đọc CAN thông thường) |

---

## 2. Chi tiết từng thành phần

### 2.1. `VERSION` – Phiên bản

- **Mục đích**: Ghi chú phiên bản hoặc thông tin DBC (không ảnh hưởng logic decode).
- **Ví dụ**:
  VERSION "MyCar_2024_v1"

---

### 2.2. `NS_` – New Symbol (namespace / từ khóa)

- **Mục đích**: Khai báo các từ khóa đặc biệt được dùng trong file (ví dụ `NS_DESC_`, `CM_`, `BA_DEF_`, …). Thường có sẵn trong template chuẩn.
- **Ví dụ**:
  NS_ :
      NS_DESC_
      CM_
      BA_DEF_
      BA_
      VAL_
      CAT_DEF_
      CAT_
      FILTER
      BA_DEF_DEF_
      EV_DATA_
      ENVVAR_DATA_
      SGTYPE_
      SGTYPE_VAL_
      BA_DEF_SGTYPE_
      BA_SGTYPE_
      SIG_TYPE_REF_
      VAL_TABLE_
      SIG_GROUP_
      SIG_VALTYPE_
      SIGTYPE_VALTYPE_
      BO_TX_BU_
      SG_MUL_VAL_

---

### 2.3. `BS_` – Bus configuration

- **Mục đích**: Khai báo tham số bus (tùy chọn). Thường để trống hoặc một dòng đơn.
- **Ví dụ**:
  BS_:

---

### 2.4. `BU_` – Bus nodes (ECU / Node)

- **Mục đích**: Liệt kê tất cả **node** (ECU) có trên mạng CAN. Mỗi node có thể là người gửi/nhận message.
- **Cú pháp**: `BU_: <tên_node1> <tên_node2> ...`
- **Ví dụ**:
  BU_: EngineECU Gateway BodyECU BCM_ECU

---

### 2.5. `BO_` – Message (CAN frame)

- **Mục đích**: Định nghĩa một **message** (một loại frame CAN), gồm:
  - **Message ID** (arbitration ID).
  - **Tên message**.
  - **DLC** (số byte dữ liệu, 0–8 hoặc 0–64 với CAN FD).
  - **Node gửi** (sender).
- **Cú pháp**:  
  `BO_ <MessageId> <MessageName>: <DLC> <Sender>`
- **Ví dụ**:
  BO_ 256 EngineStatus: 8 Engine
  BO_ 512 VehicleSpeed: 8 ECU

  Nghĩa: message có ID 256, tên `EngineStatus`, 8 byte, do node `Engine` gửi.

---

### 2.6. `SG_` – Signal

- **Mục đích**: Định nghĩa một **signal** nằm **trong** một message. Mô tả:
  - Signal nằm ở bit nào, dài bao nhiêu bit.
  - Byte order (Motorola / Intel).
  - Kiểu: unsigned/signed.
  - Hệ số scale và offset để chuyển giá trị raw → giá trị vật lý.
  - Đơn vị (unit), min/max (vật lý).
  - Node nhận (receiver), có thể nhiều node.

- **Cú pháp**:  
  `SG_ <SignalName> : <StartBit>|<Length>@<ByteOrder><ValueType> (<Factor>,<Offset>) [<Min>|<Max>] "<Unit>" <Receiver1> [, <Receiver2> ...]`
  - **ByteOrder**: `0` = Big Endian (Motorola), `1` = Little Endian (Intel).
  - **ValueType**: `+` = unsigned, `-` = signed.
  - **Physical Value** = Raw Value × Factor + Offset

- **Ví dụ**:
  SG_ EngineSpeed : 0|16@1+ (1,0) [0|8000] "rpm" ECU,Gateway
  SG_ VehicleSpeed : 16|16@1+ (0.01,0) [0|300] "km/h" ECU,Gateway,BCM

  - `EngineSpeed`: bắt đầu bit 0, dài 16 bit, Intel, unsigned, factor=1, offset=0, đơn vị "rpm", gửi tới ECU, Gateway.
  - `VehicleSpeed`: bắt đầu bit 16, 16 bit, scale 0.01 → giá trị vật lý = raw * 0.01 km/h.

---

### 2.7. `CM_` – Comment 

- **Mục đích**: Gắn **comment** cho node, message hoặc signal.
- **Cú pháp**:
  - Comment cho node:   `CM_ BU_ <NodeName> "<Comment>";`
  - Comment cho message: `CM_ BO_ <MessageId> "<Comment>";`
  - Comment cho signal:  `CM_ SG_ <MessageId> <SignalName> "<Comment>";`
- **Ví dụ**:
  CM_ BO_ 256 "Engine status from ECU, 10ms period";
  CM_ SG_ 256 EngineSpeed "Crankshaft speed";

---

### 2.8. `BA_DEF_` và `BA_` – Thuộc tính (Attribute)

- **`BA_DEF_`**: Định nghĩa **thuộc tính** (tên, kiểu, áp dụng cho đối tượng nào: node, message, signal, …).
- **`BA_DEF_DEF_`**: Giá trị mặc định của thuộc tính.
- **`BA_`**: Gán **giá trị** thuộc tính cho một node/message/signal cụ thể.
- **Ví dụ**:
  BA_DEF_ BO_ "GenMsgCycleTime" INT 0 1000;
  BA_DEF_DEF_ "GenMsgCycleTime" 100;
  BA_ "GenMsgCycleTime" BO_ 256 10;

  Nghĩa: thuộc tính `GenMsgCycleTime` (số nguyên 0–1000) cho message; mặc định 100; với message 256 thì = 10 (ms).

---

### 2.9. `VAL_` – Value description (enum / bảng giá trị)

- **Mục đích**: Gắn **mô tả chữ** cho từng giá trị số của một signal (enum). Dùng để hiển thị trạng thái (e.g. 0 = "Off", 1 = "On").
- **Cú pháp**:  
  `VAL_ <MessageId> <SignalName> <Value0> "<Mô tả0>" <Value1> "<Mô tả1>" ... ;`
- **Ví dụ**:
  VAL_ 512 IgnitionSwitch 0 "Off" 1 "Acc" 2 "On" 3 "Start";
  VAL_ 256 EngineState 0 "Stopped" 1 "Running" 2 "Cranking";

---

### 2.10. `VAL_TABLE_` – Bảng giá trị dùng chung

- **Mục đích**: Định nghĩa một **bảng enum** dùng chung, sau đó có thể tham chiếu từ nhiều signal (thông qua thuộc tính hoặc cách hỗ trợ của từng tool).
- **Cú pháp**:  
  `VAL_TABLE_ <TênBảng> <Value0> "<Mô tả0>" <Value1> "<Mô tả1>" ... ;`

---

### 2.11. `EV_` – Environment variable

- **Mục đích**: Khai báo **biến môi trường** (thường dùng trong công cụ đo/test, ít dùng khi chỉ đọc CAN để log). Có thể bỏ qua khi chỉ quan tâm message/signal.

---

### 2.12. Các thành phần khác (ít gặp hơn)

- **`SGTYPE_`**, **`SIG_TYPE_REF_`**: Kiểu signal tùy chỉnh / tham chiếu kiểu.
- **`SIG_GROUP_`**: Nhóm signal trong một message (để hiển thị/nhóm trong tool).
- **`SIG_VALTYPE_`**: Kiểu dữ liệu mở rộng cho signal (float, double, …).
- **`BO_TX_BU_`**: Gắn message với buffer truyền cụ thể (trong môi trường multi-buffer).

Trong ứng dụng CarPC chỉ **đọc và decode** CAN, thường chỉ cần quan tâm: **`BO_`**, **`SG_`**, **`VAL_`**, và **`CM_`** (để hiển thị mô tả).

---

## 3. Ví dụ file DBC tối giản

VERSION ""

NS_ :
    CM_
    BA_DEF_
    BA_
    VAL_

BS_:

BU_: Engine ECU Gateway

BO_ 256 EngineStatus: 8 Engine
 SG_ EngineSpeed : 0|16@1+ (1,0) [0|8000] "rpm" ECU,Gateway
 SG_ CoolantTemp : 16|8@1+ (1,-40) [-40|215] "degC" ECU,Gateway
 SG_ EngineState : 24|2@1+ (1,0) [0|3] "" ECU,Gateway

BO_ 512 VehicleSpeed: 8 ECU
 SG_ Speed : 0|16@1+ (0.01,0) [0|300] "km/h" ECU,Gateway

CM_ BO_ 256 "Engine status, 10ms";
CM_ SG_ 256 EngineSpeed "Crankshaft speed";

VAL_ 256 EngineState 0 "Stopped" 1 "Running" 2 "Cranking" 3 "Reserved";
```

---

## 4. Dùng DBC trong dự án CarPC CAN

- **Đọc file DBC**: dùng thư viện **cantools** (Python):
  import cantools
  db = cantools.database.load_file("my_car.dbc")
  
- **Decode frame**: sau khi nhận được `can.Message` (ID + data bytes), gọi:
  decoded = db.decode_message(msg.arbitration_id, msg.data)
  # decoded = {"EngineSpeed": 1234, "CoolantTemp": 85, "EngineState": 1}

- **Encode message**: khi cần gửi frame từ giá trị vật lý:
  data = db.encode_message("EngineStatus", {"EngineSpeed": 2000, "CoolantTemp": 90, "EngineState": 1})

Tài liệu này liệt kê và giải thích các thành phần trong file DBC; khi có file DBC thực tế của xe/hệ thống, bạn có thể đối chiếu từng dòng với các mục trên để hiểu ý nghĩa.
