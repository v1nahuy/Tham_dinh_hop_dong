# Chạy model Qwen3.5 trên máy (llama.cpp)

Hệ thống gọi model qua `llama-server` của llama.cpp, chỉ nghe trên `127.0.0.1`: dữ liệu Hợp đồng không rời khỏi máy (ADR 0001).

## 1. File cần có

| File | Nguồn | Vị trí |
|---|---|---|
| `Qwen3.5-9B-Q4_K_M.gguf` (5,68 GB, SHA-256 `03b74727a860a56338e042c4420bb3f04b2fec5734175f4cb9fa853daf52b7e8`) | huggingface.co/unsloth/Qwen3.5-9B-GGUF (không có kho GGUF chính thức của Qwen) | `models/qwen/` |
| llama.cpp bản Windows (`llama-bXXXXX-bin-win-cpu-x64.zip`, hoặc `...-vulkan-x64.zip`) | github.com/ggml-org/llama.cpp/releases | giải nén vào `models/llama.cpp/cpu/` (hoặc `vulkan/`) |

Mạng công ty có lúc chặn CDN của Hugging Face (`us.aws.cdn.hf.co`); khi đó tải ở mạng khác rồi chép vào. GitHub luôn vào được. Kiểm tra file model sau khi tải: `sha256sum models/qwen/Qwen3.5-9B-Q4_K_M.gguf`.

## 2. Chạy máy chủ model

```
models\llama.cpp\cpu\llama-server.exe -m models\qwen\Qwen3.5-9B-Q4_K_M.gguf --alias qwen3.5 --host 127.0.0.1 --port 8080 -c 49152 -fa on -ctk q8_0 -ctv q8_0 --jinja -np 1
```

- `-c 49152` phải khớp `THAMDINH_NGU_CANH=49152` trong `.env`. TOSS thực tế khoảng 27,8k token; prompt dài nhất khoảng 30k token.
- `-ctk q8_0 -ctv q8_0` (cần `-fa on`): nén bộ nhớ ngữ cảnh để tiết kiệm RAM.
- `--jinja` bắt buộc, để hệ thống tắt được chế độ suy luận của Qwen3.5 (`enable_thinking`).
- `-np 1`: một luồng xử lý, để phần đầu prompt (toàn văn Hợp đồng) được dùng lại giữa các Mục.
- Để cửa sổ này mở trong suốt quá trình thẩm định.

## 3. Kiểm tra và chạy

```
.venv\Scripts\python -m pytest -m llm
.venv\Scripts\python scripts\chay_tham_dinh.py "Sample\HĐ TOSS v 12.5.2026.pdf"
```

Kết quả lưu vào `data/tham-dinh.sqlite3` ngay sau mỗi Mục, nên tắt máy giữa chừng không mất các Mục đã chạy xong.

- **Xem danh sách Lượt và mã Lượt:**
  ```
  .venv\Scripts\python scripts\chay_tham_dinh.py --danh-sach
  ```
- **Chạy tiếp một Lượt.** Lệnh này chỉ chạy các Mục chưa chạy hoặc "chưa đánh giá được", và vẫn ghi vào chính Lượt đó:
  ```
  .venv\Scripts\python scripts\chay_tham_dinh.py "Sample\HĐ TOSS v 12.5.2026.pdf" --tiep-tuc <mã Lượt>
  ```
- **Chạy lại cả Mục đã có kết quả.** Hệ thống tạo Lượt mới, ghi lại Lượt gốc. Lượt cũ và Kết quả đã duyệt của nó giữ nguyên.
  ```
  .venv\Scripts\python scripts\chay_tham_dinh.py "Sample\HĐ TOSS v 12.5.2026.pdf" --tiep-tuc <mã Lượt> --chi-muc 14
  ```

## 3a. Chạy từ giao diện

```
.venv\Scripts\python -m streamlit run app.py
```

Trang **Thẩm định**:

- **Khởi chạy.** Chọn Văn bản hiệu lực, Phiên bản checklist và chế độ, rồi bấm "Chạy Thẩm định". Lượt chạy ở một tiến trình nền, chính là script ở mục 3, nên đóng trình duyệt hay tắt Streamlit thì Lượt vẫn chạy tiếp.
- **Kiểm tra máy chủ.** Trước khi chạy, giao diện kiểm `llama-server`. Chưa chạy hoặc đang nạp model thì báo lỗi kèm lệnh khởi động.
- **Theo dõi.** Trang tự làm mới 10 giây một lần, hiện số Mục đã xong và vài dòng cuối của nhật ký. Nhật ký lưu trong `data/nhat-ky/`.
- **Mỗi lúc chỉ một Lượt**, vì máy chủ chạy `-np 1`.
- **Dừng.** Nút "Dừng" giữ lại các Mục đã xong. Muốn chạy tiếp thì bấm "Chạy lại phần lỗi".
- **Chạy lại phần lỗi.** Chỉ chạy các Mục lỗi hoặc chưa chạy, vẫn trên cùng Lượt. Nếu chọn thêm Mục đã có kết quả thì hệ thống tạo Lượt mới; Lượt cũ và các Kết quả đã duyệt của nó giữ nguyên.

Trang **Kết quả**:

- **Bảng tổng hợp.** Bảng 17 Mục, màu theo Kết quả. Từng Mục có các Đánh giá tiêu chí và Trích dẫn kèm trạng thái xác minh.
- **Xem trang.** Nút "Xem trang" mở ảnh trang, tô vùng Điều khoản chứa câu trích.
- **Duyệt.** Form duyệt gồm Kết quả, giải thích và Trích dẫn. Mỗi lần lưu là một phiên bản mới.
- **Người duyệt.** Tên người duyệt đặt sẵn bằng `THAMDINH_NGUOI_DUYET` trong `.env`, hoặc nhập trên trang.
- **Báo cáo.** Nút "Tải báo cáo (.docx)" tạo báo cáo theo bố cục checklist; Mục chưa duyệt ghi Kết quả đề xuất kèm "(đề xuất, chưa duyệt)". Số hợp đồng được dò sẵn từ Văn bản hiệu lực và sửa được trước khi tải; nếu còn để trống thì trang và báo cáo đều có cảnh báo.

## 3b. Chế độ truy xuất (issue 09)

```
.venv\Scripts\python scripts\chay_tham_dinh.py "Sample\HĐ TOSS v 12.5.2026.pdf" --che-do truy_xuat
```

- **Lần đầu, hệ thống gắn Chủ đề cho từng Điều khoản.** Với TOSS, việc này mất khoảng 40 phút trên CPU. Kết quả lưu trong `data/chu-de/` và được dùng lại cho các lần chạy sau. Khi Văn bản hiệu lực, Phiên bản checklist hoặc model thay đổi, hệ thống gắn lại.
- **Mỗi Mục chỉ đọc một phần Hợp đồng:** các Điều khoản mang Chủ đề của Mục, cộng top-5 BM25 và top-5 embedding. Ngân sách đặt bằng `THAMDINH_NGAN_SACH_TRUY_XUAT` trong `.env`, mặc định 16.000 token văn bản mỗi Mục.
- **Embedding bge-m3 là tùy chọn.** Nếu không chạy máy chủ embedding, lưới an toàn chỉ dùng BM25 và Lượt có ghi cảnh báo. Cách chạy:
  - Tải `bge-m3-Q8_0.gguf` (634 MB, SHA-256 `c98c7c907bb3ab8c3be4c8ad827cc934c7c1a7e014d1c999e0c45c8027c158bb`) từ huggingface.co/lm-kit/bge-m3-gguf về `models/bge-m3/`. Đây là bản chuyển đổi của cộng đồng. Mạng công ty có lúc chặn CDN của Hugging Face; khi đó tải ở mạng khác.
  - Chạy một máy chủ thứ hai, để cửa sổ này mở song song với máy chủ Qwen:

    ```
    models\llama.cpp\cpu\llama-server.exe -m models\bge-m3\bge-m3-Q8_0.gguf --embedding --pooling cls --alias bge-m3 --host 127.0.0.1 --port 8081 -c 8192 -ub 8192
    ```

    Máy chủ này chiếm thêm khoảng 0,6 GB RAM. Nhúng toàn bộ TOSS (155 đoạn) mất khoảng 3 phút khi máy chủ Qwen đang chạy.

## 3c. So sánh các nguồn và danh sách gửi pháp chế (issue 15)

```
.venv\Scripts\python scripts\so_sanh_ba_nguon.py "Sample\HĐ TOSS v 12.5.2026.pdf"
```

- Lệnh này không gọi model: lấy Lượt đủ 17 Mục mới nhất của mỗi chế độ trong kho, so với nhau và với `eval/chuan/toss.yaml`. Kết quả ghi vào `eval/so-sanh/`.
- **Thêm `--chay`** để chạy trước chế độ nào chưa có Lượt đủ Mục (cần `llama-server`). Có Lượt dang dở thì chạy tiếp Lượt đó.
- **Chỉ rõ Lượt** bằng `--toan-van <mã>` và `--truy-xuat <mã>`, ví dụ khi một Lượt còn Mục chưa đánh giá được.
- **`bao-cao.md`:** tỷ lệ khớp theo Tiêu chí, Kết quả Mục và giá trị định lượng; từng Mục; Trích dẫn không xác minh được; ngữ cảnh chế độ truy xuất; các Tiêu chí không thống nhất.
- **Bộ chuẩn chưa điền xong:** chỉ so các Tiêu chí đã điền. File sai cú pháp hoặc sai giá trị thì báo lỗi kèm vị trí và chỉ so hai chế độ.
- **`danh-sach-phap-che.docx`:** chỉ tạo khi Bộ chuẩn đủ mọi Tiêu chí. Mỗi dòng là một Tiêu chí ba nguồn không thống nhất, kèm Trích dẫn của từng nguồn và một cột trống "Kết luận pháp chế".

## 4. Số đo trên máy hiện tại (Surface, Ryzen 5 6 nhân, 15,5 GB RAM, AMD Radeon tích hợp), 2026-10-29

| | Đọc prompt | Sinh câu trả lời |
|---|---|---|
| Bản CPU | 16,9 token/giây | 4,2 token/giây |
| Bản Vulkan (`-ngl 99`) | 22,9 token/giây | 3,2 token/giây |

- llama-server dùng khoảng 8,5 GB RAM (5,3 GB trọng số đọc từ file + bộ nhớ ngữ cảnh và bộ đệm); khi chạy, máy chỉ còn khoảng 0,6 GB trống. Nên đóng trình duyệt và ứng dụng nặng trước khi thẩm định.
- Phần đầu prompt được dùng lại giữa các lần gọi (kiến trúc lai của Qwen3.5 lưu trạng thái theo khối 512 token, nên mỗi lần gọi đọc lại tối đa khoảng 512 token của phần chung).
- Số đo thật với TOSS, 2026-10-30, trên máy chủ đang chạy:
  - Mục đầu tiên phải đọc toàn văn (khoảng 27,4k token, khoảng 5 token/giây), mất khoảng 1,5 giờ.
  - Mỗi Mục sau mất khoảng 10–25 phút. Phần lớn thời gian là sinh câu trả lời (khoảng 2 token/giây, mỗi Mục 400–2.800 token).
  - Ước tính một Lượt đủ 17 Mục: 5–6 giờ.
- Số đo cả Lượt TOSS, 2026-11-02 và 03: toàn văn 4 giờ 42 phút – 5 giờ 58 phút, truy xuất (có bge-m3) 7,5–8,3 giờ. Truy xuất lâu hơn toàn văn vì ngữ cảnh mỗi Mục mỗi khác, nên mọi Mục đều phải đọc lại từ đầu.
- Mỗi lần gọi giới hạn câu trả lời ở 4.096 token. Nếu model sinh lặp, lần gọi dừng sau khoảng 30 phút rồi được gọi lại. Lần chạy đầu chưa có giới hạn này: Mục 14 sinh khoảng 20,8k token đến khi hết ngữ cảnh, mất khoảng 3 giờ.
