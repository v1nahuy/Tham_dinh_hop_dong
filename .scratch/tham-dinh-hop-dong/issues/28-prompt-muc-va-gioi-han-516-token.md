# 28 - Prompt Mục: kiểm giới hạn 516 token của đuôi Mục 1

Status: done

## Vấn đề

Giới hạn đuôi prompt dưới 516 token (để dùng lại cache) chỉ nằm trong comment ở `tham_dinh.py`, không có test. Issue 15: đuôi Mục 1 vượt 21 token làm cả Lượt toàn văn mất khoảng 23 giờ thay vì 6 giờ, và chỉ biết sau khi đã chạy.

## Cách làm

Nguồn: Báo cáo kiến trúc 2026-11-11, ứng viên 3. Sau hỏi đáp (Q223–Q229) thu lại còn một test:

- Giới hạn chỉ đặt lên đuôi Mục 1, ở chế độ toàn văn. Các Mục khác có đuôi dài hơn nhiều (Mục 2 khoảng 9.800 ký tự) mà vẫn khoảng 15 phút mỗi Mục.
- Đuôi không chứa nội dung Hợp đồng (mô tả các bên nằm ở phần đầu), nên test với checklist thật, không cần Hợp đồng.
- `test_duoi_prompt_muc_1_du_ngan_de_dung_lai_cache` (`tests/test_prompt_tham_dinh.py`): với mọi Phiên bản checklist trong `checklists/`, đuôi Mục 1 không quá 1.600 ký tự. Hiệu chỉnh từ số đo issue 17: 1.567 ký tự = 500 token. Không dùng `uoc_tinh_token` (ước 627 token cho cùng đuôi).
- Bỏ (Q228): tách module prompt, test `-m llm` bằng `dem_token`. Không chặn thêm lỗi nào; nếu issue 31 cần tách prompt thì làm ở đó.

## Comments

- 2026-11-11: thêm test; kiểm tay: thêm 40 ký tự vào `NHAC_LAI_QUY_UOC` thì test đỏ (1.608 ký tự). Không đổi code chạy, prompt giữ nguyên từng byte. Chạy lại vài Mục ở chế độ toàn văn có thể chậm: ghi ở issue 33.
- 2026-11-11: review 2 trục (Standards, Spec) không có lỗi chặn. Sửa theo review: chuyển test sang `test_prompt_tham_dinh.py` (cùng các test prompt), cắt đuôi theo đúng tiêu đề Mục 1 và báo rõ khi không tìm thấy mốc, ghi tên đối số `cac_ben=None`, comment ghi rõ "mỗi Mục".
