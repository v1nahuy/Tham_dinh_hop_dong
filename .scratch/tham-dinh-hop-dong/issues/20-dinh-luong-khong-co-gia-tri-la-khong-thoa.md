# 20 - Tiêu chí định lượng không có giá trị thì không thỏa

Status: done

## Vấn đề

Ở Tiêu chí định lượng, model chỉ ghi `gia_tri` đọc từ Hợp đồng, code so với ngưỡng. Prompt yêu cầu "ghi null nếu Hợp đồng không nêu". Khi `gia_tri` là null, code hiện coi Tiêu chí là `khong_ro`. Bộ chuẩn chấm các ca Hợp đồng không có điều khoản tương ứng là `khong_thoa`:

- 8.D2 (chấm dứt thuận tiện báo trước ≥ 30 ngày): Hợp đồng không có điều khoản chấm dứt thuận tiện.
- 16.D4 (thông báo bất khả kháng không ngắn hơn 7 ngày): Hợp đồng ghi "ngay lập tức", không có số ngày.
- 17.D7 (non-solicitation ≥ 12 tháng): Hợp đồng không có điều khoản non-solicitation.

Cả ba chưa Lượt nào làm đúng. Tiêu chí định lượng sai 6/11 ở Lượt tốt nhất `d8c20de88c96-20261106T183634562376` (84/122).

## Cách làm (Q169)

- Tiêu chí định lượng có `gia_tri` null: Đánh giá tiêu chí cuối cùng là `khong_thoa` (Đạt: không đáp ứng yêu cầu; Lưu ý/Vi phạm: rủi ro không xảy ra).
- Phần điều kiện (`gia_tri_dieu_kien` null) giữ `khong_ro` như cũ.
- TDD qua `tong_hop_muc` (seam đã xác nhận ở Q169). Không đổi prompt, không chạy model.
- Rủi ro đã biết: ở chế độ truy xuất, null có thể do điều khoản nằm ngoài ngữ cảnh model được đọc.

## Đo và quy tắc giữ

- Chấm lại Lượt `…183634562376` từ dữ liệu đã lưu (không gọi model) bằng code mới, so với Bộ chuẩn.
- Giữ khi ≥ 87/122 và không có đúng→sai.

## Tiêu chí hoàn thành

- Test xanh; số đo theo quy tắc trên; quyết định giữ hay bỏ.

## Comments

**2026-11-09, số liệu khi đề xuất.** Ước lượng trên 6 Lượt đã có (chưa sửa code): 5 Lượt +3 (8.D2, 16.D4, 17.D7), Lượt toàn văn `…20261104T134515961445` +1 (17.D7); 16.D5 không đổi (Bộ chuẩn `thoa`, "Cần xác minh"); không có đúng→sai.

**2026-11-09, các phương án khác đã xét khi đề xuất (Q170–Q174).**
- Bỏ phiếu giữa 3–5 Lượt có sẵn: trung bình 84–85, dao động 80–88; 20 Tiêu chí chưa Lượt nào làm đúng (trần 102/122), lỗi tương quan mạnh. Bỏ (Q173), không thử lại.
- Model lớn hơn (Qwen3.5 27B, 35B-A3B): máy có 15,5 GB RAM, chỉ CPU; bản Q4 cần khoảng 16–20 GB, mạng công ty chặn tải model. Bỏ (Q173).
- Q170: thời gian chấp nhận cho một Hợp đồng tối đa khoảng 12 giờ, không quá 24 giờ.
- Q171: sau issue này, thử chế độ suy luận (`THAMDINH_SUY_LUAN=true`) trên riêng Mục 3 để đo thời gian và số đúng; cần xác nhận riêng trước khi chạy.
- Q172: hoãn hỏi mỗi Tiêu chí một lần gọi, quyết lại sau Q171.
- Q174: không có Hợp đồng mẫu thứ hai; Bộ chuẩn vẫn chỉ có TOSS, nên các mức tăng nhỏ khó tách khỏi dao động (±6–7).
- Bộ chuẩn 13.L1 ("cam kết uptime từ 99,9% trở lên") ghi `thoa` với giá trị 99, trái chữ của Tiêu chí. Chỉ báo, không sửa `toss.yaml`.

**2026-11-09, đã làm và đo.**
- TDD: `test_tieu_chi_dinh_luong_hop_dong_khong_neu_gia_tri_thi_khong_thoa` (`tests/test_tong_hop.py`) đỏ rồi xanh; `_danh_gia_cuoi` trả `khong_thoa` khi Tiêu chí định lượng có `gia_tri` null. Test cũ `(None, "luu_y")` vẫn đúng vì Đạt `khong_thoa` cũng ra Lưu ý. 364 test thường xanh.
- Chấm lại từ dữ liệu đã lưu (`tong_hop_muc` trên `danh_gia_llm`, `gia_tri`, `gia_tri_dieu_kien` của từng Tiêu chí, không gọi model):

  | Lượt | Tiêu chí | sai→đúng | đúng→sai | Kết quả Mục |
  |---|---|---|---|---|
  | `…20261106T183634562376` (tốt nhất) | 84→87/122 | 8.D2, 16.D4, 17.D7 | 0 | 12/17, không đổi |
  | `…20261104T203037846149` | 79→82 | 8.D2, 16.D4, 17.D7 | 0 | 9/17 |
  | `…20261106T091810431014` | 83→86 | 8.D2, 16.D4, 17.D7 | 0 | 7/17 |
  | `…20261107T012232562002` | 83→86 | 8.D2, 16.D4, 17.D7 | 0 | 11/17 |
  | `…20261104T134515961445` (toàn văn) | 82→83 | 17.D7 | 0 | 9/17 |
  | `…20261105T181447448588` (toàn văn) | 81→84 | 8.D2, 16.D4, 17.D7 | 0 | 10/17 |

- Đạt quy tắc giữ (≥ 87/122, không đúng→sai): GIỮ. Kết quả Mục không đổi; Mục có các Tiêu chí này mất ghi chú "chưa xác định được" và được giải thích bằng "không thỏa".
- Các Lượt đã lưu không ghi lại; Lượt mới dùng luật mới.

**2026-11-09, Q175–Q177: chạy thử chế độ suy luận trên Mục 3 (không đạt).**
- Q175: đã commit issue 20 (`f578205`).
- Q176: thêm `THAMDINH_TOI_DA_TOKEN` (`settings.py`, mặc định 4096, truyền vào `LocalClient` trong `chay_luot.py`); test `tests/test_settings.py` đỏ rồi xanh. Chưa commit.
- Q177, kiểm tra nhanh: với `response_format` JSON schema và `enable_thinking`, llama.cpp (build 11981) vẫn cho model suy luận (`reasoning_content` riêng) rồi trả JSON đúng. Một câu hỏi ngắn: 1.800 token, 320 giây (tắt suy luận: 71 token, 13 giây).
- Chạy Mục 3 tiếp từ `…183634562376` (16k, suy luận bật, tối đa 16.384 token), 09:24–11:49, Lượt `d8c20de88c96-20261109T092625540161`. Sau 145 phút model vẫn chưa viết xong một câu trả lời (15.659/16.384 token, 2,4 token/giây). Đã dừng: vượt ngưỡng thời gian Q177 (≤ 130 phút), và nếu bị cắt thì code chia đôi Tiêu chí gọi lại hai lần, có thể thêm khoảng 4 giờ. Mục 3 không có kết quả nên không đo được độ chính xác. Đã tắt hai máy chủ.
- Ước tính: bật suy luận cho cả Lượt mất trên 40 giờ trên máy này, vượt giới hạn 24 giờ (Q170).
