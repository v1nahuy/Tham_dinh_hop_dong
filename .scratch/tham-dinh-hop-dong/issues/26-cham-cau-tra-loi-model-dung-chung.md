# 26 - Một bước chấm câu trả lời model dùng chung

Status: done

## Vấn đề

Bước từ câu trả lời model ra Đánh giá tiêu chí, Kết quả Mục và Trích dẫn đã kiểm tra có hai bản (`tham_dinh._danh_gia_muc` và `cham_lai._cham_luot`), phần bọc Trích dẫn có bản thứ ba (`kho_luot.luu_duyet`). `cham_lai` bỏ qua bước cắt câu trích dài; hai bản chỉ khớp vì câu trích trong kho đã cắt sẵn.

## Cách làm (Q208–Q212)

- Module `src/thamdinh/ket_qua_de_xuat.py`, một hàm `ket_qua_de_xuat_muc(muc, tra_loi, van_ban) -> KetQuaMucDeXuat`. `tra_loi`: câu trả lời model theo mã Tiêu chí, đúng dạng JSON model trả (`danh_gia`, `ly_do`, `gia_tri`, `gia_tri_dieu_kien`, `trich_dan`). Hàm tổng hợp Đánh giá, bỏ câu trích rỗng, cắt câu trích bị llama-server cắt ở 300 ký tự, kiểm tra Trích dẫn, đặt `khong_tim_thay_dieu_khoan`. `tham_dinh._danh_gia_muc` chỉ còn gọi model rồi gọi hàm này (Q208).
- `TrichDanDaKiemTra` chuyển sang `trich_dan.py`, thêm `kiem_tra(trich_dan, van_ban)`; `ket_qua_de_xuat` và `kho_luot.luu_duyet` dùng chung; `tham_dinh` import lại tên cũ. Quy tắc cắt 300 ký tự chỉ ở `ket_qua_de_xuat`: câu trích Người thẩm định gõ khi duyệt không bị cắt (Q209).
- `cham_lai` dựng lại `tra_loi` từ Lượt đã lưu rồi gọi `ket_qua_de_xuat_muc`; tạm giữ `ChamLuot`, việc trả Lượt đầy đủ để issue 29 (Q210).
- `cham_lai_kho.py --so-voi` chỉ dùng được với commit từ issue 26 trở đi; ghi vào tài liệu thử nghiệm (Q212).

## Test (Q211)

- Seam `ket_qua_de_xuat_muc`, câu trả lời dạng dict, không cần `ModelGia`: cắt câu trích từ 300 ký tự, bỏ câu trích rỗng, không có Trích dẫn thì `khong_tim_thay_dieu_khoan`, Tiêu chí định lượng, chấm lại Mục đã lưu ra đúng Mục đó. 22 test `tham_dinh` giữ làm lưới an toàn.
- Hồi quy: `cham_lai_kho.py` trên 15 Lượt trước và sau refactor phải giống hệt (bản trước đã lưu).

## Tiêu chí hoàn thành

- Test xanh; hồi quy giống hệt; `/code-review` (Q197).

## Comments

**2026-11-11, đã làm.**
- `ket_qua_de_xuat.py`: `ket_qua_de_xuat_muc` (từ `tham_dinh._danh_gia_muc`), `tra_loi_da_luu` (dựng lại câu trả lời từ Mục đã lưu), `DanhGiaDeXuat`, `KetQuaMucDeXuat`, `TOI_DA_KY_TU_TRICH_DAN`; `trich_dan.py`: `TrichDanDaKiemTra`, `kiem_tra`. `tham_dinh` import lại các tên cũ; `_danh_gia_muc` chỉ còn gọi model; `luu_duyet` và `cham_lai` dùng chung.
- Test qua `ket_qua_de_xuat_muc`: test mới đỏ rồi xanh (module chưa có; `tra_loi_da_luu` chưa có). Ba test cắt 300 ký tự, câu rỗng, định lượng xanh ngay vì chốt hành vi chuyển từ `tham_dinh`. Lần đầu mình kỳ vọng sai Mục 1 ra Đạt: 1.V2 có điều kiện giá trị Hợp đồng > 2 tỷ, không có giá trị điều kiện thì ra Lưu ý (đúng luật); đã sửa test.
- Hồi quy: `cham_lai_kho.py` trên 15 Lượt trước và sau refactor giống hệt (`diff` rỗng). 370 test thường xanh; một lần chạy có 1 test hỏng không lặp lại được (chạy lại 6 lần xanh, chưa biết test nào).

**2026-11-11, review (Q197) và đóng (Q214).** Hai review không thấy lỗi; `ket_qua_de_xuat_muc` giữ nguyên văn hành vi cũ, cắt 300 ký tự chỉ cho câu trả lời model, `cham_lai` cho cùng kết quả. Đã sửa: đổi `trich_dan.kiem_tra` thành `kiem_tra_va_ghi` (dễ nhầm với `kiem_tra_trich_dan`); docstring `tra_loi_da_luu` ghi rõ `dieu_khoan_dua_vao`/`canh_bao` do người gọi giữ; docstring `cham_lai_kho.py` ghi giới hạn `--so-voi`. Để issue 29: `ket_qua_de_xuat_muc` nhận `van_ban=None` thay vì Văn bản hiệu lực rỗng trong `cham_lai`; khi trả Lượt đầy đủ thì giữ `dieu_khoan_dua_vao`/`canh_bao`; `tra_loi[tc.ma]` báo KeyError nếu Mục đã lưu thiếu Tiêu chí (hiện đã chặn bằng kiểm tra Phiên bản checklist). Để issue 27: các module khác import kiểu qua `tham_dinh`.
