# 13 - Bộ chuẩn TOSS (làm tay)

Status: ready-for-human
Blocked by: 02

## Việc cần làm

- Agent tạo file mẫu `eval/chuan/toss.yaml` sinh từ V1.1: mỗi Tiêu chí có ô trống cho Đánh giá tiêu chí, giá trị (nếu định lượng), Trích dẫn và vị trí.
- **Người dùng tự điền bằng tay**, đọc trực tiếp PDF TOSS, **trước khi xem bất kỳ Kết quả đề xuất nào** của hệ thống, để tránh thiên kiến neo.

## Tiêu chí hoàn thành

- Mọi Tiêu chí trong file đều có Đánh giá tiêu chí.

## Comments

**2026-10-29, phần của agent đã xong; còn chờ người dùng điền.**

- File mẫu `eval/chuan/toss.yaml` (17 Mục, 122 Tiêu chí, 12 tiêu chí có ô `gia_tri`), sinh bằng `scripts/tao_mau_bo_chuan.py`. Script không ghi đè file đã có.
- Ngoài phạm vi issue, mỗi Mục có thêm ô `ket_qua` (tùy chọn), để issue 15 so được cả quy tắc tổng hợp.
- `src/thamdinh/bo_chuan.py`: `nap_bo_chuan(file, checklist, pdf=None)` (seam S18) báo mọi lỗi kèm vị trí.
- Người dùng tự kiểm tra tiến độ bằng: `.venv/Scripts/python scripts/kiem_tra_bo_chuan.py eval/chuan/toss.yaml checklists/dau-ra-v1.1.yaml "Sample/HĐ TOSS v 12.5.2026.pdf"`.
- Tiêu chí hoàn thành đạt khi lệnh trên in "Hoàn thành: 122/122".
