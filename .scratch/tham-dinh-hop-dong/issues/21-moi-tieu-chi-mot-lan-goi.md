# 21 - Mỗi Tiêu chí một lần gọi model

Status: ready-for-agent

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
