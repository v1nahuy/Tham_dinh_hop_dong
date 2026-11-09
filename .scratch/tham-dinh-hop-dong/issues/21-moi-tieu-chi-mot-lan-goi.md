# 21 - Mỗi Tiêu chí một lần gọi model

Status: wontfix

## Vấn đề

Mỗi Mục hiện được chấm bằng một lần gọi model cho tất cả Tiêu chí (4–12 Tiêu chí). Nghiên cứu về gộp nhiều câu hỏi trong một prompt cho kết quả không thống nhất: model lớn gộp vẫn ổn, model nhỏ có thể giảm độ chính xác từ khoảng 5 câu mỗi lần gọi. Lượt tốt nhất `d8c20de88c96-20261106T183634562376` sai nhiều ở Mục 3, 4, 13 (11/22 Tiêu chí, phần lớn chấm dễ dãi ở Đạt).

## Cách làm (Q172, Q180)

- Biến cấu hình `THAMDINH_MOI_TIEU_CHI_MOT_LAN` (mặc định tắt). Bật thì `tham_dinh(..., moi_tieu_chi_mot_lan=True)` gọi model một lần cho mỗi Tiêu chí, dùng lại cách dựng prompt cho một phần Tiêu chí (như khi chia đôi Mục). Phần đầu prompt của Mục giống nhau nên vẫn dùng lại cache.
- Câu trả lời cho một Tiêu chí bị cắt thì Mục chưa đánh giá được (không chia tiếp, không gọi lại).
- Không bật suy luận (Q178).

## Đo và quy tắc giữ (Q180)

- Chạy lại Mục 3, 4, 13 tiếp từ `…183634562376` (16k), so với Lượt đó bằng `so_sanh_lan_chay.py`.
- Giữ khi tăng ≥ 3 trên 22 Tiêu chí, đúng→sai ≤ 1, và thời gian ≤ 1,5 lần lúc chấm cả Mục (Mục 3, 4, 13 ở Lượt `…20261106T002422807677`: 42,9 + 20,2 + 17,8 ≈ 81 phút, nên ≤ khoảng 122 phút).
- Mỗi lần chạy model cần xác nhận riêng.

## Tiêu chí hoàn thành

- Test xanh; số đo theo quy tắc trên; quyết định giữ hay bỏ.

## Comments

**2026-11-09, đã làm phần code (TDD, seam `tham_dinh()` với model giả và `load_settings`).**
- `test_moi_tieu_chi_mot_lan_goi_khi_bat`: Mục 7 gọi model một lần cho mỗi Tiêu chí, phần đầu prompt giống nhau, mỗi prompt chỉ nêu Tiêu chí của lần gọi đó; Kết quả Mục tổng hợp từ đủ Tiêu chí.
- `test_moi_tieu_chi_mot_lan_ma_van_bi_cat_thi_muc_chua_danh_gia_duoc`.
- `tests/test_settings.py` thêm `THAMDINH_MOI_TIEU_CHI_MOT_LAN`; `chay_luot.py` truyền vào `tham_dinh`.
- 366 test thường xanh.

**2026-11-09, Q181–Q182: đã đo (không đạt quy tắc giữ).**
- Q181: đã commit code (`1937d62`).
- Chạy Mục 3, 4, 13 tiếp từ `…183634562376` (16k, không suy luận, mỗi Tiêu chí một lần gọi), 13:16–15:10, Lượt `d8c20de88c96-20261109T131811248689`. Báo cáo: `eval/so-sanh/lan-chay-d8c20de88c96-20261109T131811248689.md`.
- Thời gian 114 phút (Mục 3: 55,8; Mục 4: 29,4; Mục 13: khoảng 27), trong ngưỡng 122 phút. Mỗi lần gọi đọc thêm khoảng 500 token đuôi prompt (khoảng 60 giây) và viết 200–370 token.
- Tiêu chí: 11/22 → 11/22 (+0), đúng→sai 3. Không đạt (cần ≥ +3, đúng→sai ≤ 1): KHÔNG GIỮ.
  - Sai→đúng: 3.D3, 4.D2, 4.L2 (bớt chấm dễ dãi ở Đạt).
  - Đúng→sai: 3.D1 (đọc nhầm Bên: "không thuộc về Công ty (Bên B)"), 4.L1, 13.V2 (Bộ chuẩn `khong_ro`, model ra `khong_thoa`).
  - Vẫn sai: 3.D2, 3.V1, 4.D4, 4.V1, 13.D2, 13.D3, 13.L1 (Bộ chuẩn `thoa` với 99%, xem issue 20), 13.V1.
- Kết quả Mục: Mục 4 đúng (Lưu ý) như trước; Mục 3 Lưu ý (chuẩn Vi phạm) như trước; Mục 13 từ Lưu ý thành Đạt (chuẩn Vi phạm), tệ hơn.
- Nhận xét: tách Tiêu chí làm model chặt hơn ở Đạt nhưng cũng nghiêng về `khong_thoa` ở Lưu ý/Vi phạm, nên lỗi đổi chỗ chứ không giảm. Với dao động ±6–7 trên 122 (issue 20), +0/22 không cho thấy tác dụng.
- Đã tắt hai máy chủ.
- Q183: đã gỡ code (revert `1937d62`), giống issue 19. Q184: dừng hướng đổi cách gọi model; mốc hiện tại là `…183634562376` với luật issue 20 (87/122).
