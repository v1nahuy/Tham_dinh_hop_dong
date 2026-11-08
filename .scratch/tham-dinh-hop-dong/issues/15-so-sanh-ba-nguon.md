# 15 - So sánh ba nguồn và danh sách gửi pháp chế

Status: ready-for-agent
Blocked by: 09, 13

## Việc cần làm

- Script chạy TOSS ở cả hai chế độ (toàn văn, truy xuất) rồi so với bộ chuẩn theo từng Tiêu chí và từng Mục checklist.
- Báo cáo: tỷ lệ khớp của từng chế độ so với bộ chuẩn, tỷ lệ khớp giữa hai chế độ, và các Trích dẫn không xác minh được.
- Xuất danh sách những Tiêu chí mà ba nguồn không thống nhất (kèm Trích dẫn của từng nguồn) thành file để gửi pháp chế xem.

## Tiêu chí hoàn thành

- Một lệnh tạo ra báo cáo và danh sách gửi pháp chế.
- Lượt chế độ toàn văn chạy đủ 17 Mục TOSS với model thật, không Mục nào "chưa đánh giá được" (tiêu chí còn lại của issue 08, `tests/test_llm_that.py`).

**2026-10-30, ghi chú từ issue 11:** khi chạy TOSS với model thật, chạy từ giao diện (trang Thẩm định) để thử luôn issue 11 trên trình duyệt:
- tiến trình nền, tiến độ, nút Dừng;
- "Chạy lại phần lỗi";
- duyệt trên trang Kết quả, mở lại vẫn thấy cả Kết quả đề xuất lẫn Kết quả đã duyệt.

## Comments

**2026-11-01, quyết định thiết kế (Q96–Q103).**
- Q96: không giới hạn nội dung báo cáo hai chế độ để chống neo; báo cáo có đủ chi tiết như bình thường.
- Q97: so `danh_gia` cuối cùng theo Tiêu chí, `khong_ro` khác `thoa`. Mục chưa đánh giá được tính là không khớp và ghi riêng. Có thêm tỷ lệ khớp Kết quả Mục. Giá trị định lượng so riêng, phải đúng con số.
- Q98: Bộ chuẩn chưa đủ thì so trên phần đã điền, ghi x/122. Danh sách gửi pháp chế yêu cầu đủ 122/122.
- Q99: danh sách là `.docx` khổ ngang, có cột trống "Kết luận pháp chế".
- Q100: một lệnh `scripts/so_sanh_ba_nguon.py`, mặc định không gọi model, `--chay` để chạy Lượt còn thiếu, ghi ra `eval/so-sanh/`.
- Q101: dùng bge-m3 thật thay vì chỉ BM25. Hugging Face tải được từ mạng hiện tại, nên đã tải bản Q8_0 ngay trong đêm 01/11.
- Q102: đưa độ phủ ngữ cảnh vào báo cáo, theo đúng các Điều khoản Lượt truy xuất đã đọc.
- Q103: các điểm test là hàm so sánh, đọc Bộ chuẩn chưa đầy đủ và xuất danh sách pháp chế.

**2026-11-01, đã làm phần code (TDD).**
- `src/thamdinh/so_sanh.py`: `so_sanh_nguon`, `do_phu_tu_luot`, `bao_cao_so_sanh`.
- `src/thamdinh/phap_che.py`: `tao_danh_sach_phap_che`.
- `nap_bo_chuan(..., mot_phan=True)`: chỉ lấy Tiêu chí đã điền; ô đã điền mà sai vẫn báo lỗi.
- `scripts/so_sanh_ba_nguon.py`.
- `tests/test_so_sanh.py`, `tests/test_phap_che.py`, thêm vào `tests/test_bo_chuan.py`.
- Đã thử đầu cuối trên hai Lượt giả dùng Văn bản hiệu lực thật. Chưa xem file `.docx` trong Word.

**2026-11-01 21:53, bắt đầu chạy model thật.** Lượt toàn văn rồi Lượt truy xuất nối tiếp nhau, kiểm tra mỗi giờ. Chạy bằng tiến trình nền như giao diện. Phần thử nút Dừng và thử duyệt trên trình duyệt chưa làm.

**2026-11-02, kết quả hai Lượt.**
- Toàn văn: `d8c20de88c96-20261101T215316531794`, 17/17 Mục, 5 giờ 58 phút. Mục 14 đạt, nên tiêu chí còn lại của issue 08 đã được đáp ứng bằng chính Lượt này.
- Truy xuất: `d8c20de88c96-20261102T035433909551`, 17/17 Mục, có bge-m3, khoảng 8,3 giờ. Máy mất nguồn và ngủ đông 04:13–10:15 nhưng không mất dữ liệu.
- `eval/so-sanh/bao-cao.md`: hai chế độ khớp 94/122 Tiêu chí (77,0%), 15/17 Kết quả Mục (88,2%), 9/12 giá trị định lượng (75,0%). Chưa so với Bộ chuẩn vì `toss.yaml` còn Tab ở dòng 45; chưa có danh sách pháp chế.

**2026-11-02, phát hiện lỗi ngược chiều `thoa`. Các con số trên chưa dùng được để đánh giá hai chế độ.**
- Với Tiêu chí mô tả vấn đề xấu, model hiểu `thoa` là "Hợp đồng ổn" chứ không phải "vấn đề đó có xảy ra". Prompt chưa định nghĩa chiều của `thoa`. Logic tổng hợp và phần so sánh không sai.
- Ví dụ 16.V2 "Không có điều khoản bất khả kháng": `thoa`, lý do "Hợp đồng có Điều 11…".
- Hệ quả: truy xuất 16/17 Mục ra Vi phạm, toàn văn 13/17; phần lớn là giả. Gần như toàn bộ 28 (truy xuất) và 21 (toàn văn) Tiêu chí Vi phạm được đánh `thoa` có lý do nói vấn đề không xảy ra.
- Tiêu chí Lưu ý cũng bị: đếm tay từ lý do, khoảng 10/21 (truy xuất) và 9/21 (toàn văn).
- Thử thêm định nghĩa chiều vào prompt, ngoài dự án, trên ngữ cảnh truy xuất của Mục 7, 9, 16: 12/21 Tiêu chí đổi đánh giá. Mục 7 và 9 từ Vi phạm thành Lưu ý, Mục 16 vẫn Vi phạm nhưng đúng lý do (16.V1). Đã hết các lỗi ngược rõ ràng như 7.V2, 16.V2, 7.L1, 7.L2. Cỡ mẫu nhỏ, chưa có Bộ chuẩn để đối chiếu.
- Mục 9 chưa được sửa dù Kết quả đổi: bản thử ghi 9.L1 "Điều 15.2 cấm thuê bên thứ ba", trong khi 15.2 nói việc thuê bên thứ ba làm một phần công việc không bị coi là chuyển nhượng. Đây là lỗi đọc hiểu riêng, prompt về chiều của `thoa` không xử lý được. Lượt toàn văn cũng đọc sai khoản này (ghi là cần Bên A đồng ý bằng văn bản).

**2026-11-02, Trích dẫn báo sai là không xác minh được.** `kiem_tra_trich_dan` bỏ nhãn `[thêm: …]`, `[sửa: …]` khỏi Hợp đồng nhưng không bỏ khỏi câu trích. Câu trích cũng có thể gộp nhiều dòng `[sửa: …]` của Hợp đồng thành một nhãn không đóng (12.D1, 12.V1). Kiểm lại sau khi bỏ nhãn: mọi câu có nhãn đều tìm thấy trong Văn bản hiệu lực, toàn văn 8/8 (19 → 11 không xác minh được), truy xuất 2/2 (17 → 15). Trong số này, 2 câu ở toàn văn chỉ còn khớp với số hiệu sai.

**2026-11-02 20:42, quyết định Q104–Q108 và chạy lại.**
- Q104: đã thêm định nghĩa chiều của `thoa` vào `HUONG_DAN_CHUNG` và `NHAC_LAI_QUY_UOC`.
- Q105: chạy lại cả hai chế độ qua đêm; Lượt cũ giữ trong kho, báo cáo cũ lưu ở `eval/so-sanh/bao-cao-truoc-sua-chieu.md`.
- Q106: `kiem_tra_trich_dan` bỏ nhãn khỏi câu trích, kể cả nhãn mở không đóng (TDD). 345 test thường xanh. Lượt cũ giữ nguyên trạng thái Trích dẫn đã lưu.
- Q107: thêm `test_tieu_chi_mo_ta_van_de_xau_khong_bi_hieu_nguoc` (`-m llm`, Mục 7 và 16). Test này chạy đầu chuỗi; không đạt thì chuỗi dừng, không chạy lại Lượt.
- Q108: chưa sửa Mục 9, chờ Lượt mới và Bộ chuẩn.

**2026-11-02 21:47, test chiều `thoa` đạt** (7.V2, 16.V2 đều `khong_thoa`, 1 giờ 5 phút).

**2026-11-02 23:39, chạy lại lần 2.** Lần chạy 21:47 bị dừng ở Mục 2, Lượt dở `d8c20de88c96-20261102T214703905965` bỏ không dùng.
- Nguyên nhân: Qwen3.5 chỉ dùng lại phần đầu prompt từ điểm lưu trạng thái, cách cuối prompt 516 token. Định nghĩa mới làm đuôi Mục 1 thành 537 token, điểm lưu rơi sau phần chung (28.013 token), nên mọi Mục phải đọc lại cả Hợp đồng: khoảng 80 phút mỗi Mục, Lượt khoảng 23 giờ. Số đọc lại ở Lượt cũ khớp đúng cách tính này.
- Xử lý: bỏ câu ví dụ trong `NHAC_LAI_QUY_UOC`, giữ nguyên định nghĩa đầy đủ trong `HUONG_DAN_CHUNG`. Đuôi Mục 1 còn 500 token. Đây là thay đổi nhỏ so với đoạn đã duyệt ở Q104, nên chuỗi kiểm lại 7.V2 và 16.V2 ngay sau Lượt toàn văn; sai thì dừng trước khi chạy truy xuất.

**2026-11-03, kết quả sau khi sửa chiều `thoa`.**
- Toàn văn `d8c20de88c96-20261102T233941158556`: 17/17 Mục, 4 giờ 42 phút. Truy xuất `d8c20de88c96-20261103T042340543097`: 17/17 Mục, 7 giờ 32 phút. Cả hai Lượt đều có 7.V2 và 16.V2 là `khong_thoa`.
- Từ Mục 2, chế độ toàn văn chỉ đọc lại 498–4.066 token mỗi Mục, giống Lượt cũ.
- Báo cáo cũ lưu ở `eval/so-sanh/bao-cao-truoc-sua-chieu.md`.

| | Toàn văn cũ → mới | Truy xuất cũ → mới |
|---|---|---|
| Kết quả Mục (Đạt / Lưu ý / Vi phạm) | 0 / 3 / 14 → 1 / 9 / 7 | 0 / 1 / 16 → 2 / 11 / 4 |
| Tiêu chí Vi phạm `thoa` / `khong_thoa` | 21 / 8 → 8 / 24 | 28 / 4 → 4 / 25 |
| Tiêu chí Lưu ý `thoa` / `khong_thoa` | 14 / 7 → 11 / 11 | 16 / 5 → 9 / 12 |
| Trích dẫn không xác minh được | 19/165 → 20/158 | 17/162 → 17/168 |

- Khớp giữa hai chế độ: 95/122 Tiêu chí (77,9%), 13/17 Kết quả Mục (76,5%), 10/12 giá trị (83,3%). Trước khi sửa, Kết quả Mục khớp 15/17 chủ yếu vì cả hai đều ra Vi phạm gần hết, nên con số mới thấp hơn nhưng có ý nghĩa hơn.
- Vi phạm còn lại: toàn văn Mục 5, 11, 12, 14, 15, 16, 17; truy xuất Mục 14, 15, 16, 17.
- Lỗi ngược còn sót, đếm tay từ lý do:
  - toàn văn 4.L1, 5.L1, 11.L3, 12.V3; Mục 12 ra Vi phạm chỉ vì 12.V3 (thanh toán bằng VND mà đánh `thoa`);
  - truy xuất 4.L2, 16.L1.
  - Ngoài ra truy xuất 7.L2 lấy mức phạt 8% làm giới hạn trách nhiệm (đọc hiểu sai, không phải ngược chiều).
- Mục 9: cả hai Lượt mới vẫn đọc 15.2 là "cấm thầu phụ" (9.L1 `thoa`). Theo Q108, chờ Bộ chuẩn rồi quyết.
- Trích dẫn: không còn câu nào hỏng vì nhãn. 17.D1 và 17.V3 (truy xuất) hỏng vì model chép "10. Đầu mối" có dấu cách, Hợp đồng ghi "10.Đầu mối".
- Vẫn chưa so được với Bộ chuẩn (Tab ở dòng 45 của `toss.yaml`), chưa có danh sách pháp chế.

**2026-11-04, so với Bộ chuẩn (122/122 Tiêu chí).** `scripts/so_sanh_ba_nguon.py` tạo được cả báo cáo và `danh-sach-phap-che.docx` (59 Tiêu chí, khổ ngang). Tiêu chí hoàn thành "một lệnh tạo ra báo cáo và danh sách gửi pháp chế" đã đạt.

| Cặp so sánh | Tiêu chí | Kết quả Mục | Giá trị định lượng |
|---|---|---|---|
| Toàn văn – truy xuất | 95/122 (77,9%) | 13/17 | 10/12 |
| Toàn văn – Bộ chuẩn | 76/122 (62,3%) | 10/17 | 8/12 |
| Truy xuất – Bộ chuẩn | 72/122 (59,0%) | 10/17 | 10/12 |

- Cả ba khớp: 63 Tiêu chí. Hai chế độ giống nhau nhưng khác Bộ chuẩn: 32, trong đó 18 là hệ thống `thoa` mà Bộ chuẩn `khong_thoa`. Chỉ một chế độ khớp Bộ chuẩn: 22. Ba nguồn khác nhau: 5.
- Mục 9: Bộ chuẩn ghi 9.D1 `thoa`, 9.L1 `khong_thoa` (Hợp đồng cho phép thầu phụ). Cả hai chế độ đều sai ở hai Tiêu chí này, đúng như đã nghi khi đọc 15.2.
- Mâu thuẫn trong chính câu trả lời của model: 17.D6 "có điều khoản non-solicitation" là `thoa`, nhưng 17.V1 "không có điều khoản non-solicitation" cũng là `thoa`.
- Độ phủ ngữ cảnh truy xuất: 163/181 Trích dẫn Bộ chuẩn (90,1%). Tiêu chí của issue 09 (đủ 100%) chưa đạt.
- **Lỗi số hóa (mới):** báo cáo ghi 29 Trích dẫn Bộ chuẩn "không có trong Văn bản hiệu lực (Bộ chuẩn chép chưa đúng)". Kiểm lại thì Bộ chuẩn chép đúng. 27 Trích dẫn (12 câu khác nhau) nằm trong bảng Phụ lục 02, và Văn bản hiệu lực mất ký tự ở chỗ xuống dòng trong ô bảng: "mã nguồhệ thống", "hạ tầng Cloud cVNA", "dịchphần mềm", "availabilicho", "bêb có trách nhiệm"… 2 Trích dẫn còn lại (2.L1, 4.D2, cùng một câu) do Văn bản hiệu lực thiếu dấu cách ("số hộ chiếu,mã số tổ bay"). Chi tiết ở issue 16. Lỗi này ở lớp text (issue 05). Model ở cả hai chế độ đọc phải bản lỗi này, và nhãn "Bộ chuẩn chép chưa đúng" trong báo cáo đang gây hiểu nhầm.

**2026-11-04, quyết định Q109–Q112.**
- Q109: mở issue 16 cho lỗi lớp text mất ký tự sát khung comment; sửa trước mọi thay đổi prompt.
- Q110: báo cáo đổi nhãn thành "Không tìm thấy trong Văn bản hiệu lực (Bộ chuẩn chép sai hoặc số hóa lỗi)".
- Q111: chưa gửi được danh sách cho pháp chế. Coi Bộ chuẩn là đúng: tỷ lệ khớp với Bộ chuẩn là độ chính xác của hệ thống, và mọi chỗ khác Bộ chuẩn tính là hệ thống sai.
- Q112: hoãn sửa prompt (Tiêu chí còn hiểu ngược, Mục 9) đến khi xong issue 16 và chạy lại hai Lượt.

**2026-11-02, test.** 339 test thường xanh. `tests/test_app.py` trang Kết quả từng timeout 3 giây, chỉ khi có việc khác chiếm CPU. Chưa mở `.docx` trong Word; chưa thử nút Dừng, "Chạy lại phần lỗi", duyệt trên trình duyệt.

**2026-11-05, so lại với Bộ chuẩn sau khi sửa lớp text (issue 16).** Báo cáo trước lưu ở `eval/so-sanh/bao-cao-truoc-issue-16.md`.

| Cặp so sánh | Tiêu chí trước → sau | Kết quả Mục trước → sau | Giá trị trước → sau |
|---|---|---|---|
| Toàn văn – truy xuất | 95 → 100/122 | 13 → 11/17 | 10 → 9/12 |
| Toàn văn – Bộ chuẩn | 76 → 77/122 (63,1%) | 10 → 9/17 | 8 → 8/12 |
| Truy xuất – Bộ chuẩn | 72 → 74/122 (60,7%) | 10 → 9/17 | 10 → 11/12 |

- Trích dẫn không xác minh được: toàn văn 20/158 → 14/165, truy xuất 17/168 → 14/141. Độ phủ ngữ cảnh truy xuất: 179/210 (85,2%); mẫu số lớn hơn vì 29 Trích dẫn Bộ chuẩn trước bị loại nay đã được tính.
- Danh sách pháp chế: 55 Tiêu chí (trước 59).
- **Chênh giữa hai lần chạy lớn hơn phần cải thiện.** Toàn văn đổi đánh giá ở 19 Tiêu chí (8 sai → đúng, 7 đúng → sai, 4 sai → sai khác), truy xuất đổi 15 (7, 5, 3). Model đã chạy temperature 0, nên chênh lệch đến từ độ nhạy với thay đổi nhỏ ở đầu vào: Văn bản hiệu lực chỉ dài thêm khoảng 175 token, ngữ cảnh truy xuất đổi theo Chủ đề gắn lại (ví dụ Mục 4, 5 nay chọn Phụ lục 02, Mục A rồi bỏ vì vượt ngân sách). So hai Lượt đơn lẻ không phát hiện được thay đổi nhỏ hơn khoảng 15 Tiêu chí.
- Sai ổn định ở cả hai Lượt: 9.D1, 9.L1 (Mục 9 đọc sai 15.2); 17.D6 mâu thuẫn với 17.V1.
- Theo Bộ chuẩn, 4.L1 là `thoa`, trong khi ngày 03/11 đếm tay đã xếp 4.L1 vào nhóm "hiểu ngược". Đếm tay theo lý do không đáng tin; từ nay dùng Bộ chuẩn.
- Tiêu chí hoàn thành của issue này đã đạt. Còn lại từ issue 11: thử nút Dừng, "Chạy lại phần lỗi", duyệt trên trình duyệt.
