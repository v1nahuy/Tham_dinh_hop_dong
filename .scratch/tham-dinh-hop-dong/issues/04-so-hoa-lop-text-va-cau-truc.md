# 04 - Số hóa: lớp text và dựng cấu trúc Điều khoản

Status: done
Blocked by: 01

## Việc cần làm

- Đọc lớp text của PDF theo từng trang và đo chất lượng (tỷ lệ ký tự tiếng Việt có dấu, ký tự `�`, ký tự bị thiếu dấu). Trả về quyết định: dùng lớp text hay chuyển sang OCR (issue 05).
- Bộ dựng cấu trúc dùng chung cho cả lớp text và OCR: từ các dòng có số trang → Điều khoản {số hiệu, tiêu đề, trang bắt đầu/kết thúc, nội dung, tọa độ nếu có}. Nhận diện "ĐIỀU n:", khoản nhiều cấp (4.3.2.), "Phụ lục 0n", và bỏ header/footer "Trang x / y".
- Lưu Văn bản hiệu lực theo hash file PDF.

## Tiêu chí hoàn thành

- ~~File TOSS bị phát hiện là lớp text kém.~~ Đổi theo Q34: TOSS được nhận là lớp text tốt; khung comment bị loại; trang có redline bị đánh dấu và redline được gắn nhãn tại chỗ (Q35).
- Có test cho bộ dựng cấu trúc với các dòng mẫu chép tay từ TOSS (Điều 1–5, Phụ lục).

## Comments

**2026-10-27, hoàn thành.** 63 test xanh (toàn bộ dự án).

- Khảo sát: lớp text của TOSS tốt khi đọc bằng pypdfium2 (lỗi bảng mã trước đây là do `pdftotext`). Spec và tiêu chí hoàn thành được sửa theo Q34–Q36.
- `so_hoa/lop_text.py`:
  - `danh_gia_lop_text` (S7) quyết định từng trang dùng lớp text hay OCR.
  - `doc_trang` loại chữ trong khung comment (hình chữ nhật xám bên phải) và gắn nhãn redline theo màu chữ cộng nét ngang mảnh có màu (gạch ngang hoặc gạch chân).
- `so_hoa/cau_truc.py`: `dung_cau_truc` (S8).
- `so_hoa/__init__.py`: `so_hoa` (S9, test tích hợp trên TOSS).
- `so_hoa/van_ban.py`: lưu/nạp JSON theo SHA-256 của file PDF trong `data/van-ban-hieu-luc/` (S10).
- Trên TOSS:
  - 147 Điều khoản: Điều 1–15, Phụ lục 01–05, Phụ lục 03 có Điều 1–4 riêng.
  - Nhãn: 9 `[xóa]`, 20 `[thêm]`, 88 `[sửa]`. Phần lớn `[sửa]` là đoạn tác giả tô đỏ thủ công, không bật track changes (ví dụ khoản 4.5, 4.6).
  - 43/52 trang bị đánh dấu tin cậy thấp, chủ yếu vì có comment.
  - Cảnh báo: hai khoản "4.1"; các khoản 4.3.x không có khoản 4.3 đứng trước. Đây là lỗi đánh số có thật trong Dự thảo.
- Chưa có OCR: trang có lớp text kém làm `so_hoa` báo `CanOCRError` (issue 05).
