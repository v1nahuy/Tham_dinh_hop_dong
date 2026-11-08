# 11 - UI: xem Kết quả đề xuất và duyệt

Status: done (chưa thử với model thật trên trình duyệt; chuyển sang issue 15)
Blocked by: 06, 10

## Việc cần làm

- Chạy Thẩm định từ UI (chọn chế độ), có tiến độ theo từng Mục checklist.
- Khi Lượt có Mục "chưa đánh giá được" (hoặc chưa xác định được các bên): hiện lỗi của từng Mục và nút **"Chạy lại phần lỗi"**, gọi `tham_dinh(..., luot_truoc=…)` để chỉ chạy lại các phần lỗi, giữ nguyên các Mục đã có kết quả. Cho phép chọn thêm Mục để chạy lại (`chay_lai`). Kết quả lưu sau mỗi Mục (`sau_moi_buoc`), nên đóng trình duyệt giữa chừng thì mở lại vẫn chạy tiếp được.
- Bảng 17 Mục checklist có màu theo Kết quả (xanh / vàng / đỏ như checklist).
- Mở rộng từng Mục: các Đánh giá tiêu chí, giá trị trích xuất, Trích dẫn kèm vị trí (bấm vào thì hiện ảnh trang có tô vùng trích nếu có tọa độ), Trích dẫn "không xác minh được" được đánh dấu rõ.
- Sửa Kết quả, giải thích và Trích dẫn → lưu thành Kết quả đã duyệt.
- Danh sách Lượt thẩm định cũ để mở lại.

## Tiêu chí hoàn thành

- Duyệt xong một Lượt thẩm định TOSS, mở lại vẫn thấy cả Kết quả đề xuất lẫn Kết quả đã duyệt.
- Lượt có Mục lỗi: bấm "Chạy lại phần lỗi" thì chỉ các Mục lỗi được gửi tới model; sau đó Lượt đủ 17 Mục.

## Comments

**2026-10-30, ghi chú từ issue 10:** dùng `KhoLuot(settings.data_dir)` cho các việc sau.
- Danh sách Lượt: `danh_sach()`.
- Mở Lượt: `nap(ma)`.
- Duyệt: `luu_duyet(ma, so_muc, ket_qua, giai_thich, trich_dan, nguoi_duyet, van_ban)`. `van_ban` lấy bằng `nap_van_ban(hash_pdf, data_dir, luot.hash_van_ban)`.
- Lịch sử duyệt: `lich_su_duyet(ma, so_muc)`.
- Nút "Chạy lại phần lỗi": `tham_dinh(..., luot_truoc=kho.nap(ma), sau_moi_buoc=kho.luu)`.
- Chọn thêm Mục để chạy lại (`chay_lai`): tạo Lượt mới. UI cần nói rõ điều này cho Người thẩm định.

**2026-10-30, người dùng chốt:**

| Câu hỏi | Quyết định |
|---|---|
| Q76 | (b) Chạy Lượt ở tiến trình nền. |
| Q77 | Kiểm tra máy chủ model trước khi chạy. |
| Q78 | Chia việc giữa trang Thẩm định và trang Kết quả. |
| Q79 | Bảng 17 Mục có màu, mỗi Mục một khung chi tiết. |
| Q80 | Xem trang có tô vùng Điều khoản chứa câu trích. |
| Q81 | Form duyệt gồm Kết quả, giải thích và Trích dẫn sửa được. |
| Q82 | Người duyệt lấy từ `THAMDINH_NGUOI_DUYET`, hoặc nhập trên trang. |
| Q83 | Seam S19–S22. |

### Đã làm (TDD)

- **S19 `thamdinh/chay_nen.py`**
  - `khoi_chay(doi_so, thu_muc)` chạy `scripts/chay_tham_dinh.py` ở tiến trình nền:
    - Trên Windows, tiến trình thuộc nhóm riêng và không có cửa sổ, nên Ctrl+C ở cửa sổ Streamlit không dừng Lượt.
    - Nhật ký ghi vào `data/nhat-ky/`, trạng thái ghi vào `data/dang-chay.json`.
    - Mỗi lúc chỉ một Lượt; chạy thêm thì báo `DangChayError`.
  - `trang_thai()` trả về: đang chạy hay không, mã Lượt (đọc từ dòng "Mã Lượt: …" trong nhật ký), và các dòng cuối nhật ký.
  - `dung()` dừng tiến trình đang chạy.
  - Trên Windows, kiểm tra tiến trình còn sống bằng WinAPI `OpenProcess` + `GetExitCodeProcess`, vì `os.kill(pid, 0)` sẽ diệt tiến trình.
  - Đã thử với tiến trình thật: khởi chạy, nhận ra lúc kết thúc, và Dừng đều đúng.
- **`thamdinh/chay_luot.py`**
  - `chay_luot()` là phần thân trước đây của `scripts/chay_tham_dinh.py`; script giờ chỉ đọc tham số và in kết quả.
  - Hàm in "Mã Lượt: …" ngay khi Lượt được lưu lần đầu.
  - Test với model giả (`tests/test_chay_luot.py`):
    - Chạy tiếp Lượt có Mục 7 lỗi thì model chỉ nhận Mục 7, và Lượt đủ 17 Mục.
    - Chọn thêm Mục 14 thì tạo Lượt mới có ghi Lượt gốc.
- **Q77**: `LocalClient.san_sang()` và `LocalEmbeddingClient.san_sang()` gọi `GET /health` của llama-server. Máy chủ trả 200 là sẵn sàng; 503 (đang nạp model) hoặc không kết nối được là chưa sẵn sàng.
- **S20 `thamdinh/bang_ket_qua.py`**: `bang_ket_qua(luot, duyet)` trả về các dòng của bảng. Số Trích dẫn không xác minh được đếm trên bản duyệt nếu Mục đã duyệt.
- **S21 `trich_dan.vung_trich_dan(td, van_ban)`**
  - Trả về vùng của các Điều khoản trong phạm vi số hiệu có chứa trọn câu trích; với `khop_sai_so_hieu` thì dùng số hiệu đúng. Câu trích trải qua nhiều Điều khoản thì lấy cả phạm vi.
  - Trích dẫn không xác minh được thì trả về rỗng.
  - Ảnh có tô vùng do `thamdinh/anh_trang.py` vẽ. Trang Số hóa cũng dùng hàm này.
- **`checklist.tim_checklist(thu_muc, "dau-ra 1.1")`** tìm file YAML theo checklist mà Lượt đã ghi.
- **S22 `ui/tham_dinh.py`** (`tests/test_ui_tham_dinh.py`, 5 test):
  - Chạy Lượt mới: chọn văn bản, checklist và chế độ; kiểm máy chủ trước khi chạy.
  - Phần tiến độ là `st.fragment` tự làm mới 10 giây một lần, có nút Dừng.
  - "Chạy lại phần lỗi": liệt kê lỗi các bên, lỗi từng Mục và các Mục chưa chạy. Có ô chọn thêm Mục, kèm cảnh báo rằng sẽ tạo Lượt mới. Đang chạy thì các nút bị khóa.
- **S22 `ui/ket_qua.py`** (`tests/test_ui_ket_qua.py`, 6 test):
  - Chọn Lượt, xem thông tin chung và các bên.
  - Ô người thẩm định, bảng 17 Mục tô màu xanh / vàng / đỏ.
  - Mỗi Mục có khung chi tiết: Đánh giá tiêu chí, giá trị trích xuất, Trích dẫn kèm trạng thái (`:red[không xác minh được]`), nút "Xem trang" mở `st.dialog`.
  - Form duyệt dùng `segmented_control` cho Kết quả, ô giải thích, và `data_editor` cho Trích dẫn. Lưu qua `luu_duyet`; thiếu người duyệt thì báo lỗi và không lưu.
  - Có phần lịch sử duyệt.
- **Trang Số hóa** ghi văn bản đang mở vào `van_ban_dang_mo`, để trang Thẩm định chọn sẵn văn bản đó.
- **Bộ test mặc định**: 291 test, tất cả đều qua.

### Kiểm tra với dữ liệu TOSS thật (model giả)

- Một Lượt chạy bằng `chay_luot` trên Văn bản hiệu lực TOSS, với Trích dẫn thật. Kết quả:
  - Trang Kết quả không lỗi.
  - "Xem trang" tô đúng khoản 4.3.2 trên trang 3. Khung được nới 3 điểm PDF để không cắt sát chữ cuối dòng.
  - Duyệt Mục 3 thành Lưu ý, mở lại thấy "Đạt → Lưu ý".

### Chưa làm / để sau

- Chưa thử với model thật trên trình duyệt (cần llama-server, một Lượt mất 5–6 giờ). Việc này làm cùng lần chạy thật ở issue 15.
- Nút Dừng diệt tiến trình script. Nếu llama-server đang sinh câu trả lời cho Mục hiện tại thì máy chủ vẫn chạy nốt yêu cầu đó, rồi mới sẵn sàng cho Lượt sau.
