# DBC File Format – Components and Explanations

The **DBC (Database CAN)** file is a text format used to describe **messages** and **signals** on the CAN bus. Tools like **CANalyzer**, **Vector**, **cantools**, etc., use DBC to decode/encode CAN data.

Below lists the **main components** in the DBC file and the meaning of each part.

---

## 1. Overview of DBC Structure

A DBC file typically consists of blocks (not all are mandatory):

| Component         | Keyword                           | Short Description                                           |
|-------------------|-----------------------------------|-------------------------------------------------------------|
| Version           | `VERSION`                         | DBC version note                                             |
| New Symbol        | `NS_`                             | Declaration of keywords / namespace                         |
| Bus               | `BS_`                             | Bus parameters (optional)                                   |
| Network Nodes     | `BU_`                             | List of ECUs / nodes on the network                         |
| Message           | `BO_`                             | Message definition (ID, DLC, name, sending node)            |
| Signal            | `SG_`                             | Signal definition within message                            |
| Comment           | `CM_`                             | Comment for node, message, signal                           |
| Attributes        | `BA_DEF_`, `BA_DEF_DEF_`, `BA_`   | Attribute definition and value assignment                   |
| Value Descriptions | `VAL_`                            | Map raw values → text descriptions (enum)                   |
| Environment Variables | `EV_`                         | Environment variables (rarely used in standard CAN reading applications) |

---

## 2. Details of Each Component

### 2.1. `VERSION` – Version

- **Purpose**: Version note or DBC information (does not affect decode logic).
- **Example**:
  VERSION "MyCar_2024_v1"

---

### 2.2. `NS_` – New Symbol (namespace / keywords)

- **Purpose**: Declares special keywords used in the file (e.g., `NS_DESC_`, `CM_`, `BA_DEF_`, …). Usually available in standard templates.
- **Example**:
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

- **Purpose**: Declares bus parameters (optional). Often left blank or a single line.
- **Example**:
  BS_:

---

### 2.4. `BU_` – Bus nodes (ECU / Node)

- **Purpose**: Lists all **nodes** (ECUs) on the CAN network. Each node can be a sender/receiver of messages.
- **Syntax**: `BU_: <node_name1> <node_name2> ...`
- **Example**:
  BU_: EngineECU Gateway BodyECU BCM_ECU

---

### 2.5. `BO_` – Message (CAN frame)

- **Purpose**: Defines a **message** (a type of CAN frame), including:
  - **Message ID** (arbitration ID).
  - **Message name**.
  - **DLC** (number of data bytes, 0–8 or 0–64 with CAN FD).
  - **Sending node** (sender).
- **Syntax**:  
  `BO_ <MessageId> <MessageName>: <DLC> <Sender>`
- **Example**:
  BO_ 256 EngineStatus: 8 Engine
  BO_ 512 VehicleSpeed: 8 ECU

  Meaning: message with ID 256, name `EngineStatus`, 8 bytes, sent by node `Engine`.

---

### 2.6. `SG_` – Signal

- **Purpose**: Defines a **signal** within a message. Describes:
  - Which bit it starts at, how many bits long.
  - Byte order (Motorola / Intel).
  - Type: unsigned/signed.
  - Scale factor and offset to convert raw value → physical value.
  - Unit, min/max (physical).
  - Receiving nodes (can be multiple).

- **Syntax**:  
  `SG_ <SignalName> : <StartBit>|<Length>@<ByteOrder><ValueType> (<Factor>,<Offset>) [<Min>|<Max>] "<Unit>" <Receiver1> [, <Receiver2> ...]`
  - **ByteOrder**: `0` = Big Endian (Motorola), `1` = Little Endian (Intel).
  - **ValueType**: `+` = unsigned, `-` = signed.
  - **Physical Value** = Raw Value × Factor + Offset

- **Example**:
  SG_ EngineSpeed : 0|16@1+ (1,0) [0|8000] "rpm" ECU,Gateway
  SG_ VehicleSpeed : 16|16@1+ (0.01,0) [0|300] "km/h" ECU,Gateway,BCM

  - `EngineSpeed`: starts at bit 0, 16 bits long, Intel, unsigned, factor=1, offset=0, unit "rpm", sent to ECU, Gateway.
  - `VehicleSpeed`: starts at bit 16, 16 bits, scale 0.01 → physical value = raw * 0.01 km/h.

---

### 2.7. `CM_` – Comment

- **Purpose**: Attaches **comments** to nodes, messages, or signals.
- **Syntax**:
  - Comment for node:   `CM_ BU_ <NodeName> "<Comment>";`
  - Comment for message: `CM_ BO_ <MessageId> "<Comment>";`
  - Comment for signal:  `CM_ SG_ <MessageId> <SignalName> "<Comment>";`
- **Example**:
  CM_ BO_ 256 "Engine status from ECU, 10ms period";
  CM_ SG_ 256 EngineSpeed "Crankshaft speed";

---

### 2.8. `BA_DEF_` and `BA_` – Attributes

- **`BA_DEF_`**: Defines an **attribute** (name, type, applies to which objects: node, message, signal, …).
- **`BA_DEF_DEF_`**: Default value of the attribute.
- **`BA_`**: Assigns **value** of attribute to a specific node/message/signal.
- **Example**:
  BA_DEF_ BO_ "GenMsgCycleTime" INT 0 1000;
  BA_DEF_DEF_ "GenMsgCycleTime" 100;
  BA_ "GenMsgCycleTime" BO_ 256 10;

  Meaning: attribute `GenMsgCycleTime` (integer 0–1000) for messages; default 100; for message 256 = 10 (ms).

---

### 2.9. `VAL_` – Value description (enum / value table)

- **Purpose**: Attaches **text descriptions** to each numeric value of a signal (enum). Used to display states (e.g., 0 = "Off", 1 = "On").
- **Syntax**:  
  `VAL_ <MessageId> <SignalName> <Value0> "<Description0>" <Value1> "<Description1>" ... ;`
- **Example**:
  VAL_ 512 IgnitionSwitch 0 "Off" 1 "Acc" 2 "On" 3 "Start";
  VAL_ 256 EngineState 0 "Stopped" 1 "Running" 2 "Cranking";

---

### 2.10. `VAL_TABLE_` – Shared value table

- **Purpose**: Defines a **shared enum table**, which can then be referenced by multiple signals (via attributes or tool support).
- **Syntax**:  
  `VAL_TABLE_ <TableName> <Value0> "<Description0>" <Value1> "<Description1>" ... ;`

---

### 2.11. `EV_` – Environment variable

- **Purpose**: Declares **environment variables** (usually used in measurement/test tools, rarely used when only reading CAN for logging). Can be ignored if only interested in messages/signals.

---

### 2.12. Other components (less common)

- **`SGTYPE_`**, **`SIG_TYPE_REF_`**: Custom signal types / type references.
- **`SIG_GROUP_`**: Signal groups within a message (for display/grouping in tools).
- **`SIG_VALTYPE_`**: Extended data types for signals (float, double, …).
- **`BO_TX_BU_`**: Assigns messages to specific transmit buffers (in multi-buffer environments).

In CarPC applications that only **read and decode** CAN, usually only need to care about: **`BO_`**, **`SG_`**, **`VAL_`**, and **`CM_`** (for displaying descriptions).

---

## 3. Minimal DBC File Example

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

---

## 4. Using DBC in CarPC CAN Project

- **Read DBC file**: use **cantools** library (Python):
  import cantools
  db = cantools.database.load_file("my_car.dbc")
  
- **Decode frame**: after receiving `can.Message` (ID + data bytes), call:
  decoded = db.decode_message(msg.arbitration_id, msg.data)
  # decoded = {"EngineSpeed": 1234, "CoolantTemp": 85, "EngineState": 1}

- **Encode message**: when needing to send frame from physical values:
  data = db.encode_message("EngineStatus", {"EngineSpeed": 2000, "CoolantTemp": 90, "EngineState": 1})

This document lists and explains the components in the DBC file; when you have the actual DBC file of the vehicle/system, you can compare each line with the above sections to understand the meaning.