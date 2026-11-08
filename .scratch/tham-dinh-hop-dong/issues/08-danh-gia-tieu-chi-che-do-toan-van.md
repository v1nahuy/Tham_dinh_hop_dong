# 08 - Đánh giá tiêu chí bằng LLM, chế độ toàn văn

Status: done (test với model thật chuyển sang issue 15)
Blocked by: 04, 07

## Việc cần làm

- Prompt cho từng Mục checklist: vai trò (thẩm định cho Công ty), các Tiêu chí, Danh mục tham chiếu liên quan, các Điều khoản được chọn. Đầu ra là JSON theo schema: Đánh giá tiêu chí cho từng Tiêu chí, giá trị trích xuất cho Tiêu chí định lượng, Trích dẫn {số hiệu Điều khoản, nguyên văn}, lý do.
- Bước đầu tiên của mỗi Lượt thẩm định: xác định Công ty là bên nào trong Hợp đồng, Khách hàng là bên nào.
- Prompt nêu quy ước "tiêu chí bắt đầu bằng 'Nếu ...' coi là thỏa khi điều kiện không xảy ra". Với tiêu chí có `dieu_kien`, LLM trích xuất thêm giá trị của trường điều kiện (ví dụ `gia_tri_hop_dong_vnd`) để code quyết định tiêu chí có áp dụng không.
- Chế độ toàn văn: đưa toàn bộ Văn bản hiệu lực vào.
- Ghép với issue 07 để ra Kết quả đề xuất cho cả Lượt thẩm định.

## Tiêu chí hoàn thành

- Chạy hết 17 Mục checklist với Văn bản hiệu lực của TOSS, ra JSON hợp lệ.
- Mọi Trích dẫn đều đã qua bước kiểm tra.

## Comments

**2026-10-29, code xong, chưa chạy với model thật.**

Người dùng chọn Qwen3.5 chạy local (Q45–Q50); `ClaudeClient` đã gỡ, ADR 0001 đã sửa.

- `src/thamdinh/llm.py`: `LocalClient` gọi llama-server (API chuẩn OpenAI). Hành vi:
  - ép JSON schema qua `response_format`;
  - `enable_thinking` theo cấu hình;
  - bỏ khối `<think>` nếu model vẫn trả về;
  - báo `LLMKetNoiError` khi chưa chạy máy chủ model.

  Seam S21.
- `src/thamdinh/settings.py`: các biến `THAMDINH_MODEL`, `THAMDINH_LOCAL_URL`, `THAMDINH_NGU_CANH`, `THAMDINH_SUY_LUAN` (S22).
- `src/thamdinh/tham_dinh.py`:
  - `xay_prompt_cac_ben` và `xay_prompt_muc` (S19). Schema dạng đối tượng theo mã Tiêu chí, nên model buộc phải trả đủ đúng các mã.
  - `tham_dinh()` (S20) chạy theo thứ tự:
    1. ước tính token, vượt ngữ cảnh thì báo lỗi;
    2. xác định các bên;
    3. đánh giá 17 Mục, JSON sai thì gọi lại một lần;
    4. tổng hợp Kết quả (issue 07);
    5. kiểm tra mọi Trích dẫn.

    Mục lỗi hai lần được ghi "chưa đánh giá được".
  - `luu_luot()` ghi `data/luot/*.json`.
- `scripts/chay_tham_dinh.py`: chạy TOSS từ dòng lệnh và in bảng tóm tắt.
- `docs/chay-model-local.md`: hướng dẫn tải và chạy llama-server.
- Test thường: 134 xanh. `tests/test_llm_that.py` (marker `llm`, mặc định bỏ qua) chạy với model thật. **Tiêu chí hoàn thành "chạy hết 17 Mục với TOSS" chưa kiểm được** cho đến khi có model: chạy `pytest -m llm`.
- Prompt TOSS ước tính: phần chung khoảng 34,4k token, Mục dài nhất (Mục 2, có danh mục ngành nghề) khoảng 38,1k token. Vừa ngữ cảnh 65536.

## Comment 2026-10-30: lần chạy đầu với Qwen3.5-9B thật

**`pytest -m llm` lần 1: không đạt** (12 giờ 33 phút).
- 16/17 Mục chạy xong. Mục 14 "chưa đánh giá được": cả hai lần gọi, model sinh khoảng 20,8k token đến khi hết ngữ cảnh 49.152, nên JSON bị cắt. Mỗi lần gọi mất khoảng 3 giờ.
- Test chưa lưu Lượt trước khi kiểm tra, nên mất kết quả của 16 Mục đã chạy xong.
- Thời gian các Mục bình thường: Mục 1 mất khoảng 1,5 giờ (đọc toàn văn); các Mục sau mỗi Mục 10–25 phút.

**Đã sửa (TDD, 142 test thường xanh)**
- `LocalClient` gửi `max_tokens` (tham số `toi_da_token`, mặc định 4096). Khi `finish_reason == "length"`, client báo `LLMResponseError` "Câu trả lời bị cắt…", và `_goi` gọi lại.
- `SCHEMA_TRICH_DAN`: `maxItems` 3 và `nguyen_van` `maxLength` 300. llama-server ép theo grammar. Khi trích dẫn chạm đúng 300 ký tự, `_kiem_tra` bỏ từ cuối dở dang và thêm " …", vì ký tự cuối do grammar ép đóng chuỗi thường là rác (ví dụ "sử dụng и").
- `kiem_tra_trich_dan` chấp nhận số hiệu có dấu `###` ở đầu (model hay chép "### 8.1").
- `test_llm_that` gọi `luu_luot` trước khi assert.

**Thử riêng Mục 14 với model thật** (máy chủ còn giữ cache phần đầu prompt):

| Lần thử | Kết quả |
|---|---|
| Thêm yêu cầu "tối đa 3 trích dẫn, dưới 300 ký tự, không ghi ###" vào `NHAC_LAI_QUY_UOC` | 7,1 phút, nhưng **0 trích dẫn** ở cả 7 Tiêu chí. Đã bỏ yêu cầu này, ghi chú trong code. |
| Chỉ giới hạn bằng schema | 18,6 phút, 2.275 token, không bị cắt, mỗi Tiêu chí 1–3 trích dẫn |

Với lần thử thứ hai, kiểm tra trích dẫn bằng code mới cho 12 khớp, 6 khớp sai số hiệu (model tự đặt "Phụ lục 02, Mục D.7"; hệ thống chỉ ra "Phụ lục 02, Mục D"), 0 không xác minh được.

- Kết quả Mục 14 không ổn định giữa hai lần thử: Lưu ý ở lần 1 và Vi phạm ở lần 2 (14.V2). Chất lượng sẽ đo bằng bộ chuẩn (issue 15).
- **Còn lại:** chạy lại `pytest -m llm` đủ 17 Mục để đóng tiêu chí hoàn thành. Ước tính 5–6 giờ.

## Comment 2026-10-30: dời test với model thật sang issue 15

Người dùng quyết định chưa chạy lại `pytest -m llm` đủ 17 Mục; lần chạy này gộp vào issue 15 (issue 15 vốn chạy TOSS ở chế độ toàn văn). Trên laptop, mỗi lần chạy mất 5–6 giờ.

## Comment 2026-10-30: biện pháp chống lỗi kiểu Mục 14 (TDD, 149 test thường xanh)

- **Bị cắt thì chia đôi Mục, không gọi lại y nguyên.**
  - Ở nhiệt độ 0, gọi lại cùng prompt thì model lặp y như cũ (Mục 14: hai lần khoảng 20k token).
  - `LocalClient` báo `LLMBiCatError` (lớp con của `LLMResponseError`). `_goi` không gọi lại khi gặp lỗi này.
  - `_danh_gia_muc` chia Tiêu chí của Mục thành hai nửa: `xay_prompt_muc(..., chi_tieu_chi=...)`, giữ nguyên phần đầu prompt để dùng lại cache. Kết quả hai nửa được gộp lại trước khi tổng hợp.
  - Nếu một nửa vẫn bị cắt, Mục được ghi "chưa đánh giá được (đã chia đôi Tiêu chí)", và các Mục khác vẫn chạy tiếp.
  - JSON sai vì lý do khác thì vẫn gọi lại một lần, kèm lỗi ở cuối prompt, như cũ.
- **Lưu sau mỗi bước và chạy tiếp.**
  - `tham_dinh(..., sau_moi_buoc=…)` gửi kết quả tạm sau bước xác định các bên và sau mỗi Mục; người gọi lưu ngay bằng `luu_luot`. Một Lượt ghi đè cùng một file, theo `bat_dau`.
  - `nap_luot(file)` đọc lại Lượt đã lưu.
  - `tham_dinh(..., luot_truoc=…, chay_lai={…})` chỉ gọi model cho Mục chưa chạy, Mục "chưa đánh giá được", hoặc Mục có trong `chay_lai`. Nếu `luot_truoc` thuộc Hợp đồng khác hoặc checklist khác, hệ thống báo `ValueError`.
  - `scripts/chay_tham_dinh.py` có thêm hai tùy chọn `--tiep-tuc <file>` và `--chi-muc 14,15`. Đã chạy thử trên TOSS với một Lượt tạo bằng model giả: script không gọi model lần nào.
  - `test_llm_that` lưu sau mỗi Mục.
- Đây cũng là phần đầu của issue 10 (lưu trữ Lượt).
