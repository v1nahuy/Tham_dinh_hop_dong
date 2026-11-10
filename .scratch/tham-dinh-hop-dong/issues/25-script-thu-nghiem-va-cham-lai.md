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

## Comments

**2026-11-10, đã làm (commit `68e2053`).**
- TDD qua `cham_lai()`/`so_cham()`: tổng hợp lại theo luật hiện tại (7.D1 định lượng không giá trị → `khong_thoa`), kiểm lại Trích dẫn, Lượt không nạp được ghi vào lỗi, `so_cham` đếm chuyển trạng thái, JSON giữ nguyên kết quả.
- Chạy thật `cham_lai_kho.py --so-voi f6997a6` (trước issue 22): 37 Trích dẫn `khong_xac_minh_duoc → khop`, 180 / 1480 / 444 không đổi, khớp số đo issue 22. `--so-voi f578205~1` (trước issue 20): Lượt `…183634562376` 84→87 (8.D2, 16.D4, 17.D7), Lượt toàn văn `…20261104T134515961445` 82→83 (17.D7), khớp bảng issue 20. Worktree tạm được dọn.
- `do_thu_nghiem.py` thử khi máy chủ tắt: báo lỗi rồi in "Xong chuỗi", không chạy model.

**2026-11-10, review (Q197) và sửa (Q203–Q206).**
- Q203: phiên Claude Code chính được đọc nội dung lấy từ Hợp đồng để phát triển; subagent và API ngoài khác thì không. Giữ lý do của model trong nhật ký chuỗi; tài liệu ghi lại quy tắc này.
- Q204 (TDD): mọi lỗi khi chấm một Lượt ghi vào `loi`, kể cả Lượt dùng Phiên bản checklist khác; `ChamLuot` mang `hash_pdf` (script so Bộ chuẩn theo hash, không theo tiền tố mã Lượt); Lượt thiếu Văn bản hiệu lực có `trich_dan = None` và script báo ra; thêm test Mục chưa đánh giá được (xanh ngay, chốt hành vi có sẵn). `cham_lai_kho.py` in lỗi của cả code cũ và code hiện tại, `_loc` lọc cả `loi`, kiểm commit trước khi tạo worktree, dọn worktree không che lỗi gốc và chạy `git worktree prune`.
- Q205: `do_thu_nghiem.py` bắt buộc `--tang-toi-thieu`/`--dung-thanh-sai-toi-da`; báo lỗi khi thiếu PDF; khi lỗi hoặc bị ngắt thì dừng Lượt chạy nền và ghi traceback vào nhật ký; kiểm mã thoát `so_sanh_lan_chay.py`; lệnh mẫu có `2>&1`.
- Q206: tài liệu ghi rõ `--so-voi` dùng `cham_lai.py` của bản đang sửa; "Người thẩm định điền tay". Bỏ qua các nhận định về đặt tên, `main()`, `_kiem_tra` của `tham_dinh` (kết quả hiện tương đương vì câu trích trong kho đã cắt sẵn).
- Chạy lại `--so-voi f6997a6` sau khi sửa: vẫn 37.
