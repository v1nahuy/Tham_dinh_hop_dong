# 23 - Thử tay trên trình duyệt và Word

Status: ready-for-human

## Vấn đề

Các phần sau chưa test được bằng `AppTest` hoặc chưa ai thử với dữ liệu thật. Gom từ issue 6, 11, 12, 15.

## Việc cần làm (người dùng)

Chạy `streamlit run app.py`. Lượt thật có sẵn trong kho, ví dụ `d8c20de88c96-20261106T183634562376`.

- Trang Số hóa: tải một PDF lên (issue 6).
- Trang Thẩm định: bắt đầu một Lượt, xem tiến độ tự làm mới, bấm Dừng (issue 11). Cần `llama-server`; dừng sớm được, không cần chạy hết.
- Trang Kết quả với Lượt có Mục "chưa đánh giá được": bấm "Chạy lại phần lỗi", chọn thêm Mục (issue 11).
- Trang Kết quả: duyệt một Mục (Kết quả, Giải thích, sửa Trích dẫn), xem Lịch sử duyệt, bấm "Xem trang" ở một Trích dẫn (issue 11).
- Tải báo cáo .docx của một Lượt thật, mở bằng Word: tiếng Việt, bảng, màu ô Kết quả (issue 12, 15).

## Tiêu chí hoàn thành

- Mỗi mục trên ghi "được" hoặc mô tả lỗi gặp phải trong Comments. Lỗi tách thành issue riêng.
