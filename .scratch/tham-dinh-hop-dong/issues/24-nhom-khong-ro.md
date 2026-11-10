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
