# 02 - Checklist V1.1 có cấu trúc

Status: done
Blocked by: 01

## Việc cần làm

- Định nghĩa schema YAML cho Phiên bản checklist (xem spec, mục "Checklist có cấu trúc"), kèm trình nạp và kiểm tra hợp lệ.
- Chuyển `Sample/Checklist_Tham_Dinh_Hop_Dong_Dau_Ra (V1)_260716.pdf` thành `checklists/dau-ra-v1.1.yaml`: tách mỗi ô Đạt / Lưu ý / Vi phạm thành các Tiêu chí đơn lẻ, kiểm tra được; đánh dấu Tiêu chí định lượng (phạt ≤ 8%, giá trị > 2 tỷ, thanh toán ≥ 30 ngày, thông báo chấm dứt ≥ 30 ngày, bảo hành ≥ 12 tháng, non-solicitation ≥ 12 tháng, service credit ≤ 15%, thông báo bất khả kháng 7–15 ngày…); khai báo Chủ đề cho từng Mục checklist.
- Áp dụng các thay đổi đã chốt cho Mục 6 và Mục 11 (xem spec).
- Viết `checklists/dau-ra-v1.1-khac-biet.md` liệt kê mọi khác biệt so với V1, để pháp chế duyệt. Gắn cờ căn cứ Mục 11 là "cần đối chiếu bản gốc Luật 48/2024/QH15 và NĐ 181/2025".

## Tiêu chí hoàn thành

- File YAML qua được trình kiểm tra hợp lệ; đủ 17 Mục checklist.
- Có file khác biệt.

## Comments

**2026-10-27, hoàn thành.** 29 test xanh (toàn bộ dự án).

- Bộ nạp: `src/thamdinh/checklist.py` (`load_checklist`). Báo lỗi chỉ rõ vị trí khi: thiếu trường bắt buộc, mục thiếu tiêu chí Đạt, trùng số mục, trùng mã tiêu chí, `loai` sai, tiêu chí định lượng thiếu `truong`/`phep_so_sanh`/`nguong`, phép so sánh không hỗ trợ, Chủ đề hoặc danh mục chưa khai báo, file danh mục không tồn tại.
- Cấu trúc có thêm trường `danh_muc` ở cấp Mục checklist (danh mục tham chiếu mà mục đó dùng).
- Nội dung: `checklists/dau-ra-v1.1.yaml` (17 Mục, 22 Chủ đề, 122 Tiêu chí, trong đó 11 tiêu chí định lượng); `checklists/danh-muc/nganh-nghe-dang-ky.yaml` (44 mã ngành, đủ); 3 danh mục khung `chua-soan` cho issue 03.
- `checklists/dau-ra-v1.1-khac-biet.md`: khác biệt so với V1 và 9 điểm cần pháp chế quyết định.
- Ghi chú cho issue 08: prompt phải nêu quy ước "tiêu chí bắt đầu bằng 'Nếu ...' coi là thỏa khi điều kiện không xảy ra"; tiêu chí 11.D2 hiện do LLM đánh giá trực tiếp (chưa so sánh phân loại bằng code).

**2026-10-27, cập nhật theo quyết định của pháp chế** (9 điểm trong file khác biệt). 36 test xanh.

- Cấu trúc thêm `dieu_kien` (tiêu chí chỉ áp dụng khi giá trị trích xuất thỏa điều kiện) và `can_thong_tin_ngoai` cho Tiêu chí.
- Mục 1: bỏ 1.L1; 1.V2 có điều kiện giá trị > 2 tỷ. Mục 11: 11.L4 chuyển thành 11.V3. Đánh dấu `can_thong_tin_ngoai` cho 2.V2, 9.V1, 13.V2, 14.D1, 14.V1.
