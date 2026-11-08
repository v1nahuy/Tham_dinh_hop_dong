# 12 - Xuất báo cáo .docx

Status: done
Blocked by: 11

## Việc cần làm

- python-docx: thông tin Hợp đồng (số hợp đồng, Khách hàng, Phiên bản checklist, ngày thẩm định), bảng các Mục checklist theo bố cục của checklist, ô Kết quả có nền xanh / vàng / đỏ, giải thích, Trích dẫn kèm vị trí.
- Phụ lục cuối báo cáo: các Mục có Kết quả đã duyệt khác Kết quả đề xuất.
- Nút tải xuống trên UI.

## Tiêu chí hoàn thành

- Mở được file bằng Word, tiếng Việt hiển thị đúng.

## Comments

**2026-10-30, người dùng chốt:**

| Câu hỏi | Quyết định |
|---|---|
| Q84 | Mục đã duyệt dùng Kết quả đã duyệt; chưa duyệt thì dùng Kết quả đề xuất, ghi "(đề xuất, chưa duyệt)". Đầu báo cáo ghi "x/17 Mục đã duyệt". |
| Q85 | Mỗi Mục một bảng: câu hỏi; Đạt / Lưu ý / Vi phạm; Kết quả có màu; Giải thích; Trích dẫn. Không đưa Đánh giá tiêu chí của model vào. |
| Q86 | Số hợp đồng còn để trống thì ghi nguyên văn đoạn tìm được, kèm cảnh báo "Không tìm thấy số hợp đồng". Ô số hợp đồng sửa được trên giao diện. Ngày thẩm định là ngày duyệt gần nhất. |
| Q87 | Trích dẫn ghi kèm vị trí (khoản, trang). |
| Q88 | Phụ lục chỉ gồm các Mục có mức Kết quả đổi. |
| Q89 | Tạo trong bộ nhớ; tên file không dấu; Times New Roman 12; A4. |
| Q90 | Seam S23–S25. |

### Đã làm (TDD)

- **S24 `bao_cao.so_hop_dong(van_ban)`**
  - Thứ tự tìm: dòng "Số: …" ở phần mở đầu, rồi câu "Kèm theo Hợp đồng số …".
  - Số còn để trống (có "…" hoặc "..") thì giữ nguyên văn và kèm cảnh báo.
  - Với TOSS, kết quả là `……./2026/VNA-VTIT`, kèm cảnh báo.
- **S23 `bao_cao.tao_bao_cao(luot, duyet, van_ban, checklist, so_hop_dong, canh_bao) -> bytes`**
  - Bảng thông tin: số hợp đồng (kèm cảnh báo màu đỏ), tên file, Khách hàng, Phiên bản checklist, ngày thẩm định, Người thẩm định, tình trạng duyệt, Lượt.
  - Bảng tổng hợp 17 Mục.
  - Mỗi Mục một bảng theo bố cục checklist:
    - hàng câu hỏi nền DCE6F1;
    - Đạt / Lưu ý / Vi phạm có nhãn màu, liệt kê Tiêu chí;
    - Kết quả tô C6EFCE / FFEB9C / FFC7CE;
    - Giải thích;
    - Trích dẫn.
  - Phụ lục ở trang riêng.
  - Vị trí Trích dẫn dùng `trich_dan.dieu_khoan_chua_trich_dan` (tách ra từ `vung_trich_dan`), nên khớp với vùng tô của nút "Xem trang".
  - `ten_file_bao_cao` cho tên dạng `Bao-cao-tham-dinh_HD-TOSS-v-12.5.2026_20261030.docx`.
- **S25 trang Kết quả, mục "Báo cáo"**
  - Ô số hợp đồng điền sẵn, cảnh báo khi còn để trống.
  - `st.download_button`, dữ liệu được đệm theo (Lượt, các phiên bản duyệt, số hợp đồng), vì mỗi lần tạo mất khoảng 0,5 giây.
  - Test bọc `st.download_button` để kiểm tên file và mở lại file .docx.
- **Phụ thuộc:** thêm `python-docx` (cùng `pandas`, `pillow` vốn được dùng trực tiếp) vào `pyproject.toml`.
- **Test:** `tests/test_bao_cao.py` có 11 test. Bộ test mặc định đều qua.

### Kiểm tra tiêu chí "mở được bằng Word, tiếng Việt hiển thị đúng"

- Báo cáo tạo từ một Lượt chạy bằng model giả trên Văn bản hiệu lực TOSS thật, có duyệt Mục 2.
- Microsoft Word mở được (qua COM, chế độ chỉ đọc) và xuất ra PDF 9 trang.
- Đã xem ảnh các trang: tiếng Việt đủ dấu; màu ô Kết quả đúng; vị trí Trích dẫn ghi "(khoản 4.3.2, trang 3)"; phụ lục chỉ có Mục 2.

**2026-10-30, người dùng đồng ý sửa: mã danh mục trong mô tả Tiêu chí.**

- Có 5 Tiêu chí ghi mã danh mục: 2.D1, 2.L1, 6.D1, 6.L1, 11.D2. Ví dụ "(Danh mục nganh-nghe-dang-ky)".
- Báo cáo và trang Kết quả giờ hiện tên của danh mục, lấy từ trường `ten` của file danh mục. Ví dụ "(danh mục “Ngành nghề kinh doanh đã đăng ký của Công ty”)".
- Hàm dùng chung là `checklist.mo_ta_de_doc(mo_ta, checklist)`. File checklist không sửa, vì Phiên bản checklist là bất biến.
- Có thêm test cho chỗ sửa này.
