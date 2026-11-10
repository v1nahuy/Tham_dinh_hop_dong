# 25 - Script chạy thử model và chấm lại kho

Status: ready-for-agent

## Vấn đề

Retro chuỗi issue 17–22 (Q195): mỗi lần thử nghiệm agent viết lại một script chuỗi trong scratchpad (8 bản `chuoi_*.py`) và một script chấm lại Lượt đã lưu (5 bản). Scratchpad mất khi hết phiên. `docs/agents/thu-nghiem-model.md` trỏ tới hai script dưới đây.

## Cách làm (Q195, Q198)

- `src/thamdinh/cham_lai.py`:
  - `cham_lai(kho, checklist, thu_muc)`: với mỗi Lượt nạp được, tổng hợp lại Đánh giá từng Tiêu chí từ câu trả lời model đã lưu (`danh_gia_llm`, `gia_tri`, `gia_tri_dieu_kien`) bằng `tong_hop_muc`, tính lại Kết quả Mục, kiểm lại trạng thái từng Trích dẫn với Văn bản hiệu lực Lượt đã dùng. Lượt không nạp được ghi vào lỗi, không dừng.
  - `so_cham(truoc, sau, bo_chuan)`: đếm sai→đúng, đúng→sai so với Bộ chuẩn, Kết quả Mục đổi, chuyển trạng thái Trích dẫn.
  - Đọc/ghi JSON để so giữa hai bản code.
- `scripts/cham_lai_kho.py [--so-voi <commit>]`: `--so-voi` chạy phần chấm trong một git worktree tạm ở commit đó rồi so với code hiện tại.
- `scripts/do_thu_nghiem.py`: chạy tiếp Lượt gốc với các Mục chọn và biến môi trường đặt thêm, tự dừng khi quá thời gian, so bằng `so_sanh_lan_chay`, in từng Tiêu chí so với Bộ chuẩn.

## Test (Q198)

- Seam `cham_lai()` và `so_cham()` với kho tạm, Lượt giả (`tham_dinh` + `ModelGia`), Bộ chuẩn nhỏ.
- Không có test: worktree của `cham_lai_kho.py`, toàn bộ `do_thu_nghiem.py` (chỉ nối các phần đã có test). Kiểm bằng chạy thật: `cham_lai_kho.py --so-voi f6997a6` phải ra 37 Trích dẫn khớp lại như issue 22.

## Tiêu chí hoàn thành

- Test xanh; lần chạy thật trên khớp số đo issue 22; tài liệu và `CLAUDE.md` commit cùng (Q199); `/code-review` (Q197).
