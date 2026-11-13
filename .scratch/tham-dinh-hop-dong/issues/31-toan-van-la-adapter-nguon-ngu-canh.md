# 31 - Chế độ toàn văn thành adapter của nguồn ngữ cảnh

Status: wontfix

## Vấn đề

Chế độ được chọn bằng các nhánh `truy_xuat is None` trong `tham_dinh`; toàn văn không phải adapter của `NguonNguCanh` như truy xuất.

## Cách làm

Chờ hỏi đáp (grilling). Nguồn: Báo cáo kiến trúc 2026-11-11 (`C:\Users\huydt\AppData\Local\Temp\architecture-review-20261111T155046.html`), ứng viên 6. Nếu cần tách prompt Mục thành phần đầu và phần đuôi thì làm ở issue này (issue 28, Q228).

## Comments

- 2026-11-13 (Q233): không làm. Chỉ có hai chế độ; việc chọn chế độ nằm ở 5 nhánh trong một hàm `tham_dinh`. Chưa có chế độ thứ ba nên tách adapter chỉ làm gọn code. Mở lại nếu thêm chế độ.
