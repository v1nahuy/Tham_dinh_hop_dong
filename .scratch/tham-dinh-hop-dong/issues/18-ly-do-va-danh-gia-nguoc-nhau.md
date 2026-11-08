# 18 - Lý do và đánh giá ngược nhau ở Tiêu chí Vi phạm/Lưu ý

Status: wontfix

## Vấn đề

Model viết `ly_do` kết luận một đằng, `danh_gia` ghi một nẻo. Thường gặp nhất ở Tiêu chí [Vi phạm] và [Lưu ý] (mô tả rủi ro): `thoa` nghĩa là "rủi ro có xảy ra", nhưng model ghi `thoa` khi lý do kết luận "Hợp đồng ổn".

Ví dụ đã gặp (TOSS, Bộ chuẩn `eval/chuan/toss.yaml`):

- 1.V1 (Lượt `d8c20de88c96-20261106T183634562376`): lý do "không có dấu hiệu cho thấy người này không có thẩm quyền", đánh giá `thoa`.
- 5.L1 (cùng Lượt): lý do "không quy định mức phạt cố định riêng cho vi phạm bảo mật", đánh giá `thoa`.
- Lượt `d8c20de88c96-20261106T091810431014` (thử đặt `ly_do` trước `danh_gia`, issue 17 Q127): 7/12 Tiêu chí đúng→sai thuộc loại này (1.V1, 1.V2, 2.V1, 8.L1, 8.V1, 8.V2, 12.V1). Lỗi này làm 4 Mục bị báo Vi phạm sai.
- Chiều ngược lại ở Tiêu chí [Đạt]: 17.D6 trước đây (lý do "không có điều khoản non-solicitation", đánh giá `thoa`), 10.D1, 14.D2, 12.V1, 17.V3 ở Lượt toàn văn `…20261105T181447448588`.
- 7.V2/16.V2 bị hiểu ngược từ trước; có test `pytest -m llm` riêng cho hai Tiêu chí này.

## Đã biết

- Đặt `ly_do` trước `danh_gia` trong schema làm lỗi nặng hơn (issue 17, Q127/Q132): đã bỏ, test `test_schema_dat_danh_gia_truoc_ly_do` giữ thứ tự cũ.
- Đuôi prompt Mục 1 đã 500/516 token, nên không thêm được câu nhắc dài vào `NHAC_LAI_QUY_UOC`.
- Qwen chạy `temperature` = 0, thinking tắt.

## Hướng có thể xét (chưa quyết)

- Kiểm tra sau khi model trả lời: phát hiện lý do và đánh giá ngược nhau, rồi hỏi lại model hoặc đánh dấu để người duyệt xem.
- Đổi cách diễn đạt Tiêu chí [Vi phạm]/[Lưu ý] trong prompt (ví dụ ghi rõ "thoa = rủi ro có trong Hợp đồng" ngay cạnh từng Tiêu chí).
- Thêm trường trung gian trong schema (ví dụ nhận xét Hợp đồng có đúng như mô tả của Tiêu chí không) trước `danh_gia`.

## Comments

**2026-11-08, phân loại 38 Tiêu chí sai của Lượt tốt nhất `d8c20de88c96-20261106T183634562376` (84/122), đọc thủ công lý do.**
- Lý do và đánh giá ngược nhau (lỗi của issue này): 5, gồm 1.V1, 1.V3 (lý do ghi rõ "đánh giá là 'thoa' (không phát hiện vi phạm)"), 5.L1, 11.D2, 16.D5 (lý do "được coi là thỏa mãn" mà ghi `khong_ro`). Sửa hết thì 84→89/122. 1.V1 và 1.V3 là lý do Mục 1 bị báo Vi phạm.
- `khong_ro` thay vì `khong_thoa`/`thoa` (nhóm Q120, đã hoãn): khoảng 6, gồm 1.D1, 8.D2, 9.V1, 16.D4, 16.L1, 17.D7.
- Lý do và đánh giá khớp nhau nhưng nội dung sai so với Bộ chuẩn (đọc sai, suy luận pháp lý sai, hiểu Tiêu chí khác người thẩm định): khoảng 26, ví dụ 2.V1 (cho rằng chưa đăng ký mã 6310), 3.V1, 13.V1, 14.D3, 17.D1.
- Ở Lượt Q127 (`ly_do` trước `danh_gia`), lỗi này chiếm 7/12 đúng→sai; với thứ tự hiện tại nó ít hơn nhiều.

**2026-11-08, quyết định Q140–Q148.**
- Q140: làm issue này (tối đa +5 trên Lượt tốt nhất, sửa Mục 1 bị báo Vi phạm sai).
- Q141: Đối chiếu lý do bằng một lần gọi Qwen mỗi Mục, chỉ đưa mô tả Tiêu chí và `ly_do` (không đưa Hợp đồng, không đưa đánh giá), hỏi theo lý do thì Hợp đồng có đúng như mô tả không.
- Q142: lệch thì `danh_gia` đi theo lý do, `danh_gia_llm` giữ câu trả lời gốc, ghi Cảnh báo của Mục.
- Q143: đo trên Lượt đã lưu; giữ khi trên Lượt `…183634562376` bắt ≥ 4/5 ca đánh dấu tay, tăng ≥ 3, đúng→sai ≤ 1.
- Q144: seam `doi_chieu_ly_do(muc, ket_qua_muc, llm) -> KetQuaMucDeXuat` trong `src/thamdinh/doi_chieu.py`; `tham_dinh()` gọi sau mỗi Mục. Test với model giả: lệch thì sửa và tính lại Kết quả Mục; khớp thì không đổi; lỗi gọi model thì giữ nguyên và cảnh báo.
- Q145: chỉ sửa khi đối chiếu ra `thoa`/`khong_thoa` khác đánh giá của model; đối chiếu ra `khong_ro` thì giữ nguyên.
- Q146: bỏ qua Tiêu chí định lượng (code so ngưỡng). Tiêu chí có điều kiện: đối chiếu phần định tính (`danh_gia_llm`), code vẫn xét điều kiện.
- Q147: `scripts/doi_chieu_luot.py <mã Lượt>` lưu Lượt mới (`luot_goc`), in Tiêu chí đã sửa, so với Lượt gốc.
- Q148: thêm "Đối chiếu lý do" vào `GLOSSARY.md`.

**2026-11-08, đã làm (TDD).**
- `src/thamdinh/doi_chieu.py`: `doi_chieu_ly_do(muc, kq, llm)`, prompt `HUONG_DAN_DOI_CHIEU` (chỉ mô tả Tiêu chí và lý do; nói rõ "thoa" ở Tiêu chí rủi ro nghĩa là rủi ro CÓ; dặn không chép kết luận lý do tự ghi). Import kiểu `KetQuaMucDeXuat` chỉ khi kiểm tra kiểu để tránh import vòng với `tham_dinh`.
- `tests/test_doi_chieu.py`: 5 test (lệch thì sửa và tính lại Kết quả Mục; khớp hoặc `khong_ro` thì giữ nguyên; lỗi gọi model thì giữ nguyên và cảnh báo; bỏ qua Tiêu chí định lượng). Test 2 xanh ngay vì lát 1 đã lọc.
- `tham_dinh()` gọi `doi_chieu_ly_do` sau mỗi Mục, sau khi gắn Cảnh báo truy xuất. Test `test_moi_muc_duoc_doi_chieu_ly_do_sau_khi_cham`; `ModelGia` trong `test_tham_dinh.py` trả lời lần gọi đối chiếu riêng (mặc định lặp lại đánh giá đã trả lời).
- `scripts/doi_chieu_luot.py <mã Lượt>`: chạy trên Lượt đã lưu, lưu Lượt mới có `luot_goc`.
- 365 test thường xanh; `test_app` trang Kết quả quá thời gian khi chạy cả bộ, chạy riêng xanh (đã biết).

**2026-11-08, đo Đối chiếu lý do trên Lượt `…183634562376` (12:35–12:53, 18 phút).**
- Lượt `d8c20de88c96-20261108T123519446922` (`eval/so-sanh/lan-chay-d8c20de88c96-20261108T123519446922.md`): 84→66/122, sai→đúng 7, đúng→sai 25. Sửa 39 Tiêu chí; trong 5 ca đánh dấu tay chỉ bắt 11.D2 (1/5). Không đạt Q143.
- Nguyên nhân: chính lần gọi đối chiếu bị lỗi phủ định lồng nhau. Tiêu chí viết dạng phủ định ("Không có điều khoản về hậu quả chấm dứt", "Không có danh mục bàn giao cụ thể"…) với lý do "Hợp đồng có …" bị ghi `thoa` (8.V2, 12.V1, 15.V1, 17.V2…). Ngược lại vẫn để lọt 1.V1, 1.V3, 5.L1. Qwen3.5 9B không làm tốt việc này hơn khi bỏ Hợp đồng ra khỏi prompt.
- Theo Q143: không giữ. Đã gỡ lời gọi `doi_chieu_ly_do` khỏi `tham_dinh()` và test tích hợp; `src/thamdinh/doi_chieu.py`, `tests/test_doi_chieu.py`, `scripts/doi_chieu_luot.py` còn lại, chờ quyết định. Đã tắt Qwen.
- Quan sát: nhiều Tiêu chí [Vi phạm]/[Lưu ý] viết dạng phủ định ("Không có …"). Kết luận "thoa" cho một rủi ro được mô tả bằng câu phủ định là chỗ model 9B sai lặp lại, cả khi chấm lẫn khi đối chiếu.

**2026-11-08, đóng issue (Q149, Q150).**
- Q149: đã xóa `src/thamdinh/doi_chieu.py`, `tests/test_doi_chieu.py`, `scripts/doi_chieu_luot.py` và mục "Đối chiếu lý do" trong `GLOSSARY.md`. Cách làm và số đo vẫn ghi ở các comment trên; Lượt `d8c20de88c96-20261108T123519446922` vẫn trong kho để xem lại.
- Q150: `wontfix`. Qwen3.5 9B không tự kiểm tra được lý do của chính mình, vì lần kiểm tra cũng mắc cùng lỗi phủ định. Hướng gỡ ở gốc chuyển sang issue 19 (câu hỏi sự kiện cho Tiêu chí: model trả lời có/không, code quy ra `thoa`/`khong_thoa`).
