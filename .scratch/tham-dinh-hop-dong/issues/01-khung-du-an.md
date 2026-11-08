# 01 - Khung dự án và lớp LLM trung gian

Status: done

## Việc cần làm

- Cấu trúc package Python 3.12, `pyproject.toml`, pytest, app Streamlit chạy local (`streamlit run`), chỉ có trang trống và điều hướng giữa các bước.
- Cấu hình bằng `.env`: `ANTHROPIC_API_KEY`, tên mô hình (mặc định `claude-opus-5-5`), thư mục `data/`.
- Interface `LLMClient` (gửi prompt văn bản, nhận JSON theo schema) và một triển khai Claude. Luồng thẩm định chỉ được phụ thuộc vào interface này, không gọi thẳng SDK (ADR 0001). Không dùng tính năng chỉ Claude mới có, ví dụ gửi thẳng PDF.

## Tiêu chí hoàn thành

- `streamlit run` mở được app.
- Có test cho `LLMClient` dùng một client giả.

## Comments

**2026-10-27, hoàn thành.** 11 test xanh (`.venv/Scripts/python -m pytest`).

- Seam đã test: `ClaudeClient.complete_json` với transport giả (JSON hợp lệ, sai schema, không phải JSON, bọc khối code, schema được gửi kèm); `load_settings` (mặc định, ghi đè); app Streamlit khởi động và mở được 3 bước bằng `AppTest`.
- Chạy app: `.venv/Scripts/streamlit run app.py`. Copy `.env.example` thành `.env` và điền `ANTHROPIC_API_KEY`.
- `.streamlit/config.toml` khóa app chỉ nghe trên `localhost` và tắt gửi thống kê sử dụng.
- Mạng công ty chặn xác thực SSL của pip; `.venv/pip.ini` bật `use-feature = truststore` để pip dùng kho chứng chỉ Windows.
