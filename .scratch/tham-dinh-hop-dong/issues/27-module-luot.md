# 27 - Module Lượt: kiểu dữ liệu và định dạng lưu

Status: needs-triage
Blocked by: 26

## Vấn đề

Quy tắc định dạng Lượt rải ở `tham_dinh.py` (`luot_tu_dict`, `muc_tu_dict`) và `kho_luot.py` (`luu`, `nap`): trường lạ gây `TypeError` (issue 19), `muc_tu_dict` bỏ qua trường mới, `KhoLuot.luu` làm mất trường mới ở cấp Lượt. Các module khác import `tham_dinh` chỉ để lấy kiểu.

## Cách làm

Chờ hỏi đáp (grilling). Nguồn: Báo cáo kiến trúc 2026-11-11 (`C:\Users\huydt\AppData\Local\Temp\architecture-review-20261111T155046.html`), ứng viên 2.
