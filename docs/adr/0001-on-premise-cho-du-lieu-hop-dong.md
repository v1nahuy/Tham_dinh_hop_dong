# Dữ liệu hợp đồng bắt buộc xử lý on-premise, kể cả ở bản demo

Hợp đồng chứa thông tin mật (giá, bảo lãnh, khách hàng), nên ở môi trường production toàn bộ việc đọc và thẩm định Hợp đồng phải chạy trên hạ tầng nội bộ. Mọi lời gọi mô hình đi qua một lớp trung gian (`LLMClient`), để thay mô hình hoặc máy chủ mà không phải viết lại luồng thẩm định.

**Sửa đổi 2026-10-29:** ban đầu bản demo được phép dùng Claude API. Nay bản demo cũng chạy local: Qwen3.5 (Apache 2.0) qua llama.cpp `llama-server`, chỉ nghe trên `127.0.0.1`. Lý do: Claude API tính phí theo lượt, và chạy local ngay từ demo đúng với hướng triển khai on-prem. `ClaudeClient` đã bị gỡ.

## Consequences

- Không dựa vào tính năng chỉ một nhà cung cấp mô hình mới có (ví dụ gửi thẳng PDF vào API) như một phần cốt lõi của luồng xử lý.
- Chất lượng thẩm định phụ thuộc mô hình nhỏ chạy trên máy (4B–9B). Không còn mốc chất lượng của một mô hình lớn để so sánh; issue 15 đo chất lượng bằng bộ chuẩn làm tay.
- Trên laptop chỉ có CPU, một Lượt thẩm định ở chế độ toàn văn mất nhiều giờ (TOSS: khoảng 5–6 giờ); prompt được thiết kế với phần đầu cố định (hướng dẫn + toàn văn) để máy chủ model dùng lại phần đã đọc giữa các Mục.
- Mạng công ty chặn nơi lưu file model, nên file model phải được tải ở mạng khác và chép vào máy (`docs/chay-model-local.md`).
