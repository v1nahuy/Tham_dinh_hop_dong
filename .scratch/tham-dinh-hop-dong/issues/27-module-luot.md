# 27 - Module Lượt: kiểu dữ liệu và định dạng lưu

Status: ready-for-agent
Blocked by: 26

## Vấn đề

Quy tắc định dạng Lượt rải ở `tham_dinh.py` (`luot_tu_dict`, `muc_tu_dict`) và `kho_luot.py` (`luu`, `nap`): trường lạ gây `TypeError` (issue 19), `muc_tu_dict` bỏ qua trường mới, `KhoLuot.luu` làm mất trường mới ở cấp Lượt. Các module khác import `tham_dinh` chỉ để lấy kiểu.

## Cách làm (Q216–Q222)

- `src/thamdinh/luot.py`: `KetQuaLuot`, `CacBen` (từ `tham_dinh`), `luot_tu_dict` và hàm dựng phần con, `luot_den_dict` mới. Kiểu con ở lại module sở hữu: `KetQuaMucDeXuat`/`DanhGiaDeXuat` (`ket_qua_de_xuat`), `TrichDanDaKiemTra` (`trich_dan`), `KetQuaMuc` (`tong_hop`) (Q216).
- Định dạng đổi: trường lạ ở bất kỳ cấp nào → `DinhDangLuotError` kèm mã Lượt, chỗ và tên trường; thiếu trường có mặc định → mặc định; thiếu trường bắt buộc → `DinhDangLuotError`. Không thêm số phiên bản (Q217, giữ hướng Q188).
- `KhoLuot.luu` ghi `chung` từ `luot_den_dict` (mọi trường trừ cột chỉ mục và `muc`), không còn danh sách 3 khóa cố định (Q218).
- Bỏ `luu_luot`/`nap_luot` (chỉ test dùng), chuyển test sang `luot_den_dict`/`luot_tu_dict` (Q219).
- Import kiểu từ module sở hữu; `tham_dinh` thôi re-export. `cham_lai` giữ `KetQuaLuot` dưới `TYPE_CHECKING` để `--so-voi` vẫn so được từ issue 26 (Q220).
- Một bảng tên Kết quả ở `tong_hop.TEN_KET_QUA` (Q222).

## Test (Q221)

- Seam `luot_tu_dict`/`luot_den_dict`: round-trip Lượt có mọi trường khác mặc định; trường lạ ở Tiêu chí → `DinhDangLuotError` có mã Lượt, mã Tiêu chí, tên trường; thiếu trường tùy chọn (định dạng cũ) → mặc định. Test qua `KhoLuot` giữ làm lưới an toàn.
- Hồi quy: 15 Lượt thật nạp được; `cham_lai_kho.py` giống hệt trước.

## Tiêu chí hoàn thành

- Test xanh; hồi quy giống hệt; `/code-review` (Q197).

## Comments

**2026-11-11, đã làm.**
- `luot.py`: `KetQuaLuot`, `CacBen`, `luot_den_dict`, `luot_tu_dict`, `DinhDangLuotError`. Mọi cấp (Lượt, các bên, Mục, Kết quả Mục, Tiêu chí, Trích dẫn) dựng qua một hàm `_dung`: trường lạ → lỗi nêu mã Lượt, chỗ và tên trường; thiếu trường có mặc định → mặc định; thiếu trường bắt buộc → lỗi.
- `KhoLuot`: `COT_LUOT` là một danh sách cột dùng cho cả INSERT và SELECT; `chung` ghi mọi trường còn lại của Lượt.
- Bỏ `luu_luot`/`nap_luot` và 3 test của chúng (round-trip chuyển sang `test_luot.py`). Import kiểu từ module sở hữu; `tham_dinh` bỏ các import không còn dùng. Một bảng tên Kết quả ở `tong_hop.TEN_KET_QUA` (bỏ 4 bản sao ở `bang_ket_qua`, `bo_chuan`, `tham_dinh`, `scripts/chay_tham_dinh.py`).
- TDD qua `luot_tu_dict`/`luot_den_dict`: round-trip (đỏ vì chưa có module, rồi xanh); trường lạ ở Tiêu chí và ở cấp Lượt (đỏ: ra `TypeError`); định dạng cũ thiếu trường tùy chọn (xanh); thiếu `model` (xanh) và thiếu `muc` (đỏ: trước đó âm thầm trả Lượt rỗng).
- Hồi quy: 15 Lượt thật nạp được; `cham_lai_kho.py` giống hệt bản trước issue 26; `--so-voi HEAD` không có chuyển trạng thái nào. 373 test thường xanh.
