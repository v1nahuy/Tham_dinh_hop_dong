# 16 - Lớp text mất ký tự thân bài nằm sát khung comment

Status: done
Blocked by: 04

## Việc cần làm

- `doc_trang` (`so_hoa/lop_text.py`) bỏ mọi ký tự có tâm nằm bên phải mép khung comment. Ở TOSS, chữ trong bảng Phụ lục 02 tràn qua mép khung vài điểm, nên ký tự cuối dòng của thân bài bị bỏ cùng với chữ của comment.
- Sửa để giữ chữ thân bài tràn qua mép khung, vẫn bỏ chữ của comment.
- Số hóa lại TOSS (bản lưu theo hash PDF sẽ không tự làm lại), rồi chạy lại hai Lượt của issue 15.

## Tiêu chí hoàn thành

- Các câu trích của Bộ chuẩn `eval/chuan/toss.yaml` nằm trong bảng Phụ lục 02 tìm thấy được trong Văn bản hiệu lực. Hiện có 27 Trích dẫn (12 câu khác nhau) không tìm thấy vì lỗi này.
- Không còn chữ của comment lọt vào Văn bản hiệu lực ở các trang có khung comment.

## Comments

**2026-11-04, chẩn đoán (phát hiện khi so với Bộ chuẩn ở issue 15).**
- Ví dụ trang 21: khung comment bắt đầu từ x = 414,9. Chữ "n" cuối của "mã nguồn" có hộp x = 414–419 (tâm 416,5), nên bị bỏ; Văn bản hiệu lực ghi "mã nguồhệ thống". Tương tự: "Cloud cVNA", "dịchphần mềm", "availabilicho", "bêb có trách nhiệm"…
- Đếm theo trang, ký tự bị bỏ mà hộp bắt đầu trước mép khung hoặc lố vào chưa tới 3 điểm: tổng 132. Tập trung ở trang 16–37 (bảng Phụ lục 02, khung ở x = 414,9), lẻ tẻ ở trang 14, 49, 51. Các trang này có comment thật: nhiều ký tự nằm sâu trong khung.
- Ảnh hưởng: model ở cả hai chế độ đọc bản lỗi ở mọi Mục dùng Phụ lục 02. Kiểm tra Trích dẫn và độ phủ ngữ cảnh báo sai với câu chép đúng. Báo cáo so sánh từng ghi những câu này là "Bộ chuẩn chép chưa đúng" (đã đổi nhãn theo Q110).
- Câu của 2.L1 và 4.D2 ("số hộ chiếu, mã số tổ bay") lỗi khác: Văn bản hiệu lực thiếu dấu cách sau dấu phẩy ở chỗ ô bảng xuống dòng.
- `ocr.py` cũng có `co_khung_comment`; cần xem đường OCR có cùng lỗi không.

**2026-11-04, quyết định Q113–Q117 và đã sửa (TDD).**
- Q113: ký tự bên phải mép khung được giữ nếu cùng dòng và cách ký tự thân bài vừa giữ không quá `KHE_LIEN_MACH` = 3 điểm. Thử trên 52 trang TOSS trước khi chọn ngưỡng: phần được giữ thêm đều là đuôi chữ thân bài ("ủa", "ty)", "hiết", "độ vi"…), còn chữ comment cùng dòng gần nhất cách khoảng 498 điểm.
- Q114: thêm hai test vào `tests/test_so_hoa_toss.py`: `test_giu_chu_than_bai_tran_qua_mep_khung_comment` (trang 21) và `test_moi_trich_dan_bo_chuan_co_trong_van_ban`. Hai test đỏ trước khi sửa, xanh sau khi sửa; `test_bo_khung_comment` vẫn xanh. 347 test thường xanh.
- Q116: lỗi thiếu dấu cách của 2.L1/4.D2 cùng nguyên nhân (dấu cách và xuống dòng sau "chiếu," cũng nằm bên phải mép khung). Không cần issue riêng.
- Q115: đã số hóa lại TOSS (`lam_lai`). Văn bản hiệu lực mới `2c511c4e94fe…`, vẫn 148 Điều khoản; bản cũ `50987d7b94de…` không có chỉnh sửa tay nên không mất gì. 210/210 Trích dẫn Bộ chuẩn tìm thấy trong Văn bản hiệu lực mới (trước: 29 không thấy).
- Đường OCR cắt ảnh theo cột khung (`cat_khung_comment`), cơ chế khác; chưa kiểm vì TOSS không qua OCR và chưa có bản scan.
- Q117: 2026-11-04 13:45 bắt đầu chạy lại hai Lượt (toàn văn rồi truy xuất, có gắn lại Chủ đề), kiểm tra mỗi giờ, cuối chuỗi tạo lại báo cáo so với Bộ chuẩn. Báo cáo trước đó lưu ở `eval/so-sanh/bao-cao-truoc-issue-16.md`.

**2026-11-05, chạy lại hai Lượt với Văn bản hiệu lực mới (hoàn thành).**
- Toàn văn `d8c20de88c96-20261104T134515961445`: 17/17 Mục, 5 giờ 50 phút. Truy xuất `d8c20de88c96-20261104T203037846149`: 17/17 Mục, gắn lại Chủ đề 52 phút rồi khoảng 7 giờ 20 phút. Cả hai Lượt có 7.V2, 16.V2 là `khong_thoa`.
- Hai tiêu chí hoàn thành đều đạt: 210/210 Trích dẫn Bộ chuẩn tìm thấy trong Văn bản hiệu lực; `test_bo_khung_comment` xanh.
- Ảnh hưởng tới độ chính xác chưa đo được: xem issue 15 (2026-11-05).

**2026-11-09, Q191: đo đường OCR trên TOSS (không chạy model OCR).** Dựng ảnh từng trang có khung comment ở 300 DPI, chỉnh nghiêng, cắt bằng `cat_khung_comment`, so chỗ cắt với hộp ký tự lớp text (đã sửa theo issue này).
- Trang 16–40: ảnh cắt ở x = 430,6 (khung lớp text 414,9), nên chữ thân bài tràn qua mép vẫn giữ. Lớp text trước khi sửa mất 132 ký tự ở vùng này.
- Cả file: trang 49 mất 1 ký tự thân bài ("g") và 1 ký tự bị cắt dở; trang 51 lọt 4 ký tự comment ("CoBB").
- Giới hạn: ảnh dựng từ PDF gốc, không phải bản scan thật. Không sửa code; cần bản scan thật có khung comment nếu muốn kiểm tiếp.
