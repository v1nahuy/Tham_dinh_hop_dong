# 14 - Biến thể đầu vào từ TOSS

Status: done (phần scan thật của người dùng: tùy chọn, chưa có)
Blocked by: 05

## Việc cần làm

- Script tạo bản giả lập scan từ TOSS: render ảnh, xoay ±1–3°, nhiễu, giảm dpi, nén JPEG, rồi ghép lại thành PDF không có lớp text. Lưu trong `eval/bien-the/`.
- Script đo chất lượng Bước 1 trên các biến thể so với Văn bản hiệu lực đã sửa tay của TOSS (tỷ lệ lỗi ký tự, số Điều khoản nhận diện đúng).
- (Người dùng, nếu được) in ra rồi scan thật vài trang để đối chiếu với bản giả lập.

## Tiêu chí hoàn thành

- Báo cáo tỷ lệ lỗi ký tự theo từng biến thể.

## Comments

**2026-10-30, người dùng chốt:**

| Câu hỏi | Quyết định |
|---|---|
| Q91 | Năm biến thể: `anh-300`, `scan-200-nghieng-1`, `scan-200-nghieng-3`, `scan-150-xam`, `den-trang-200`. |
| Q92 | Lỗi ký tự từng trang so với lớp text gốc; cấu trúc so với Văn bản hiệu lực đang dùng. |
| Q93 | Mặc định đo 12 trang đại diện; `--ca-file` thì đo cả 52 trang. Kết quả OCR được lưu lại. |
| Q94 | PDF biến thể lưu vào `eval/bien-the/` và đưa vào `.gitignore`. Báo cáo ở `eval/bien-the/bao-cao.md`. |
| Q95 | Seam S26–S28. |

### Đã làm (TDD)

- **S26 `thamdinh/bien_the.py`**
  - `CAU_HINH` khai báo 5 biến thể.
  - `tao_bien_the(anh, cau_hinh, seed)` xoay ảnh, thêm nhiễu Gauss, chuyển sang xám hoặc đen trắng. Cùng seed thì ra cùng ảnh.
  - `tao_pdf_bien_the` tạo PDF chỉ có ảnh, không có lớp text. Ảnh JPEG được nhúng nguyên bằng pypdfium2 (`load_jpeg`) để không bị nén lại lần nữa. Bộ đệm JPEG được giữ đến lúc lưu file.
  - Test trong `tests/test_bien_the.py`: 8 test.
- **S27 `thamdinh/do_chat_luong.py`**
  - Các hàm: `chuan`, `cer`, `ty_le_tu`, `so_sanh_cau_truc`. Hàm cuối chỉ so các Điều khoản của bản đúng nằm trọn trong các trang đo.
  - `scripts/do_cer_ocr.py` và `tests/test_ocr_toss.py` giờ dùng chung module này, bỏ các bản chép riêng.
- **S28 `tests/test_ocr_bien_the.py`** (marker `ocr`): trang 3 của biến thể nghiêng −3°. Kiểm đo được góc −3°, CER dưới 10%, có nhãn `[xóa:`, không lẫn comment.
- **`scripts/do_bien_the.py`** tạo các biến thể, OCR (lưu kết quả vào `eval/bien-the/ket-qua/`), đo và ghi báo cáo. Có các tùy chọn `--trang`, `--ca-file` và `--scan-that ... --trang-goc ...` (cho bản scan thật).

### Lỗi OCR tìm ra nhờ biến thể, đã sửa (có test)

1. **Lẫn comment ở bản scan nghiêng.** `ocr_trang` cắt khung comment trước khi chỉnh nghiêng. Đã đổi sang chỉnh nghiêng trước, rồi mới cắt khung.
2. **Không nhận ra dải xám ở bản có nhiễu và JPEG.** Nhiễu làm nền trắng tối đi, còn khoảng 248, lọt vào ngưỡng tuyệt đối của dải xám. `cat_khung_comment` được làm lại:
   - Làm mờ theo chiều dọc (1×31). Không làm mờ ngang, để mép dải và đường kẻ dọc mảnh không bị trải ra.
   - Lấy mức xám của dải ở vùng 80–95% bề ngang, và nền giấy là phân vị 90 của nửa trái trang.
   - Một điểm là xám khi sáng gần mức xám của dải (lệch tối đa 5).
   - Một cột là xám khi quá nửa số điểm là điểm xám. Vì vậy phần bảng tràn vào dải xám vẫn được giữ, ví dụ các trang Letter 16–40 cắt ở 1794 và trang 51 cắt ở 1790.
   - Lề trắng ở mép phải được bỏ qua, tối đa 5%.
   - Dải xám phải rộng ít nhất 4% bề ngang. Đã gặp một vệt xám mép trang chỉ rộng khoảng 8 px ở trang 47.
3. **Kết quả trên TOSS gốc sau khi sửa:** cả 52 trang cắt khung giống như trước.

Các thử nghiệm không giữ lại: làm mờ hai chiều làm lệch mép dải; bỏ qua khe hở hoặc làm trơn theo chiều ngang thì cắt vào bảng của trang 51.

### Kết quả (`eval/bien-the/bao-cao.md`, 12 trang đại diện, 2026-10-30)

| Biến thể | Lỗi ký tự (trang) | Từ có mặt | Điều khoản đúng (mốc 58/67) | Lẫn comment | Đoạn [xóa:] (lớp text 9) |
|---|---|---|---|---|---|
| anh-300 | 9,7% | 97,2% | 57/67 | không | 8 |
| scan-200-nghieng-1 | 9,8% | 97,0% | 57/67 | không | 14 |
| scan-200-nghieng-3 | 9,7% | 96,8% | 57/67 | không | 10 |
| scan-150-xam | 10,9% | 95,5% | 53/67 | không | 11 |
| den-trang-200 | 11,6% | 96,9% | 53/67 | 8 trang | 10 |

**Đọc kết quả:**

- **Lỗi ký tự** của trang văn bản là 1–4% ở mọi biến thể. Mức trung bình khoảng 10% là do các trang bảng 14, 47 và 51 (40–62%), nơi thứ tự đọc ô khác lớp text, như đã thấy ở issue 05.
- **Ảnh 200 dpi, nghiêng ±3°, nhiễu vừa** gần như không làm giảm chất lượng so với ảnh 300 dpi sạch. Góc nghiêng đo đúng ở mọi biến thể.
- **Cấu trúc**
  - Mốc lớp text chỉ đạt 58/67 vì đo các trang rời: khoản 9.2 ở trang 22 không liền với Điều 9.
  - Các bản 200 dpi chỉ thiếu thêm 4.3.4 (dòng `[xóa: 4.3.3] [thêm: 4.3.4.]`).
  - `scan-150-xam` thiếu thêm 4.3.1, 4.3.3, 4.3.5 và Phụ lục 04, Mục I.
  - `den-trang-200` thiếu thêm 1.1, 3.1, 4.3.5 và Phụ lục 04, Mục I.
- **Bản đen trắng (fax)**
  - Mất nền xám của khung comment, nên không cắt được: 8/12 trang lẫn chữ comment. Đây là giới hạn đã ghi trong `docs/cai-ocr.md`.
  - Trang 8 (bảng) có lỗi ký tự 20,8%.
  - Tín hiệu gạch ngang vẫn hoạt động: ra 10 đoạn `[xóa:`, so với 9 đoạn ở lớp text.
- **Nhãn `[xóa:` bị gắn dư**
  - Đoạn một ký tự bị gắn nhầm khi có nhiễu hoặc viền bảng ("a", "T", "7", "Á", "BÊN B" ở trang 51).
  - Ở biến thể nghiêng 1°, một dòng chữ thêm có gạch chân bị gắn thành `[xóa:` (trang 3).
  - Chữ bị gạch ngang thì VietOCR đọc rất kém, ví dụ "Bảy trính sétt Hitrơi bịt".
  - Các điểm này chưa sửa. Hướng sửa có thể: bỏ nhãn của đoạn một ký tự khi trang có nhiễu, hoặc xóa nét gạch khỏi ảnh trước khi nhận dạng.

### Chưa làm

- Phần của người dùng (tùy chọn): in rồi scan thật vài trang. Đo bằng lệnh `scripts/do_bien_the.py --bien-the "" --scan-that scan.pdf --trang-goc 3,8`.
- Chưa đo cả 52 trang (`--ca-file`, khoảng 3 giờ cho 5 biến thể).
