# prvCarPC

CarPC toolkit tập trung vào CAN:

- Thu thập dữ liệu CAN từ xe (read frames)
- Xử lý dữ liệu CAN (decode theo DBC → signals)
- Lưu trữ dữ liệu CAN đã xử lý (signal) + lưu raw frames
- Set giá trị CAN xuống xe (send frames)
- Logging & Debug
- ECU Control & Command (định nghĩa “command” ở mức cao)
- Simulation & Testing (virtual CAN bus + pytest)

## Yêu cầu

- Python 3.11+ (khuyến nghị)

## Cài đặt

```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows Git Bash
pip install -r requirements.txt
```

## Quickstart (không cần xe thật)

1) Khởi tạo DB

```bash
python -m carpc db init --db carpc.db
```

2) Chạy mô phỏng “xe” phát CAN trên virtual bus

```bash
python -m carpc sim run --channel vcan0 --dbc examples/example.dbc
```

3) Ở terminal khác: collect + decode + lưu DB

```bash
python -m carpc collect --channel vcan0 --dbc examples/example.dbc --db carpc.db
```

4) Gửi command (ví dụ set tốc độ)

```bash
python -m carpc ecu set-speed --channel vcan0 --dbc examples/example.dbc --kph 42
```

## Ghi chú interface CAN

Mặc định project dùng `python-can` nên có thể cấu hình các interface phần cứng (PCAN/Kvaser/Vector/...). Demo & test dùng `virtual` để chạy cross-platform.

