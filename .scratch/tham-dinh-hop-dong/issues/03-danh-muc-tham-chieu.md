# 03 - Danh mục tham chiếu cho V1.1

Status: done
Blocked by: 02

## Việc cần làm

Soạn các Danh mục tham chiếu đi kèm V1.1, ghi rõ nguồn cho từng mục:

- **Ngành nghề đã đăng ký:** lấy từ Mục 2 của V1 (mã ngành và tên ngành).
- **Ngành nghề kinh doanh có điều kiện:** theo Phụ lục IV Luật Đầu tư (bản hiện hành). Ưu tiên những ngành gần với lĩnh vực của Công ty (viễn thông, an ninh mạng, mật mã dân sự, dịch vụ dữ liệu, cung ứng lao động…).
- **Thuế GTGT theo loại dịch vụ:** phần mềm / dịch vụ phần mềm → không chịu thuế; dịch vụ khác → 10%; ghi chú về mức 8% giảm tạm thời nếu còn hiệu lực.
- **Dấu hiệu EAR:** cung cấp phần cứng hoặc thiết bị; phần mềm hoặc thiết bị có mã hóa (Category 5 Part 2); sản phẩm của hãng Mỹ được nêu tên; mục đích quân sự hoặc lưỡng dụng; Khách hàng hoặc người dùng cuối thuộc diện bị hạn chế.

Mọi nội dung đều là bản nháp để pháp chế duyệt.

## Tiêu chí hoàn thành

- Danh mục nằm trong `checklists/` và được tham chiếu từ `dau-ra-v1.1.yaml`.
- Mỗi mục có nguồn.

## Comments

**2026-10-27, hoàn thành.** 40 test xanh. Có test kiểm tra mọi danh mục đã soạn và mỗi mục đều có nguồn.

- `nganh-nghe-co-dieu-kien.yaml`: 25 mục theo Phụ lục IV **Luật Đầu tư 143/2025/QH15** (hiệu lực từ 01/7/2026, thay Phụ lục IV của Luật 2020). Mỗi mục có `nganh_dang_ky_lien_quan`.
- `thue-gtgt.yaml`: 5 mục. Theo Nghị định 174/2025, CNTT không còn thuộc nhóm loại trừ khỏi mức 8% (áp dụng đến 31/12/2026).
- `dau-hieu-ear.yaml`: 9 dấu hiệu, mỗi dấu hiệu dẫn điều khoản 15 CFR.
- Cả ba để `trang_thai: ban-nhap`; điểm cần pháp chế xác nhận ghi ở phần 4 của `dau-ra-v1.1-khac-biet.md`.
- Ghi chú cho issue 08: đưa nội dung danh mục mà Mục checklist khai báo trong `danh_muc` vào prompt.
