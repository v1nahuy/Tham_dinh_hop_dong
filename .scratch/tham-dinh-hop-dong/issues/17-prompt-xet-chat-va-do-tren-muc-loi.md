# 17 - Prompt "xét chặt" và cách đo trên các Mục có lỗi ổn định

Status: done
Blocked by: 15, 16

## Việc cần làm

- Thêm quy ước "xét chặt" vào `HUONG_DAN_CHUNG` (`tham_dinh.py`): chỉ `thoa` khi Hợp đồng đáp ứng mọi yếu tố nêu trong Tiêu chí; thiếu một yếu tố hoặc điều khoản mâu thuẫn nhau thì `khong_thoa`. Kèm một ví dụ dạng "Có điều khoản X" và một ví dụ dạng "Nếu …". Không thêm vào `NHAC_LAI_QUY_UOC` (đuôi prompt Mục 1 đã 500/516 token).
- Đo bằng cách chạy lại các Mục có lỗi ổn định (3, 4, 8, 13, 15, 17) của Lượt truy xuất `d8c20de88c96-20261104T203037846149` với cùng ngữ cảnh, chấm mọi Tiêu chí của các Mục đó theo Bộ chuẩn.

## Tiêu chí hoàn thành

- Có báo cáo so Lượt trước và sau khi đổi prompt trên các Mục chạy lại: số Tiêu chí đúng trước/sau, danh sách sai→đúng và đúng→sai, cảnh báo nếu ngữ cảnh của Mục khác nhau.
- Quyết định giữ hay bỏ thay đổi prompt theo quy tắc đã thống nhất.

## Comments

**2026-11-05, quyết định Q118–Q120 (từ issue 15).**
- Q118: thêm quy ước "xét chặt" như trên, đặt ở phần hướng dẫn chung đầu prompt.
- Q119: đo trên Mục 3, 4, 8, 13, 15, 17 (49 Tiêu chí; Lượt truy xuất hiện đúng 26, Lượt toàn văn đúng 27 theo Bộ chuẩn — lần đầu báo nhầm 27/28, đếm lại bằng `so_sanh_lan_chay` và `so_sanh_nguon` đều ra 26/27). Chỉ giữ thay đổi khi tổng số đúng tăng và ít Tiêu chí đúng→sai.
- Q120: chưa xử lý 6 Tiêu chí lệch ở `khong_ro` (2.V2, 4.V1, 7.D1, 7.V1, 14.V3, 17.D7).
- Đã có sẵn cơ chế chạy lại Mục: `chay_tham_dinh.py <pdf> --tiep-tuc <mã Lượt> --chi-muc 3,4,8,13,15,17` tạo Lượt mới (ghi `luot_goc`), Lượt cũ giữ nguyên. Ngữ cảnh chọn lại từ Chủ đề đã lưu (`data/chu-de/`), BM25 và bge-m3, nên cần cả hai máy chủ; ngân sách 16000 token chỉ tính phần Điều khoản, không phụ thuộc độ dài hướng dẫn.

**2026-11-05, quyết định Q121–Q124 và đã làm.**
- Q121: thêm dòng "Xét chặt" (ví dụ bảo hiểm) và ví dụ cho "Nếu …" (thuê kho bãi) vào `HUONG_DAN_CHUNG`; hai ví dụ cố ý không trùng chủ đề Tiêu chí nào của checklist. `NHAC_LAI_QUY_UOC` giữ nguyên.
- Q122: giữ thay đổi khi số Tiêu chí đúng tăng ít nhất 5 (từ 26 lên 31/49 trở lên) và đúng→sai không quá 3.
- Q123: sau khi sửa prompt chạy `pytest -m llm`, rồi chạy 6 Mục; đạt Q122 thì chạy thêm một Lượt truy xuất đủ 17 Mục. Chưa chạy lại toàn văn.
- Q124 (TDD): `so_sanh_lan_chay(checklist, truoc, sau, bo_chuan, muc)` trong `so_sanh.py`, 3 test trong `tests/test_so_sanh.py` (đếm đúng và sai→đúng/đúng→sai, chỉ tính Mục được chọn, cảnh báo khi Mục đọc Điều khoản khác nhau). Script `scripts/so_sanh_lan_chay.py` ghi `eval/so-sanh/lan-chay-<mã Lượt sau>.md` và áp quy tắc Q122. 361 test thường xanh.

**2026-11-06, `pytest -m llm` với prompt mới (7 giờ 20 phút).**
- 4/5 đạt, gồm 7.V2/16.V2 không bị hiểu ngược. Đỏ: `test_moi_trich_dan_bo_chuan_nam_trong_ngu_canh_cua_muc` (độ phủ ngữ cảnh truy xuất, không phụ thuộc prompt, đã đỏ từ trước: độ phủ 85%).
- `test_luot_tham_dinh_toss_du_17_muc` tạo Lượt toàn văn đủ 17 Mục với prompt mới: `d8c20de88c96-20261105T181447448588` (6 giờ 4 phút). Cùng ngữ cảnh với Lượt toàn văn `…20261104T134515961445`, nên so được trên cả 17 Mục.
- Lưu ý: `eval/chuan/toss.yaml` được sửa lúc 2026-11-05 16:51 (sau báo cáo issue 16), nên số đúng của các Lượt cũ đổi: toàn văn 77→82/122, truy xuất 74→79/122. Mọi số trong issue này tính theo bản Bộ chuẩn hiện tại.
- Kết quả toàn văn (`eval/so-sanh/lan-chay-d8c20de88c96-20261105T181447448588.md`): 17 Mục 82→81/122 (sai→đúng 7, đúng→sai 8); 6 Mục 3, 4, 8, 13, 15, 17: 27→28/49 (đúng→sai 1). Không đạt quy tắc Q122.
- Quan sát: phần lớn thay đổi là lý do và đánh giá mâu thuẫn nhau (lý do nói "không có", đánh giá vẫn `thoa`, hoặc ngược lại): 10.D1, 14.D2, 12.V1, 17.V3 sai đi; 12.V3, 17.L1 đúng ra nhưng lý do vẫn ngược. "Xét chặt" làm 1.D1 thành `khong_ro` (đòi giấy ủy quyền) và đúng ra ở 17.D1, 12.L1. 7.D3/7.L2 sai đi vì coi mức phạt 8% là giới hạn trách nhiệm.

**2026-11-06, chạy lại 6 Mục truy xuất với prompt mới (00:22–03:06).**
- Lượt `d8c20de88c96-20261106T002422807677` (tạo từ `…20261104T203037846149`), đủ Mục, không lỗi. Mục 3 mất 43 phút, các Mục sau 15–20 phút.
- Không Mục nào đọc Điều khoản khác lần trước (không có cảnh báo ngữ cảnh), nên so sánh công bằng.
- Kết quả (`eval/so-sanh/lan-chay-d8c20de88c96-20261106T002422807677.md`): 26→32/49, sai→đúng 6 (15.D1, 15.D2, 15.L1, 15.V2, 17.D6, 17.L1), đúng→sai 0. Đạt quy tắc Q122: GIỮ thay đổi.
- Cùng 6 Mục ở toàn văn chỉ 27→28/49. Prompt "xét chặt" có tác dụng rõ ở truy xuất (ngữ cảnh khoảng 16k token), gần như không ở toàn văn (khoảng 29k token).
- Ở cả 6 Tiêu chí đúng ra, lý do và đánh giá khớp nhau (17.D6 trước đây là ví dụ mâu thuẫn: lý do "không có điều khoản non-solicitation" mà vẫn `thoa`).
- Đã tắt hai máy chủ model.

**2026-11-06, quyết định Q126–Q129 và đã làm.**
- Q126: giữ prompt "xét chặt".
- Q127: đảo thứ tự schema mỗi Tiêu chí thành `ly_do` → `gia_tri` / `gia_tri_dieu_kien` → `danh_gia` → `trich_dan`, câu cuối prompt thành "ghi ly_do, danh_gia, trich_dan". Qwen chạy với thinking tắt nên thứ tự thuộc tính là thứ tự model viết. Đã làm: test `test_schema_dat_ly_do_truoc_danh_gia` (Mục 1 và 7) đỏ rồi xanh; 362 test thường xanh, `test_app` trang Kết quả quá thời gian một lần khi chạy cả bộ, chạy riêng thì xanh (vấn đề thời gian đã biết).
- Q128: chạy một Lượt truy xuất đủ 17 Mục với cả "xét chặt" và Q127, so với `…20261104T203037846149`.
- Q129: giữ khi tăng ít nhất 8 (79 lên 87/122 trở lên) và đúng→sai không quá 5. `scripts/so_sanh_lan_chay.py` thêm `--tang-toi-thieu` và `--dung-thanh-sai-toi-da` (mặc định vẫn 5 và 3 như Q122).

**2026-11-06, Q130–Q131: ngân sách ngữ cảnh.**
- Q130: đo độ phủ Trích dẫn Bộ chuẩn trong ngữ cảnh truy xuất (không chấm, không ghi Lượt):

  | Ngân sách | Độ phủ | Mục vượt ngân sách | Token TB / lớn nhất mỗi Mục |
  |---|---|---|---|
  | 16000 | 165/191 (86%) | 11/17 | 9822 / 15992 |
  | 20000 | 180/191 (94%) | 1/17 (Mục 14) | 13499 / 19961 |
  | 24000, 32000 | 180/191 (94%) | 0/17 | 13520 / 20310 |

  - 20k lấy lại Trích dẫn của 12 Tiêu chí: 2.L1, 2.V2, 4.D2, 4.L2, 4.V1, 11.D3, 13.L1, 14.D1, 14.L1, 14.V1, 17.D3, 17.V2. Trên 20k không thêm gì.
  - 8 Tiêu chí vẫn thiếu dù không giới hạn (2.D1, 6.D1, 6.D2, 10.L2, 12.L1, 15.D5, 15.L1, 16.D2): lỗi chọn Điều khoản (Chủ đề hoặc lưới an toàn), không phải ngân sách.
- Q131: Lượt Q128 vẫn chạy ở 16k; nâng ngân sách là thí nghiệm riêng sau. Đã khởi chạy 09:16, nhật ký `data/nhat-ky/chuoi-17b.log`, Lượt `20261106T091616.log`.

**2026-11-06, kết quả Lượt Q128 (09:16–17:10).**
- Lượt `d8c20de88c96-20261106T091810431014` ("xét chặt" + `ly_do` trước `danh_gia`, 16k), đủ 17 Mục, không lỗi. Đã tắt hai máy chủ.
- So với `…20261104T203037846149` (`eval/so-sanh/lan-chay-d8c20de88c96-20261106T091810431014.md`): 79→83/122, sai→đúng 16, đúng→sai 12. Không đạt Q129 (cần +8 và đúng→sai ≤ 5): KHÔNG giữ.
- Trên 6 Mục 3, 4, 8, 13, 15, 17, so với Lượt chỉ có "xét chặt" (`…20261106T002422807677`): 32→31/49. Q127 thêm đúng 8.D3, 8.D4, 17.D1 nhưng làm sai 8.L1, 8.V1, 8.V2, 17.V3.
- Nguyên nhân chính của đúng→sai: hiểu ngược nghĩa `thoa` ở Tiêu chí mô tả rủi ro. 7/12 (1.V1, 1.V2, 2.V1, 8.L1, 8.V1, 8.V2, 12.V1) có lý do kết luận "Hợp đồng ổn" (người ký có thẩm quyền; có điều khoản hậu quả chấm dứt; có cơ chế CR…) rồi ghi `thoa`, tức là coi `thoa` là "Hợp đồng đạt". Viết lý do trước khiến model chốt một nhận định tốt/xấu, rồi chuyển "tốt" thành `thoa`. Ở Tiêu chí [Đạt] thì lý do và đánh giá khớp hơn trước (8.D3, 8.D4, 15.D1, 15.D2, 17.D1, 17.D6).
- Hệ quả ở cấp Mục: 13/17 Mục ra Vi phạm (trước 7/17); Mục 1, 2, 8, 12 bị báo Vi phạm sai.
- Các đúng→sai khác: 9.V1 (suy diễn giả định), 14.V1 (`khong_ro` thành `thoa`), 16.D1 (xét chặt quá: mốc T+n bị coi là chưa có ngày cụ thể), 17.V3, 2.L1.

**2026-11-06, quyết định Q132–Q133 và đã làm.**
- Q132: bỏ Q127, giữ "xét chặt". Schema và câu cuối prompt về lại `danh_gia` trước `ly_do`; test đổi thành `test_schema_dat_danh_gia_truoc_ly_do` (ghi lý do trong docstring), đỏ rồi xanh. 363 test thường xanh.
- Q133: chạy 11 Mục 1, 2, 5, 6, 7, 9, 10, 11, 12, 14, 16 tiếp từ `…20261106T002422807677` (16k), được Lượt "xét chặt" đủ 17 Mục; so với `…20261104T203037846149` theo Q129. Khởi chạy 18:34, Lượt `d8c20de88c96-20261106T183634562376`, nhật ký `data/nhat-ky/chuoi-17c.log`.

**2026-11-07, kết quả Q133 (18:34–23:47).**
- Lượt `d8c20de88c96-20261106T183634562376` ("xét chặt" đủ 17 Mục, 16k), không lỗi. Đã tắt hai máy chủ.
- So với `…20261104T203037846149` (`eval/so-sanh/lan-chay-d8c20de88c96-20261106T183634562376.md`): 79→84/122 (+5), sai→đúng 12, đúng→sai 7. Không đạt Q129 (cần +8 và đúng→sai ≤ 5).
- Tách theo nhóm Mục: 6 Mục đã đo 26→32/49 (+6, đúng→sai 0); 11 Mục mới chạy 53→52/73 (−1), sai→đúng 6 (6.D1, 6.D2, 6.L1, 11.D3, 11.V1, 16.V1), đúng→sai 7 (1.V1, 2.L1, 2.V1, 5.L1, 9.V1, 11.L3, 14.D3).
- Đúng→sai ở 11 Mục phần lớn không do "xét chặt": 1.V1 hiểu ngược `thoa` (lý do "không có dấu hiệu không có thẩm quyền"); 5.L1 lý do "không quy định mức cố định" mà ghi `thoa`; 2.V1 cho rằng Công ty chưa đăng ký 6310/8559 (Bộ chuẩn: đã đăng ký); 2.L1 lặp lỗi của Lượt Q128; 14.D3 ghi `thoa` với lý do một câu. 9.V1 thành `khong_ro` có thể do "xét chặt" (đòi xem thêm Điều 10, 12).
- Cấp Mục: 3/17 Mục đổi kết quả, cả 3 đều về đúng Bộ chuẩn: Mục 11 Lưu ý→Vi phạm (11.V1), Mục 15 Lưu ý→Vi phạm (15.V2), Mục 16 Vi phạm→Lưu ý (16.V1).
- `temperature` = 0, nên khác biệt giữa hai Lượt là do prompt đổi, không do ngẫu nhiên; nhưng một thay đổi nhỏ ở đầu prompt vẫn làm lật 6–7 Tiêu chí ở các Mục không liên quan.

**2026-11-07, quyết định Q134–Q136.**
- Q134: GIỮ "xét chặt" dù không đạt Q129 (+5 thay vì +8, đúng→sai 7 thay vì ≤ 5). Lý do: 84/122 là kết quả truy xuất tốt nhất; cả 3 Mục đổi kết quả đều về đúng Bộ chuẩn, không Mục nào bị báo Vi phạm sai; trong 7 đúng→sai chỉ 9.V1 có vẻ do "xét chặt".
- Q135: lỗi lý do và đánh giá ngược nhau tách thành issue 18 (`needs-triage`).
- Q136: chạy lại 11 Mục từng vượt 16k (2, 3, 4, 5, 6, 11, 13, 14, 15, 16, 17) ở 20k (`THAMDINH_NGAN_SACH_TRUY_XUAT=20000`, chưa đổi mặc định), tiếp từ `…20261106T183634562376`, so đủ 17 Mục với Lượt đó. Giữ 20k khi tăng ít nhất 4 và đúng→sai không quá 4; giữ thì đổi `DEFAULT_NGAN_SACH_TRUY_XUAT`. 6 Mục còn lại có ngữ cảnh giống hệt ở 16k và 20k nên không chạy lại. Nhật ký `data/nhat-ky/chuoi-17d.log`.

**2026-11-07, kết quả Q136: ngân sách 20k (01:20–10:37).**
- Lượt `d8c20de88c96-20261107T012232562002`, không lỗi; đã xác nhận dùng 20000 (prompt Mục 2 là 21.527 token so với 20.451 ở 16k; cuối nhật ký ghi "Vượt ngân sách 20000" ở Mục 14). Đã tắt hai máy chủ.
- So với `…20261106T183634562376` (`eval/so-sanh/lan-chay-d8c20de88c96-20261107T012232562002.md`): 84→83/122, sai→đúng 6 (2.L1, 2.V1, 5.L1, 11.L3, 14.D3, 16.L1), đúng→sai 7 (6.D2, 6.V1, 11.V1, 11.V3, 14.V1, 16.V1, 17.L1). Trên 11 Mục chạy lại: 55→54/81. Không đạt Q136: KHÔNG giữ 20k.
- 12 Tiêu chí được lấy lại Trích dẫn ở 20k: chỉ 2.L1 đúng ra, 14.V1 sai đi (`khong_ro` thành `khong_thoa`); 5 Tiêu chí đúng ở cả hai (11.D3, 14.D1, 14.L1, 17.D3, 17.V2), 5 sai ở cả hai (2.V2, 4.D2, 4.L2, 4.V1, 13.L1). Model đọc được đoạn cần thiết nhưng vẫn kết luận sai: độ phủ ngữ cảnh không còn là nút thắt chính ở các Tiêu chí này.
- Các thay đổi còn lại là xáo trộn do ngữ cảnh khác: 5/6 sai→đúng (2.L1, 2.V1, 5.L1, 11.L3, 14.D3) chính là các Tiêu chí đúng→sai của Q133 quay về đúng, đổi lại 7 Tiêu chí khác sai đi (trong đó 11.V1, 16.V1 là các Tiêu chí Q133 vừa làm đúng ra). Cấp Mục: Mục 16 Lưu ý→Vi phạm (sai, do 16.V1); Mục 11 vẫn Vi phạm nhưng do 11.V3 (sai) thay vì 11.V1.
- Thời gian: 11 Mục mất 9 giờ 17 phút; nhiều Mục chậm gấp 1,1–2,5 lần ở 16k (Mục 4, 5, 13, 14 khoảng 50–55 phút so với 18–24 phút).

**2026-11-08, quyết định Q137–Q139, đóng issue.**
- Q137: giữ `DEFAULT_NGAN_SACH_TRUY_XUAT = 16000`.
- Q138: đóng issue. Chốt lại:
  - Giữ "xét chặt" (Q134); Lượt truy xuất tốt nhất là `d8c20de88c96-20261106T183634562376`, 84/122.
  - Bỏ đặt `ly_do` trước `danh_gia` (Q127, Q132).
  - Giữ ngân sách 16k (Q137).
  - Model chạy `temperature` = 0 nên lặp lại được, nhưng đổi prompt hoặc ngữ cảnh làm 6–7 Tiêu chí lật hai chiều. Trên một Hợp đồng, ngưỡng +4/+5 sát mức dao động này; thay đổi nhỏ khó đo được bằng cách chạy lại Lượt.
- Q139: việc tiếp theo là triage issue 18.
