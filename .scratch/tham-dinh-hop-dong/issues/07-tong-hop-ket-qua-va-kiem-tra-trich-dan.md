# 07 - Tổng hợp Kết quả và kiểm tra Trích dẫn (code thuần)

Status: done
Blocked by: 02

## Việc cần làm

- Hàm so sánh cho Tiêu chí định lượng: nhận giá trị đã trích xuất cùng phép so sánh và ngưỡng trong checklist, trả về thỏa / không thỏa / không rõ (không rõ khi thiếu giá trị).
- Tiêu chí có `dieu_kien` (ví dụ 1.V2: chỉ áp dụng khi giá trị Hợp đồng > 2 tỷ): code so sánh giá trị trích xuất với điều kiện. Không áp dụng → tiêu chí Đạt coi là thỏa, tiêu chí Lưu ý/Vi phạm coi là không thỏa. Thiếu giá trị → không rõ.
- Hàm tổng hợp Kết quả của một Mục checklist từ các Đánh giá tiêu chí, theo quy tắc mức xấu nhất thắng (xem spec), kèm giải thích Tiêu chí nào đã quyết định Kết quả. Nếu Kết quả là Vi phạm do một Tiêu chí có `can_thong_tin_ngoai: true`, kèm thông báo `GHI_CHU_CAN_THONG_TIN_NGOAI` ("các tiêu chí này cần thông tin ngoài Hợp đồng").
- Kiểm tra Trích dẫn: chuẩn hóa NFC và khoảng trắng, bỏ qua nhãn redline (so được cả với bản có nhãn lẫn bản đã chấp nhận thay đổi, xem `ban_sach()` trong `so_hoa/cau_truc.py`), so khớp nguyên văn trong Điều khoản được trỏ tới (dự phòng: tìm trong toàn bộ Văn bản hiệu lực). Không khớp → "không xác minh được".

## Tiêu chí hoàn thành

- Có test bảng cho mọi tổ hợp thỏa / không thỏa / không rõ của các mức.
- Có test cho tiêu chí có điều kiện (áp dụng / không áp dụng / thiếu giá trị) và cho thông báo cần thông tin ngoài Hợp đồng.
- Có test cho Trích dẫn khớp, lệch dấu tiếng Việt và bịa.

## Comments

**2026-10-29, hoàn thành.**

- `src/thamdinh/tong_hop.py`: `tong_hop_muc(muc, danh_gia) -> KetQuaMuc` (seam S16), gồm:
  - Đánh giá tiêu chí cuối cùng;
  - Tiêu chí quyết định Kết quả;
  - giải thích;
  - ghi chú.
- Quy tắc trong `tong_hop.py`:
  - Tiêu chí định lượng chỉ dùng `gia_tri` LLM trích xuất; `danh_gia` LLM trả cho tiêu chí này bị bỏ qua.
  - Tiêu chí có `dieu_kien` dùng `gia_tri_dieu_kien`.
  - Thiếu Đánh giá tiêu chí thì coi là không rõ.
  - Q42: tiêu chí Lưu ý/Vi phạm không rõ → Lưu ý.
- `src/thamdinh/trich_dan.py`: `kiem_tra_trich_dan(trich_dan, van_ban) -> KetQuaTrichDan` (seam S17) theo Q43. Trạng thái: `khop` | `khop_sai_so_hieu` (kèm `so_hieu_dung`) | `khong_xac_minh_duoc`.
- Ghi chú cho issue 08:
  - Schema JSON của LLM phải có `gia_tri` cho tiêu chí định lượng và `gia_tri_dieu_kien` cho tiêu chí có điều kiện (1.V2: `gia_tri_hop_dong_vnd`).
  - Trích dẫn rỗng (không có điều khoản tương ứng) hiện trả `khong_xac_minh_duoc`; issue 08 cần hiển thị lý do "Không tìm thấy điều khoản về …" thay vì báo lỗi trích dẫn.
