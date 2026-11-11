# 28 - Prompt Mục: tách phần đầu và phần đuôi, kiểm giới hạn 516 token

Status: needs-triage

## Vấn đề

Giới hạn đuôi prompt dưới 516 token (để dùng lại cache) chỉ nằm trong comment ở `tham_dinh.py`, không có test. Issue 15: vượt giới hạn làm cả Lượt mất khoảng 23 giờ. `xay_prompt_muc` trả về một chuỗi liền.

## Cách làm

Chờ hỏi đáp (grilling). Nguồn: Báo cáo kiến trúc 2026-11-11 (`C:\Users\huydt\AppData\Local\Temp\architecture-review-20261111T155046.html`), ứng viên 3.
