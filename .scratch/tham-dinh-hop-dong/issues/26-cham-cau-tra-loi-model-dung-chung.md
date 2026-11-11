# 26 - Một bước chấm câu trả lời model dùng chung

Status: needs-triage

## Vấn đề

Bước từ câu trả lời model ra Đánh giá tiêu chí, Kết quả Mục và Trích dẫn đã kiểm tra có hai bản (`tham_dinh._danh_gia_muc` và `cham_lai._cham_luot`), phần bọc Trích dẫn có bản thứ ba (`kho_luot.luu_duyet`). `cham_lai` bỏ qua bước cắt câu trích dài; hai bản chỉ khớp vì câu trích trong kho đã cắt sẵn.

## Cách làm

Chờ hỏi đáp (grilling). Nguồn: Báo cáo kiến trúc 2026-11-11 (`C:\Users\huydt\AppData\Local\Temp\architecture-review-20261111T155046.html`), ứng viên 1.
