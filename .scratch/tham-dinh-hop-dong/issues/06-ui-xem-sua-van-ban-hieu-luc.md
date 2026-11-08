# 06 - UI: tải PDF, số hóa, xem và sửa Văn bản hiệu lực

Status: done (chờ người dùng thử tải PDF trên trình duyệt)
Blocked by: 05

## Việc cần làm

- Trang Streamlit: tải PDF lên, chọn Phiên bản checklist, chạy Số hóa.
- Chế độ xem song song: ảnh trang bên trái, text các Điều khoản trên trang đó bên phải. Có bộ lọc chỉ hiện các trang tin cậy thấp, kèm lý do.
- Sửa text của Điều khoản và lưu đè Văn bản hiệu lực đã lưu (theo hash). Lần tải sau dùng lại bản đã sửa.

## Tiêu chí hoàn thành

- Sửa một Điều khoản của TOSS, tải lại file thì vẫn thấy bản đã sửa.

## Comments

**2026-10-30, người dùng chốt:**

| Câu hỏi | Quyết định |
|---|---|
| Q69 | Chỉ sửa nội dung Điều khoản. |
| Q70 | Kiểm ngoặc vuông và nhãn redline trước khi lưu, không cho nội dung rỗng. |
| Q71 | Không thêm trường lịch sử; ghi chú "đã sửa tay" lấy bằng cách so với bản số hóa gốc. |
| Q72 | Phiên bản checklist lưu trong `session_state`. |
| Q73 | Số hóa từ giao diện có hiện tiến độ; có danh sách Văn bản đã số hóa; có nút "Số hóa lại từ đầu" kèm xác nhận. |
| Q74 | Xem song song ảnh trang và Điều khoản, chưa tô vùng (để cho issue 11). |
| Q75 | Seam S16–S18. |

### Đã làm (TDD)

- **`so_hoa/van_ban.py`**
  - S16 `sua_dieu_khoan(van_ban, ma, noi_dung)` là hàm thuần:
    - Kiểm ngoặc vuông: phải đóng đủ và không lồng nhau.
    - Dạng `[tên: …]` thì tên phải là `xóa`, `thêm` hoặc `sửa`. Ngoặc thường của hợp đồng, như `[●]`, vẫn hợp lệ.
    - Nội dung rỗng thì báo `ValueError`.
  - `luu_van_ban(..., ban_goc=True)` ghi thêm bản gốc `<hash_pdf>-goc.json`; `so_hoa` luôn ghi bản gốc. Hàm đọc là `nap_van_ban_goc`. Văn bản số hóa trước thay đổi này chưa có bản gốc, nên không hiện ghi chú "đã sửa tay".
  - S17:
    - `dieu_khoan_tren_trang(van_ban, so)`: các Điều khoản có trên trang.
    - `dieu_khoan_da_sua(van_ban, goc)`: mã các Điều khoản khác bản gốc.
    - `danh_sach_van_ban(thu_muc)`: các văn bản đã lưu, mới cập nhật trước.
- **`so_hoa(..., lam_lai=True)`**: số hóa lại từ đầu, bỏ bản đang dùng. Các bản theo hash nội dung vẫn giữ, nên Lượt cũ vẫn mở được.
- **`ui/so_hoa.py`**:
  - Chọn Phiên bản checklist; giá trị được chép sang `st.session_state["phien_ban_checklist"]` cho trang Thẩm định.
  - Tải PDF lên rồi Số hóa, với tiến độ từng trang OCR hiện trong `st.status`.
  - Danh sách "Văn bản đã số hóa" và nút "Số hóa lại từ đầu" (có xác nhận).
  - Cảnh báo cấu trúc; bộ lọc "Chỉ trang tin cậy thấp", kèm nguồn đọc (lớp text hay OCR) và lý do.
  - Bên trái là ảnh trang 110 dpi, render từ `data/pdf/<hash>.pdf`. Bên phải là các Điều khoản của trang, mỗi Điều khoản có ô sửa và nút Lưu.
  - Nút Lưu chạy qua callback, nên ghi chú "đã sửa tay" hiện ngay sau khi lưu.
- **Test**
  - S16 và S17: `tests/test_sua_van_ban.py`, 14 test. Có test đúng tiêu chí: sửa khoản 4.3.2 của TOSS, tải lại vẫn thấy bản đã sửa.
  - S18: `tests/test_ui_so_hoa.py`, 5 test `AppTest`.
  - Bộ test mặc định: 256 test qua.
- **Đã thử với TOSS thật qua `AppTest`:** ảnh trang hiện đúng; trang 3 có 10 Điều khoản kèm lý do tin cậy thấp.
- **Đã kiểm `streamlit run app.py`:** ứng dụng khởi động, chỉ nghe trên 127.0.0.1 nhờ `.streamlit/config.toml`.

### Chưa kiểm tự động / ghi chú

- **Tải PDF lên** chưa test được bằng `AppTest`. Người dùng cần thử trên trình duyệt: `streamlit run app.py`.
- **Bộ lọc tin cậy thấp kém tác dụng với TOSS:** 43/52 trang bị đánh dấu, chủ yếu vì "có khung comment". Đây là quy tắc có từ issue 04. Nếu muốn bộ lọc hữu ích hơn, có thể chỉ đánh dấu những trang mà comment thực sự có chữ gần nội dung.
- **Số hóa chạy đồng bộ.** Đóng tab trong lúc OCR thì mất phần đang làm, vì kết quả chỉ được lưu khi xong cả file.

**2026-10-30, đổi quy tắc tin cậy thấp (người dùng đồng ý):**

- Trang chỉ có khung comment không còn bị đánh dấu tin cậy thấp, vì comment đã bị bỏ hẳn khỏi text. Lý do "có khung comment (đã bỏ)" vẫn được ghi ở trang đó.
- Trang bị đánh dấu tin cậy thấp khi có redline, hoặc là trang OCR có độ tin cậy nhận dạng dưới 85%.
- Với TOSS, số trang tin cậy thấp giảm từ 43 xuống 12: trang 3–7, 12, 22, 41, 44, 48, 49, 51.
- Spec đã sửa theo quy tắc mới. Thêm test `test_trang_chi_co_khung_comment_khong_tin_cay_thap_nhung_van_ghi_ly_do`.
- Bản TOSS đã lưu trong `data/` vẫn mang cờ cũ (43 trang) cho đến khi bấm "Số hóa lại từ đầu". Nội dung Điều khoản không đổi.
- Sửa thêm một test chập chờn, `test_danh_sach_van_ban_da_so_hoa`. Đồng hồ file của Windows thô, khoảng 16 ms, nên khi máy bận, hai lần ghi liền nhau có thể trùng thời điểm. Test giờ đặt thời điểm file một cách tường minh.
