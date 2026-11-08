# 10 - Lưu trữ Lượt thẩm định

Status: done
Blocked by: 08

## Việc cần làm

- Schema SQLite: Lượt thẩm định (hash PDF, Phiên bản checklist, chế độ, mô hình, thời điểm), Kết quả đề xuất và Đánh giá tiêu chí, Kết quả đã duyệt (Kết quả, giải thích và Trích dẫn đã sửa).
- File PDF và Văn bản hiệu lực lưu trong `data/` theo hash.
- Kết quả đề xuất không bao giờ bị ghi đè khi duyệt.

## Tiêu chí hoàn thành

- Có test lưu rồi đọc lại một Lượt thẩm định đầy đủ.

## Comments

**2026-10-30, quyết định thiết kế (Q62–Q67).**
- **Q62 (b), cấu trúc SQLite:** dùng file `data/tham-dinh.sqlite3`.
  - Bảng `luot` chứa thông tin chung của Lượt.
  - Kết quả đề xuất lưu JSON, mỗi Mục một dòng trong bảng `muc_de_xuat`, để cơ sở dữ liệu tự chặn việc ghi đè từng Mục.
  - Kết quả đã duyệt lưu ở bảng `duyet`.
  - `luu_luot` và `nap_luot` dạng JSON giữ lại làm chức năng xuất file.
- **Q63, không ghi đè Kết quả đề xuất:**
  - Mục đã có Kết quả thì không được sửa. Trigger trong SQLite chặn việc này.
  - "Chạy lại phần lỗi" chạy trên chính Lượt đó.
  - `chay_lai` trên một Mục đã có Kết quả thì tạo Lượt mới, ghi `luot_goc` trỏ về Lượt cũ.
- **Q64, Kết quả đã duyệt:**
  - Lưu theo từng Mục: Kết quả, giải thích, Trích dẫn, người duyệt, thời điểm.
  - Chỉ thêm, không sửa: bản mới nhất là Kết quả đã duyệt hiện tại.
  - Trích dẫn đã sửa được kiểm tra lại bằng `kiem_tra_trich_dan`.
- **Q65, Văn bản hiệu lực:** Lượt ghi `hash_van_ban`, là mã nội dung của đúng Văn bản hiệu lực đã dùng. Mỗi bản Văn bản hiệu lực lưu theo cặp hash PDF và hash nội dung, nên bản cũ không bị mất khi sửa tay (issue 06).
- **Q66, file PDF:** khi số hóa, chép PDF vào `data/pdf/<hash>.pdf`.
- **Q67, các điểm test:**
  - lưu rồi đọc lại;
  - lưu sau mỗi Mục, kèm chặn ghi đè và `chay_lai` tạo Lượt mới;
  - duyệt;
  - danh sách Lượt;
  - Văn bản hiệu lực theo hash nội dung, và chép file PDF.

**2026-10-30, hoàn thành (TDD, 213 test thường xanh).**
- `src/thamdinh/kho_luot.py`, lớp `KhoLuot(thu_muc)`, dùng file `data/tham-dinh.sqlite3`:
  - `luu`, `nap`, `danh_sach` (danh sách `TomTatLuot`);
  - `luu_duyet`, `nap_duyet`, `lich_su_duyet` (danh sách `KetQuaDuyet`).
  - `GhiDeError` khi cố ghi đè Kết quả đề xuất.
  - Trigger trong SQLite chặn UPDATE và DELETE trên Mục đã có Kết quả, và trên mọi bản ghi `duyet`.
- `KetQuaLuot` có thêm `ma`, `luot_goc`, `hash_van_ban`.
  - `tham_dinh(..., chay_lai=…)` trên Mục đã có Kết quả thì tạo Lượt mới.
  - `sau_moi_buoc` được gọi sau mọi Mục, kể cả Mục chép từ Lượt gốc.
- `luu_van_ban` ghi thêm một bản theo hash nội dung. `nap_van_ban(hash_pdf, thu_muc, hash_nd)` đọc lại đúng bản đó.
- `so_hoa(..., thu_muc_luu)` chép PDF vào `data/pdf/<hash>.pdf`.
- `luot_tu_dict` dùng chung cho JSON và SQLite. `luu_luot` và `nap_luot` (JSON) giữ lại làm chức năng xuất file.
- `scripts/chay_tham_dinh.py`: có thêm `--danh-sach`, và `--tiep-tuc <mã Lượt>` thay cho đường dẫn file JSON.
  - Đã thử trên TOSS với Lượt tạo bằng model giả: liệt kê được, chạy tiếp được, không gọi model lần nào.
