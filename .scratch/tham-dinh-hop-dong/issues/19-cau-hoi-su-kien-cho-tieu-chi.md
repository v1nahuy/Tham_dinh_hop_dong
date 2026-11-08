# 19 - Câu hỏi sự kiện cho Tiêu chí

Status: ready-for-agent

## Vấn đề

Qwen3.5 9B sai lặp lại ở Tiêu chí mô tả rủi ro, nhất là khi Tiêu chí viết dạng phủ định. Ví dụ 8.V2 "Không có điều khoản về hậu quả chấm dứt": lý do "Hợp đồng có các điều khoản chi tiết về hậu quả chấm dứt" nhưng model ghi `thoa`. Lỗi gặp cả khi chấm (issue 18: 1.V1, 1.V3, 5.L1, 11.D2, 16.D5 trên Lượt `d8c20de88c96-20261106T183634562376`) lẫn khi hỏi lại chỉ với Tiêu chí và lý do (Đối chiếu lý do, issue 18: 84→66/122). Đổi thứ tự `ly_do`/`danh_gia` trong schema cũng làm nặng thêm (issue 17, Q127).

Gốc của lỗi: model phải tự kết hợp hai bước, "Hợp đồng có X không" và "Tiêu chí này mô tả rủi ro nên có X nghĩa là `thoa` hay `khong_thoa`". Bước thứ hai là chỗ phủ định lồng nhau.

## Cách làm (đã quyết khi triage, Q151–Q158)

- **Phạm vi (Q152):** mọi Tiêu chí định tính (111: 57 Đạt, 34 Vi phạm, 20 Lưu ý) có một câu hỏi sự kiện. 11 Tiêu chí định lượng giữ cách cũ: model ghi `gia_tri`, code so ngưỡng.
- **Lưu ở file riêng (Q154):** `checklists/cau-hoi-su-kien/dau-ra-v1.1.yaml`, mỗi mã Tiêu chí có `cau_hoi` và `thoa_khi` (`co` | `khong`). Khi nạp, kiểm tra file phủ đúng mọi Tiêu chí định tính, không thừa không thiếu. Không tạo checklist v1.2: checklist bất biến và Bộ chuẩn `toss.yaml` gắn với "dau-ra 1.1".
- **Soạn (Q155):** agent soạn chỉ từ chữ trong checklist, không xem Bộ chuẩn hay lý do trong Lượt (tránh khớp riêng với TOSS). Tiêu chí ghép "và/hoặc" và Tiêu chí "Nếu …" được đánh dấu để duyệt kỹ. Người dùng duyệt cả file trước khi chạy model.
- **Prompt (Q153):** phần "Các Tiêu chí cần đánh giá" chỉ còn danh sách câu hỏi (`- 8.V2: Hợp đồng có điều khoản về hậu quả chấm dứt không?`), không còn mô tả Tiêu chí và nhãn [Đạt]/[Lưu ý]/[Vi phạm]. Schema: `danh_gia` đổi thành `tra_loi` (`co` | `khong` | `khong_ro`), vẫn đứng trước `ly_do`. Trong `HUONG_DAN_CHUNG` và `NHAC_LAI_QUY_UOC`: thay đoạn "Ý nghĩa của danh_gia … kể cả [Vi phạm]" bằng ý nghĩa của có/không; viết lại "Xét chặt" (câu hỏi nêu nhiều yếu tố thì chỉ `co` khi có đủ) và "Nếu …" (câu hỏi bắt đầu bằng "Nếu …" thì `co` khi điều kiện không xảy ra) theo câu hỏi.
- **Quy đổi:** code đổi `tra_loi` ra `danh_gia_llm` theo `thoa_khi`; `khong_ro` giữ `khong_ro`. Phần điều kiện (`dieu_kien`) và tổng hợp Mục như cũ.
- **Lượt (Q156):** `DanhGiaDeXuat` thêm `cau_hoi` và `tra_loi` (trống với Lượt cũ và Tiêu chí định lượng). UI và báo cáo docx giữ nguyên trong issue này.
- **Thuật ngữ (Q158):** thêm "Câu hỏi sự kiện" vào `GLOSSARY.md` chỉ khi quyết định giữ.

## Đo và quy tắc giữ (Q151, Q157)

1. Thử trước: chạy lại Mục 1, 5, 11, 16 (chứa 5 ca đánh dấu tay) bằng `chay_tham_dinh.py <pdf> --tiep-tuc d8c20de88c96-20261106T183634562376 --chi-muc 1,5,11,16`, ngân sách 16k (~2 giờ). Đi tiếp khi bắt ≥ 3/5 ca và đúng→sai ≤ 2 trên 4 Mục đó.
2. Cả Lượt (~9 giờ): giữ khi ≥ 87/122 (tăng ≥ 3), đúng→sai ≤ 5, và Mục 1 không còn bị báo Vi phạm sai.
- Mỗi lần chạy model cần xác nhận riêng.

## Tiêu chí hoàn thành

- File câu hỏi sự kiện đã được người dùng duyệt.
- Code theo cách làm trên, test xanh (seam xác nhận trước khi viết test).
- Báo cáo đo bước 1 (và bước 2 nếu đi tiếp), quyết định giữ hay bỏ theo quy tắc trên.

## Liên quan

- Issue 18 (wontfix): Đối chiếu lý do không đạt.
- Issue 17: prompt "xét chặt", thứ tự schema.
- Nhóm `khong_ro` (Q120) có thể xét chung vì câu hỏi có/không rõ hơn.

## Comments

**2026-11-08, số liệu khi triage.**
- 38 Tiêu chí sai của Lượt tốt nhất (84/122): Đạt 14/57, Vi phạm 9/34, Lưu ý 9/20, định lượng 6/11. Loại "lý do và đánh giá ngược nhau" (hướng này nhắm vào) chỉ 5 ca, nên phần chắc gỡ được tối đa khoảng +5, sát mức dao động ±6–7. Lợi ích thứ hai là bớt chao đảo khi đổi prompt (Lượt Q127: 7 đúng→sai thuộc loại này).
- Phần lớn lỗi ở Đạt là chấm dễ dãi (`thoa` thay vì `khong_thoa`); hướng này không nhắm vào đó.
- Chỉ 11/122 Tiêu chí mở đầu bằng "Không/Chưa/Thiếu"; nhiều Tiêu chí khác có phủ định giữa câu (1.V1).
- `nap_bo_chuan` kiểm tra tên checklist "dau-ra 1.1", nên không tạo checklist phiên bản mới được mà không sửa Bộ chuẩn.
- Ở Tiêu chí định lượng, `danh_gia_llm` không được dùng (`_danh_gia_cuoi` chỉ so `gia_tri`).

**2026-11-08, triage xong.** Người dùng đồng ý Q151–Q158. Chuyển `ready-for-agent`.

**2026-11-08, quyết định Q159–Q162 và đã làm.**
- Q162: `git init` cục bộ (không remote), `.gitignore` loại `data/`, `eval/`, `sample/`, `models/`, `.venv/`, `.pytest_cache/`, `*.egg-info/`. Mốc trước issue này: commit `a60f599`.
- Q159: soạn `checklists/cau-hoi-su-kien/dau-ra-v1.1.yaml` trước (111 câu, `# XEM KỸ` ở 20 câu), chờ người dùng duyệt; code làm song song. Tiêu chí là phần bù của nhau dùng chung câu hỏi (2.D1/2.V1, 6.D1/6.L1, 7.D3/7.L2, 17.D1/17.V3, 17.D6/17.V1).
- Q160/S1: `load_checklist` gắn `cau_hoi`/`thoa_khi` vào `TieuChi` định tính từ `cau-hoi-su-kien/<tên file checklist>`; báo lỗi khi thiếu file, sai tên checklist, thiếu/thừa mã, Tiêu chí định lượng có câu hỏi, `thoa_khi` sai, hoặc câu "Nếu …" sai chiều (Đạt phải `co`, Lưu ý/Vi phạm phải `khong`; quy tắc này bắt được một lỗi soạn ở 3.L1).
- S2: prompt "Các câu hỏi cần trả lời", không còn mô tả và nhãn Tiêu chí định tính; `HUONG_DAN_CHUNG`/`NHAC_LAI_QUY_UOC` viết theo có/không. Schema: `tra_loi` (`co`/`khong`/`khong_ro`) trước `ly_do`; định lượng chỉ `gia_tri`. Đuôi prompt ngắn hơn bản cũ (Mục 1: 1380/1566 ký tự).
- S3: `quy_doi(tc, tra_loi)`; `danh_gia_llm` là giá trị quy đổi (None ở định lượng); `DanhGiaDeXuat` thêm `cau_hoi`, `tra_loi`. S4: Lượt cũ nạp được.
- UI `ket_qua.py`: không hiện "(model trả lời …)" khi `danh_gia_llm` là None. `ModelGia` trong test nhận kịch bản theo `danh_gia` và đổi ra `tra_loi`.
- 377 test thường xanh (cả `test_app`). Test `pytest -m llm` không phụ thuộc schema, chưa chạy.
