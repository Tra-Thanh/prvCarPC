# prvCarPC (carPC)

Toolkit carPC chuyên sâu cho CAN/ECU:

- Thu thập dữ liệu CAN từ xe (read frames)
- Xử lý dữ liệu CAN (decode theo DBC → signals)
- Lưu raw CAN + lưu signals (SQLite)
- Set giá trị CAN xuống xe (send frames / command)
- Logging & Debug
- ECU Control & Command (command mức cao)
- Simulation & Testing (virtual CAN bus + pytest)

## Mục lục

- [Linux + Docker (khuyến nghị)](#linux--docker-khuyến-nghị)
  - [Build image](#1-build-image)
  - [Chạy trong container bằng Docker Compose](#2-chạy-trong-container-dev-bằng-docker-compose)
  - [Cài deps (trong container)](#3-cài-deps-trong-container)
  - [Quickstart (virtual CAN)](#4-quickstart-virtual-can-không-cần-hardware)
- [Chạy trên host Linux (không Docker)](#chạy-trên-host-linux-không-docker)
- [Troubleshooting (Docker permissions)](#troubleshooting-docker-permissions)
- [SocketCAN (xe thật trên Linux)](#socketcan-xe-thật-trên-linux)
- [ECU Control & Command](#ecu-control--command)
- [Logging & Debug](#logging--debug)
- [Simulation & Testing](#simulation--testing)
  - [Run simulation (virtual bus)](#run-simulation-virtual-bus)
  - [Run collector (decode + store to SQLite)](#run-collector-decode--store-to-sqlite)
  - [Run tests](#run-tests)

## Linux + Docker (khuyến nghị)

### 1) Build image

```bash
docker build -t carpc:dev .
```

- `docker build`: build Docker image từ `Dockerfile` trong thư mục hiện tại.
- `-t carpc:dev`: đặt tên/tag cho image.
- Dấu `.`: build context (toàn bộ source trong folder hiện tại).

### 2) Chạy trong container (dev) bằng Docker Compose

```bash
docker compose run --rm carpc bash
```

- `docker compose run`: chạy một container mới từ service trong `docker-compose.yml`.
- `--rm`: tự xoá container khi bạn `exit` (không để rác).
- `carpc`: tên service trong `docker-compose.yml`.
- `bash`: mở shell để bạn chạy lệnh bên trong container.

### 3) Cài deps (trong container)

```bash
pip install -r requirements.txt
```

- `pip install`: cài Python packages.
- `-r requirements.txt`: cài đúng các package đã liệt kê trong file `requirements.txt`.

### 4) Quickstart (virtual CAN, không cần hardware)

```bash
python3 -m carpc db init --db /data/carpc.db
python3 -m carpc sim run --channel vcan0 --interface virtual --dbc dbcResource/vehicle.dbc
```

- `python3 -m carpc ...`: chạy CLI của app (module `carpc`).
- `db init`: tạo schema SQLite.
- `--db /data/carpc.db`: đường dẫn DB (được mount ra host qua volume `./data:/data`).
- `sim run`: chạy mô phỏng "xe" phát CAN frames.
- `--interface virtual`: dùng CAN bus kiểu virtual (không cần can0 thật).
- `--channel vcan0`: tên kênh logic cho virtual bus (hai terminal phải trùng nhau).
- `--dbc dbcResource/vehicle.dbc`: file DBC dùng để encode/decode signals.

Mở terminal khác (trong container):

```bash
docker compose run --rm carpc bash

python3 -m carpc collect --channel vcan0 --interface virtual --dbc dbcResource/vehicle.dbc --db /data/carpc.db --max-seconds 5
python3 -m carpc ecu set-speed --channel vcan0 --interface virtual --dbc dbcResource/vehicle.dbc --kph 42

```

- Dòng `docker compose run ... bash`: mở **terminal container thứ 2** để chạy collector/command song song với simulator.
- `collect`: đọc CAN frames, decode theo DBC, rồi lưu raw + signals vào SQLite.
- `--max-seconds 5`: chạy trong 5 giây rồi tự dừng (tiện demo).
- `ecu set-speed`: ví dụ ECU command mức cao (encode DBC message `VehicleCommand` với signal `SetSpeedKph`).
- `--kph 42`: set giá trị muốn gửi (km/h).

python3 -m carpc --help
- `python3 -m carpc --help`: xem danh sách lệnh và options.

## Chạy trên host Linux (không phải chạy trên Docker)

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python3 -m carpc --help
```

- `python3 -m venv .venv`: tạo virtualenv tại `.venv` trong project.
- `. .venv/bin/activate`: kích hoạt venv (để `pip` cài vào venv, không vào hệ thống).
- `pip install -r requirements.txt`: cài deps cho app.
- `python3 -m carpc --help`: chạy CLI.

## Troubleshooting (Docker permissions)

Nếu Docker báo lỗi không ghi được vào `~/.docker`, thử:

```bash
export DOCKER_CONFIG="/tmp/docker-config-$USER"
mkdir -p "$DOCKER_CONFIG"
```

- `DOCKER_CONFIG`: đổi thư mục config của Docker CLI sang nơi ghi được (tránh lỗi quyền ở `~/.docker`).
- `mkdir -p`: tạo folder nếu chưa tồn tại.

## SocketCAN (xe thật trên Linux)

- **Interface**: `socketcan`
- **Channel**: `can0` (hoặc `can1`, ...)

Ví dụ:

```bash
python3 -m carpc collect --interface socketcan --channel can0 --dbc /dbc/vehicle.dbc --db /data/carpc.db
python3 -m carpc ecu set-speed --interface socketcan --channel can0 --dbc /dbc/vehicle.dbc --kph 60
```

- `--interface socketcan`: dùng SocketCAN của Linux (CAN thật).
- `--channel can0`: interface CAN trên Linux (ví dụ `can0`).
- `--dbc /dbc/vehicle.dbc`: file DBC của xe (bạn mount/đặt ở đường dẫn này).

## ECU Control & Command

### set-speed command (đã mã hóa theo DBC)

```bash
python3 -m carpc ecu set-speed --channel vcan0 --interface virtual --dbc dbcResource/vehicle.dbc --kph 60
```

- Gửi thông điệp `VehicleCommand` với signal `SetSpeedKph = 60` km/h.
- Dữ liệu được **mã hóa theo DBC** → tự động tính frame ID + payload.
- Để SocketCAN: `--interface socketcan --channel can0`

### send-raw command (dữ liệu thô)

```bash
python3 -m carpc send-raw --channel vcan0 --interface virtual --id 0x100 --data "0x11 0x22 0x33 0x44"
```

**Tham số:**
- `--id 0x100`: CAN arbitration ID (thập lục phân)
- `--data "..."`: dữ liệu hex (cách bằng space hoặc không)

**Ví dụ:**
```bash
# Gửi VehicleStatus (ID 0x100) với dữ liệu thô
python3 -m carpc send-raw --id 0x100 --data "11 22 33 44 55 66 77 88"

# Hoặc viết liền
python3 -m carpc send-raw --id 0x200 --data "1122334455667788"
```

- Không cần DBC, gửi "nguyên trạng" (debug/test).
- Để SocketCAN: `--interface socketcan --channel can0`

---

- Với dự án thật, bạn sẽ thay `VehicleCommand/SetSpeedKph` bằng các message/signal command theo DBC của xe (ví dụ: torque request, mode request, ...).
- Nếu cần control theo UDS/DoIP (diagnostic), bạn có thể mở rộng module `carpc/ecu.py` để gửi request/response theo protocol; hiện bản scaffold tập trung CAN frame level + DBC.

## Logging & Debug

- Set log level: `--log-level DEBUG`
- JSON logs: `CARPC_LOG_FORMAT=json`

## Simulation & Testing

### Run simulation (virtual bus)

```bash
python3 -m carpc sim run --channel vcan0 --interface virtual --dbc dbcResource/vehicle.dbc
```

- Chạy simulator để có dữ liệu CAN “giả” phát liên tục.

### Run collector (decode + store to SQLite)

```bash
python3 -m carpc collect --channel vcan0 --interface virtual --dbc dbcResource/vehicle.dbc --db /data/carpc.db --max-seconds 10 --log-level INFO
```

- `--log-level INFO`: mức log (đổi `DEBUG` để xem chi tiết hơn).

### Run tests

Trong container:

```bash
pytest -q
```

- `pytest`: chạy unit/integration tests.
- `-q`: chế độ ít output.

