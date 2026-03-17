# prvCarPC
CarPC toolkit tập trung vào CAN:
- Chạy trên môi trường linux
- Docker để tạo môi trường, đóng gói 
- Thu thập dữ liệu CAN từ xe (read frames)
- Xử lý dữ liệu CAN (decode theo DBC → signals)
- Lưu trữ dữ liệu CAN đã xử lý (signal) + lưu raw frames
- Set giá trị CAN xuống xe (send frames)
- Logging & Debug
- ECU Control & Command (định nghĩa “command” ở mức cao)
- Simulation & Testing (virtual CAN bus + pytest)

# Setup on Linux
- Install Docker V2