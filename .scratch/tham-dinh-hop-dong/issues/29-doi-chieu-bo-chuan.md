# 29 - Một module đối chiếu với Bộ chuẩn

Status: wontfix
Blocked by: 26

## Vấn đề

Ba cách đếm đúng/sai so với Bộ chuẩn (`so_sanh_nguon`, `so_sanh_lan_chay`, `cham_lai.so_cham`), xử lý Mục chưa đánh giá và kiểm hash PDF khác nhau; quy tắc giữ thay đổi nằm trong `scripts/so_sanh_lan_chay.py`, không có test.

## Cách làm

Chờ hỏi đáp (grilling). Nguồn: Báo cáo kiến trúc 2026-11-11 (`C:\Users\huydt\AppData\Local\Temp\architecture-review-20261111T155046.html`), ứng viên 4.

## Comments

- 2026-11-11 (Q230 = C): không làm. Rà code: ba cách đếm (`so_sanh_nguon`, `so_sanh_lan_chay`, `so_cham`) cùng tính Mục chưa đánh giá là sai, cùng chỉ chấm Tiêu chí Bộ chuẩn đã điền; cả ba đều kiểm Lượt thuộc đúng Hợp đồng (hai script truyền PDF khi nạp Bộ chuẩn, `cham_lai_kho.py` bỏ từng Lượt khác Hợp đồng). Không có lỗi đếm; gộp lại chủ yếu làm gọn code. Quy tắc giữ thay đổi vẫn là một dòng trong `scripts/so_sanh_lan_chay.py`, không có test.
- Các việc dời từ issue 26 cũng không làm: `ket_qua_de_xuat_muc` nhận `van_ban=None` sẽ làm `--so-voi` hỏng với commit cũ; `cham_lai` trả Lượt đầy đủ chỉ cần khi gộp; KeyError khi Mục thiếu Tiêu chí đã chặn bằng kiểm Phiên bản checklist.
