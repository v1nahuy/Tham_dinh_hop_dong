# 09 - Chế độ truy xuất theo cấu trúc

Status: done (cần quay lại test: độ phủ Trích dẫn Bộ chuẩn khi Bộ chuẩn có Trích dẫn đúng; lưới an toàn với bge-m3 thật)
Blocked by: 08

## Việc cần làm

- Gắn Chủ đề: LLM đọc từng Điều khoản (giới hạn ngữ cảnh ~32k) và gắn Chủ đề từ danh sách Chủ đề của Phiên bản checklist. Lưu kết quả cùng Văn bản hiệu lực.
- Chọn Điều khoản cho mỗi Mục checklist: mọi Điều khoản mang Chủ đề khai báo, cộng top-k BM25 + embedding (bge-m3, chạy local) làm lưới an toàn. Cắt bớt theo ngân sách token nếu vượt.
- Tùy chọn chế độ (toàn văn / truy xuất) trên UI và trong code.

## Tiêu chí hoàn thành

- Với TOSS, mọi Trích dẫn trong Bộ chuẩn (`eval/chuan/toss.yaml`) đều nằm trong ngữ cảnh truy xuất của Mục tương ứng (`do_phu_ngu_canh`; thay cho tiêu chí cũ "Mục 4 lấy được Phụ lục 03, Mục 10 lấy được Điều 4 và Phụ lục 01", theo Q60).
- Ngữ cảnh đưa vào cho mỗi Mục không vượt ngân sách cấu hình.

## Comments

**2026-10-30, quyết định thiết kế (Q51–Q57).**
- **Q51, embedding:** bge-m3 bản GGUF (Q8_0, khoảng 0,6 GB), chạy bằng `llama-server --embedding` trên cổng 8081. Gọi qua API `/v1/embeddings`, đặt sau một interface.
  - Khi chưa chạy máy chủ embedding: chỉ dùng BM25, và ghi cảnh báo vào Lượt.
  - File model là bản chuyển đổi của cộng đồng, nên phải ghi SHA-256. Tải ở nhà vì mạng công ty chặn Hugging Face.
- **Q52, gắn Chủ đề:**
  - Mỗi lần gọi gửi một nhóm Điều khoản liền nhau, tối đa khoảng 4k token. Điều khoản lớn hơn mức đó được gửi riêng.
  - Model trả về JSON theo từng Điều khoản. Chỉ nhận mã Chủ đề có trong danh sách Chủ đề của Phiên bản checklist.
  - Kết quả lưu trong `data/` và dùng lại theo nội dung Văn bản hiệu lực, Phiên bản checklist và model. Khi Văn bản hiệu lực bị sửa tay thì khóa đổi, nên gắn lại.
- **Q53, phạm vi lấy Điều khoản:**
  - Chọn một Điều khoản thì lấy cả các Điều khoản con cháu của nó.
  - Điều khoản cha chỉ đưa dòng tiêu đề.
  - Ngữ cảnh xếp theo thứ tự trong Hợp đồng, dùng cùng dấu `### số hiệu` như chế độ toàn văn.
- **Q54, ngân sách:** 16k token văn bản cho mỗi Mục, cấu hình bằng `THAMDINH_NGAN_SACH_TRUY_XUAT`.
  - Thứ tự ưu tiên: Điều khoản lấy theo Chủ đề trước, Điều khoản do lưới an toàn tìm được sau. Trong mỗi nhóm, xếp theo điểm liên quan.
  - Vượt ngân sách thì bỏ nguyên Điều khoản, không cắt giữa một Điều khoản, và ghi cảnh báo.
  - Không tách bảng lớn. Phụ lục 02, Mục A của TOSS khoảng 11,5k token; ảnh hưởng của nó sẽ đo ở issue 15. Ngân sách cũng sẽ chốt theo số đo thật ở Q56.
- **Q55, lưới an toàn:**
  - Câu truy vấn gồm câu hỏi của Mục và mô tả các Tiêu chí.
  - Lấy top-5 BM25 và top-5 embedding, bỏ những Điều khoản đã lấy theo Chủ đề.
  - BM25 tách từ theo âm tiết và cặp âm tiết liền nhau (bigram).
- **Q56:** test với model thật (marker `llm`) chạy ở cuối issue này. Test kiểm Mục 4 và Mục 10 của TOSS, và in ra bảng token từng Mục so với ngân sách.
- **Q57, các điểm test:**
  - `gan_chu_de` với model giả;
  - `chon_dieu_khoan` là code thuần;
  - BM25 tiếng Việt;
  - `tham_dinh(..., che_do="truy_xuat")` với model giả;
  - test với model thật.
- **Hệ quả về thời gian trên laptop:** ở chế độ truy xuất, ngữ cảnh khác nhau giữa các Mục, nên gần như không dùng lại được cache. Ước tính một Lượt mất khoảng 4 giờ, so với 5–6 giờ ở chế độ toàn văn. Trên máy chủ GPU, chênh lệch này không đáng kể.

**2026-10-30, đã làm và chạy thật lần 1.**

Code (TDD, 182 test thường xanh):
- `src/thamdinh/truy_xuat.py`:
  - `gan_chu_de`;
  - `chon_dieu_khoan`;
  - `BoTimBM25`, `BoTimNhung`, `LocalEmbeddingClient`, `tao_bo_tim_kiem`;
  - `TruyXuat`, `chuan_bi_truy_xuat`.
- `tham_dinh(..., truy_xuat=…)`. Lượt ghi `che_do`, `canh_bao`, và với mỗi Mục ghi `dieu_khoan_dua_vao` và `canh_bao`.
- Cấu hình mới: `THAMDINH_NGAN_SACH_TRUY_XUAT`, `THAMDINH_EMBEDDING_URL`, `THAMDINH_EMBEDDING_MODEL`.
- `scripts/chay_tham_dinh.py --che-do truy_xuat`.

`pytest -m llm tests/test_truy_xuat_that.py` với Qwen3.5-9B, chỉ BM25 (chưa có bge-m3): **2 đạt, 1 không đạt**.
- Gắn Chủ đề TOSS:
  - 8 nhóm, 54 phút. Kết quả lưu ở `data/chu-de/`.
  - 50/148 Điều khoản không có Chủ đề.
  - Phụ lục 02, Mục A được gắn 5 Chủ đề (chạm mức tối đa).
- Mục 4 lấy đủ các khoản về dữ liệu cá nhân của Phụ lục 03: **đạt**. Không Mục nào vượt ngân sách: **đạt**.
- Mục 10: **không đạt** vì thiếu 4.3.4.
  - 4.3.4 là khoản gia hạn bảo đảm thực hiện hợp đồng. Khoản này chỉ nhắc qua "thanh toán chi phí gia hạn", nên không phải điều khoản thanh toán.
  - Mọi khoản thanh toán của Điều 4 (4.1–4.5) và Phụ lục 01, Mục B đều được lấy.
  - Cách test chọn khoản cần có ("có chữ thanh toán") quá rộng.
- **Vấn đề phân bổ ngân sách:**
  - Mục 2 (đối tượng, phạm vi) bỏ trọn Phụ lục 02 (yêu cầu kỹ thuật). Lý do: cả cây khoảng 15k token theo ước tính, không vừa phần ngân sách còn lại.
  - Mục 3 (sở hữu trí tuệ) lại lấy Phụ lục 02, Mục A, và vì thế bỏ 6.3, Phụ lục 03, 4.2…
  - Ước tính token (độ dài chia 2,5) cao hơn thực tế khoảng 18%: TOSS ước 33,2k, thật 27,4k.

**2026-10-30, Q58 và Q59 (TDD, 189 test thường xanh).**
- **Q58:**
  - Khi một cây không vừa ngân sách, hệ thống thử phần riêng của Điều khoản gốc, rồi đến từng Điều khoản con. Không cắt giữa một Điều khoản.
  - Trong nhóm lấy theo Chủ đề, Điều khoản lớn hơn nửa ngân sách được xếp sau cùng.
  - Điều khoản đã bỏ thì không thử lại.
- **Q59:**
  - `LocalClient.dem_token` gọi `/tokenize` của llama-server.
  - `chuan_bi_truy_xuat(..., dem_token=…)`: không gọi được thì quay về cách ước tính đếm dư và ghi cảnh báo.
  - Phần kiểm tra độ dài ở chế độ toàn văn vẫn dùng cách ước tính.

Kết quả chọn Điều khoản cho TOSS: dùng Chủ đề đã gắn, BM25, đếm token chính xác.

| Mục | token / 16000 | bị bỏ |
|---|---|---|
| 2, 3, 6, 16 | 15,5–15,9k | (Phụ lục 02, Mục A vừa; 6 bỏ 9.3.4) |
| 4, 5 | 15,6–15,8k | Phụ lục 05; 5.4 |
| 11, 15 | 15,7–15,9k | 9.1, 10.1, Phụ lục 03, 3.2, 11.1; Phụ lục 03, 3.2 |
| 13, 14, 17 | 6,2–8,7k | Phụ lục 02, Mục A |
| 1, 7, 8, 9, 10, 12 | 1,6–6,7k | không |

- Phụ lục 02, Mục A (khoảng 11,3k token) được gắn 5 Chủ đề, nên vào cả những Mục không cần nó, như Mục 3 (sở hữu trí tuệ). Trong khi đó Mục 13 (phạm vi, nghiệm thu) lại không còn chỗ cho nó.
- 8/17 Mục chạm khoảng 16k token, nên trên laptop một Lượt vẫn tốn nhiều thời gian.
- Ảnh hưởng đến chất lượng sẽ đo ở issue 15.

**2026-10-30, Q60/Q61.**
- Tiêu chí hoàn thành đổi thành độ phủ Trích dẫn của Bộ chuẩn, dùng chung cho mọi Hợp đồng có Bộ chuẩn.
  - `bo_chuan.doc_trich_dan_chuan`: đọc Trích dẫn kể cả khi Bộ chuẩn chưa điền xong.
  - `truy_xuat.do_phu_ngu_canh`: mỗi Trích dẫn được xếp vào một trong ba trạng thái: co | thieu | khong_co_trong_van_ban. Trạng thái khong_co_trong_van_ban nghĩa là Bộ chuẩn chép không đúng nguyên văn, nên không tính vào độ phủ.
  - Đã bỏ hai test riêng cho Mục 4 và Mục 10 của TOSS. 194 test thường xanh.
- Q61: người dùng tự sửa Bộ chuẩn, nên không xử lý riêng dấu "|".
- `nap_bo_chuan` và `scripts/kiem_tra_bo_chuan.py`: khi file sai cú pháp YAML (ví dụ có Tab), báo dòng và cột thay vì traceback, và không in tiến độ sai. Khi `gia_tri` có dấu chấm phân cách hàng nghìn, gợi ý cách ghi đúng.
- Hiện tại Bộ chuẩn còn Tab ở dòng 45, và 3 Trích dẫn đã điền đều chưa đúng nguyên văn. Issue này chờ Bộ chuẩn có Trích dẫn đúng thì mới chạy được test độ phủ.
- Chưa kiểm với embedding bge-m3 thật, vì chưa tải model.

**2026-11-02, chạy lại với bge-m3 thật (`pytest -m llm tests/test_truy_xuat_that.py`): 1 đạt, 1 không đạt.**
- Không Mục nào vượt ngân sách: **đạt**.
- Độ phủ Trích dẫn của Bộ chuẩn: **không đạt**, vì chưa đọc được Bộ chuẩn (còn Tab ở dòng 45). Chưa có số đo độ phủ. Chờ người dùng sửa `eval/chuan/toss.yaml`.
- Lượt truy xuất thật mất khoảng 8,3 giờ, không phải 4 giờ như ước tính ở Q57, tức lâu hơn toàn văn (5 giờ 58 phút).
