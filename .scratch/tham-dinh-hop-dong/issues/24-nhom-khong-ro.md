# 24 - Tiêu chí lệch ở `khong_ro`

Status: needs-info

## Vấn đề

Ở các Lượt TOSS, khoảng 6 Tiêu chí lệch với Bộ chuẩn vì khác nhau ở `khong_ro` (đối chiếu ngày 2026-11-04, Q118–Q120):

- Bộ chuẩn ghi "cần xác minh" (`khong_ro`) còn model kết luận dứt khoát: 2.V2, 4.V1, 7.D1, 7.V1, 14.V3. Lượt `…20261109T131811248689` (issue 21) thêm 13.V2.
- Ngược lại 17.D7: model ghi `khong_ro`, Bộ chuẩn `khong_thoa`. Issue 20 đã sửa ca này (định lượng không có giá trị thì `khong_thoa`).

## Cần thông tin

- Khi nào một Tiêu chí cần thông tin ngoài Hợp đồng (năng lực thực tế của Công ty, quy định nội bộ, tra cứu bên ngoài) và phải là `khong_ro`? Có danh sách Tiêu chí như vậy không, hay cần quy tắc chung?
- Hướng xử lý (đánh dấu sẵn trong checklist hay đổi prompt) phụ thuộc câu trả lời. Đổi prompt là đổi cách gọi model, Q184 đã dừng hướng này, nên cần quyết lại.

## Tiêu chí hoàn thành

- Có quyết định về quy tắc `khong_ro`; chuyển sang `ready-for-agent` hoặc `wontfix`.

## Câu hỏi cho người dùng / Người thẩm định (Q234, 2026-11-13)

Hướng làm không đổi prompt: đánh dấu trong checklist các Tiêu chí luôn cần thông tin ngoài Hợp đồng; code sau model ghi `khong_ro` cho chúng (như luật issue 20), đo bằng `cham_lai_kho.py`, không chạy model. Chỉ đánh dấu Tiêu chí mà **ở mọi Hợp đồng** đều cần thông tin ngoài; chọn theo đúng chỗ lệch Bộ chuẩn TOSS là chỉnh cho khớp một Hợp đồng.

Với mỗi Tiêu chí: ở mọi Hợp đồng, có cần thông tin ngoài Hợp đồng mới đánh giá được không? (Nhận định sơ bộ của agent trong ngoặc, cần xác nhận.)

- **2.V2** "Hàng hóa/dịch vụ thuộc ngành nghề có điều kiện mà Công ty chưa có giấy phép" (sơ bộ: có, cần biết giấy phép Công ty đang có).
- **4.V1** "Hợp đồng có chuyển dữ liệu cá nhân ra nước ngoài mà không có đánh giá tác động/thông báo theo quy định" (sơ bộ: có, việc đánh giá tác động/thông báo nằm ngoài Hợp đồng).
- **7.D1** "Mức phạt vi phạm cao nhất áp dụng cho Công ty không vượt 8% giá trị phần nghĩa vụ vi phạm" và **7.V1** "Mức phạt vi phạm vượt 8% …" (sơ bộ: không, mức phạt thường ghi trong Hợp đồng; Bộ chuẩn TOSS ghi `khong_ro` có thể vì lý do riêng của Hợp đồng này, cần xem ghi chú Bộ chuẩn).
- **13.V2** "SLA vượt quá khả năng thực tế dựa trên giá trị Hợp đồng và thời gian thực hiện" (sơ bộ: có, cần biết năng lực thực tế).
- **14.V3** "Cam kết về trách nhiệm vượt quá giá trị Hợp đồng" (sơ bộ: chưa rõ; nếu Hợp đồng ghi trần trách nhiệm thì đánh giá được).
