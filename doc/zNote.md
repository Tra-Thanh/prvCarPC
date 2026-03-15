CAN Netwwork:
    - Xe có bao nhiêu CAN bus?
    - CarPC sẽ kết nối vào CAN bus nào?
    - CAN bus là CAN hay CANFD?
    - Bitrate của CAN bus là bao nhiêu?
    - CarPC đọc broadcast message hay phải request (Diagnostic protocol)?
        - Nếu là broadcast message, Cycle time của message?
    - Có Gateway ECU giữa các CAN bus không?
    - Khách hàng có cung cấp file DBC cho mình không?
    - Nếu khách hàng không cung cấp DBC file thì khách hàng có thể cung cấp những gì để decode CAN Frame?

Physical CAN:
    - CarPC kết nối vào đâu?
    - Chuẩn kết nối là gì? Sơ đồ Pin trên cổng?

Diagnostic:
    Có sử dụng Diagnostic protocol không?
    Có cho phép CarPC gửi request không?

Security:
    CAN message có authentication không?
    Có gateway filter chặn message không?

Logging và Debug:
    Có simulation environment không?
    Có tool debug CAN không?



-------------------------------------------------------------------------------------------------------------------------------------
Để CarPC đọc CAN cần:
    Hardware:
        CAN Adapter
        OBD-II connection
