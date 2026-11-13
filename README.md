# Thẩm định hợp đồng đầu ra

Công cụ hỗ trợ Người thẩm định rà Dự thảo Hợp đồng đầu ra theo Checklist thẩm định. Với mỗi Mục checklist, công cụ đưa ra Kết quả đề xuất (Đạt, Lưu ý hoặc Vi phạm) kèm Trích dẫn nguyên văn từ Hợp đồng. Người thẩm định duyệt từng Mục rồi xuất báo cáo Word.Toàn bộ dữ liệu Hợp đồng ở lại trên máy. 

Hệ thống gồm:

- Model ngôn ngữ Qwen3.5-9B, chạy bằng llama.cpp và chỉ nghe ở `127.0.0.1`.
- OCR chạy trên máy.
- Kho kết quả là một file SQLite.
---

## Mục lục

1. [Yêu cầu máy](#1-yêu-cầu-máy)
2. [Cài đặt](#2-cài-đặt)
3. [Chạy chương trình](#3-chạy-chương-trình)
4. [Quy trình thẩm định: giải thích từng bước](#4-quy-trình-thẩm-định-giải-thích-từng-bước)
5. [Dùng bằng dòng lệnh](#5-dùng-bằng-dòng-lệnh)
6. [Dữ liệu được lưu ở đâu](#6-dữ-liệu-được-lưu-ở-đâu)
7. [Kiểm thử](#7-kiểm-thử)
8. [Kiến trúc](#8-kiến-trúc)
9. [Cấu trúc thư mục](#9-cấu-trúc-thư-mục)
10. [Sự cố thường gặp](#10-sự-cố-thường-gặp)
11. [Tài liệu thêm](#11-tài-liệu-thêm)

---

## 1. Yêu cầu máy

| | Tối thiểu | Ghi chú |
|---|---|---|
| Hệ điều hành | Windows 10/11 64-bit | Các lệnh dưới đây viết cho Windows |
| CPU | 6 nhân | Không cần GPU. Số đo trong tài liệu lấy trên Ryzen 5 6 nhân |
| RAM | 16 GB | Máy chủ model dùng khoảng 8,5 GB. Nên đóng trình duyệt và ứng dụng nặng khi thẩm định |
| Ổ đĩa | khoảng 8 GB trống | Model Qwen 5,7 GB; bge-m3 0,6 GB; VietOCR 0,25 GB |
| Python | 3.12 trở lên | |

**Thời gian chạy một Lượt** (Hợp đồng khoảng 50 trang, 17 Mục):

| Chế độ | Thời gian |
|---|---|
| Toàn văn | khoảng 5–6 giờ (riêng Mục đầu khoảng 1,5 giờ) |
| Truy xuất | khoảng 7,5–8,5 giờ |

Lượt chạy nền, nên đóng trình duyệt thì Lượt vẫn chạy tiếp.

---

## 2. Cài đặt

Mọi lệnh chạy ở thư mục gốc của project.

### 2.1. Môi trường Python

```
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -e .[dev]
```

Nếu cần OCR, tức là có Dự thảo dạng bản scan hoặc lớp text lỗi, cài thêm nhóm `ocr`. Nhóm này gồm torch bản CPU, khoảng 110 MB:

```
.venv\Scripts\python -m pip install --timeout 180 --retries 10 -e .[dev,ocr]
```

### 2.2. File cấu hình `.env`

```
copy .env.example .env
```

Các biến cần chú ý:

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `THAMDINH_NGU_CANH` | `49152` | Độ dài ngữ cảnh. **Phải khớp tham số `-c` khi chạy máy chủ model** (mục 3.1) |
| `THAMDINH_LOCAL_URL` | `http://127.0.0.1:8080/v1` | Địa chỉ máy chủ Qwen |
| `THAMDINH_EMBEDDING_URL` | `http://127.0.0.1:8081/v1` | Địa chỉ máy chủ bge-m3 (chỉ dùng ở chế độ truy xuất) |
| `THAMDINH_DATA_DIR` | `data` | Thư mục lưu Văn bản hiệu lực, Lượt thẩm định, nhật ký |
| `THAMDINH_SUY_LUAN` | `false` | Bật chế độ suy luận của Qwen3.5. Chậm hơn nhiều trên CPU, không khuyến nghị |
| `THAMDINH_NGUOI_DUYET` | (trống) | Tên ghi vào Kết quả đã duyệt; để trống thì nhập trên trang Kết quả |

### 2.3. Model

Các file model không nằm trong repo (thư mục `models/` bị `.gitignore` bỏ qua). Tải về rồi đặt đúng vị trí:

| Thành phần | Bắt buộc? | Tải ở đâu | Đặt vào |
|---|---|---|---|
| llama.cpp bản Windows CPU (`llama-bXXXXX-bin-win-cpu-x64.zip`) | Có | github.com/ggml-org/llama.cpp/releases | giải nén vào `models\llama.cpp\cpu\` |
| `Qwen3.5-9B-Q4_K_M.gguf` (5,68 GB) | Có | huggingface.co/unsloth/Qwen3.5-9B-GGUF | `models\qwen\` |
| `bge-m3-Q8_0.gguf` (634 MB) | Chỉ cho chế độ truy xuất | huggingface.co/lm-kit/bge-m3-gguf | `models\bge-m3\` |
| VietOCR `vgg_transformer.pth` cùng các file `.yml` | Chỉ khi cần OCR | xem [docs/cai-ocr.md](docs/cai-ocr.md) | `models\vietocr\` |

Mã SHA-256 để kiểm file sau khi tải nằm trong [docs/chay-model-local.md](docs/chay-model-local.md) và [docs/cai-ocr.md](docs/cai-ocr.md). Mạng công ty có thể chặn CDN của Hugging Face; khi đó tải ở mạng khác rồi chép vào.

### 2.4. Kiểm tra cài đặt

```
.venv\Scripts\python -m pytest
```

Lệnh này chạy các test thường, không cần model, mất khoảng 2–3 phút, và phải xanh hết. Kiểm tra với model thật ở [mục 7](#7-kiểm-thử).

---

## 3. Chạy chương trình

Cần **hai hoặc ba cửa sổ lệnh** mở song song.

### 3.1. Cửa sổ 1: máy chủ model Qwen (bắt buộc)

```
models\llama.cpp\cpu\llama-server.exe -m models\qwen\Qwen3.5-9B-Q4_K_M.gguf --alias qwen3.5 --host 127.0.0.1 --port 8080 -c 49152 -fa on -ctk q8_0 -ctv q8_0 --jinja -np 1
```

Chờ đến khi cửa sổ in dòng `listening on`. Để cửa sổ này mở suốt quá trình thẩm định. Ý nghĩa các tham số:

| Tham số | Ý nghĩa |
|---|---|
| `--host 127.0.0.1` | Chỉ nghe trên máy này |
| `-c 49152` | Độ dài ngữ cảnh, phải khớp `THAMDINH_NGU_CANH` |
| `-fa on -ctk q8_0 -ctv q8_0` | Nén bộ nhớ ngữ cảnh để tiết kiệm RAM |
| `--jinja` | Bắt buộc, để hệ thống tắt được chế độ suy luận |
| `-np 1` | Một luồng xử lý, để phần đầu prompt (toàn văn Hợp đồng) được dùng lại giữa các Mục. Vì vậy mỗi lúc chỉ chạy được một Lượt |

### 3.2. Cửa sổ 2: máy chủ embedding bge-m3 (tùy chọn, chỉ cho chế độ truy xuất)

```
models\llama.cpp\cpu\llama-server.exe -m models\bge-m3\bge-m3-Q8_0.gguf --embedding --pooling cls --alias bge-m3 --host 127.0.0.1 --port 8081 -c 8192 -ub 8192
```

Không chạy máy chủ này thì chế độ truy xuất vẫn chạy, nhưng chỉ dùng tìm kiếm từ khóa (BM25), và Lượt có ghi cảnh báo.

### 3.3. Cửa sổ 3: giao diện

```
.venv\Scripts\python -m streamlit run app.py
```

Trình duyệt mở `http://localhost:8501`, với ba trang theo thứ tự công việc: **Số hóa → Thẩm định → Kết quả**. Có thể mở giao diện trước, rồi bật máy chủ model khi bắt đầu thẩm định.

---

## 4. Quy trình thẩm định: giải thích từng bước

```
Dự thảo (PDF)
   │  Bước 1: Số hóa (không dùng model ngôn ngữ)
   ▼
Văn bản hiệu lực: các Điều khoản có số hiệu, số trang, nhãn sửa đổi
   │  Bước 2: Thẩm định (Qwen3.5, mỗi Mục checklist một lần gọi)
   ▼
Lượt thẩm định: Kết quả đề xuất cho 17 Mục, Đánh giá từng Tiêu chí, Trích dẫn đã kiểm
   │  Bước 3: Duyệt (Người thẩm định)
   ▼
Kết quả đã duyệt và báo cáo .docx
```

### Bước 1: Số hóa (trang Số hóa)

Mục đích: biến file PDF Dự thảo thành Văn bản hiệu lực, tức là văn bản dùng để thẩm định, chia thành các Điều khoản có số hiệu.

1. Tải PDF lên và bấm Số hóa.
2. Đọc từng trang: Với mỗi trang, hệ thống thử đọc lớp text của PDF trước, vì cách này nhanh và chính xác. Nếu lớp text kém (bản scan, lỗi bảng mã), trang được OCR trên máy bằng RapidOCR để tìm dòng chữ và VietOCR để nhận dạng tiếng Việt. Trước khi OCR, ảnh trang được chỉnh nghiêng, cắt bỏ khung bình luận bên lề và khử nền màu.
3. Giữ lại thay đổi theo dõi (redline) dưới dạng nhãn: `[xóa: …]`, `[thêm: …]`, `[sửa: …]`. Khung bình luận bên lề bị loại bỏ. Model thẩm định được dặn bỏ qua chữ trong `[xóa: …]` và coi chữ trong `[thêm: …]` và `[sửa: …]` là có hiệu lực.
4. Dựng cấu trúc: nhận ra Điều, Khoản, Phụ lục và phần mở đầu, kèm số hiệu, trang bắt đầu và kết thúc, và tọa độ trên trang (để sau này tô vị trí Trích dẫn).
5. Kiểm tra bằng mắt: Trang hiện song song ảnh trang và các Điều khoản đọc được. Tick Chỉ trang tin cậy thấp để chỉ xem những trang OCR có redline, có khung bình luận hoặc độ tin cậy dưới 85%. Điều khoản đọc sai thì sửa tay và bấm Lưu.

Văn bản hiệu lực được lưu theo mã hash của file PDF, nên mỗi file chỉ phải số hóa một lần. Mỗi lần sửa tay tạo một bản mới; Lượt đã chạy trước đó vẫn mở lại được đúng văn bản lúc chạy.

### Bước 2: Thẩm định (trang Thẩm định)

Mục đích: đối chiếu Văn bản hiệu lực với từng Mục checklist để tạo Kết quả đề xuất.

Cách khởi chạy:

1. Chọn Văn bản hiệu lực, Phiên bản checklist (hiện có `dau-ra-v1.1`) và chế độ:
   - Toàn văn: mỗi Mục đọc cả Hợp đồng. Nhanh hơn nhờ dùng lại phần đầu prompt.
   - Truy xuất: mỗi Mục chỉ đọc các Điều khoản liên quan. Dùng khi Hợp đồng quá dài so với ngữ cảnh của model.
2. Bấm Chạy Thẩm định. Giao diện kiểm máy chủ model trước; nếu máy chủ chưa chạy thì hiện lệnh khởi động. Lượt chạy ở tiến trình nền; trang tự làm mới 10 giây một lần, hiện số Mục đã xong và nhật ký.

Bên trong một Lượt:

1. Xác định các bên. Model đọc phần mở đầu Hợp đồng để biết bên nào là "Công ty" và bên nào là "Khách hàng", bất kể văn bản gọi là Bên A hay Bên B.
2. Chọn ngữ cảnh cho từng Mục:
   - Chế độ toàn văn dùng cả Hợp đồng. Nếu Hợp đồng quá dài so với `THAMDINH_NGU_CANH`, hệ thống báo lỗi ngay, trước khi gọi model.
   - Chế độ truy xuất: lần đầu với mỗi Hợp đồng, hệ thống gắn "Chủ đề" cho từng Điều khoản (khoảng 40 phút, sau đó dùng lại). Mỗi Mục lấy các Điều khoản mang Chủ đề của Mục, cộng 5 Điều khoản khớp nhất theo từ khóa (BM25) và 5 theo nghĩa (bge-m3), trong ngân sách `THAMDINH_NGAN_SACH_TRUY_XUAT` token.
3. Gọi model một lần cho mỗi Mục. Prompt gồm hướng dẫn chung, Hợp đồng, các Tiêu chí của Mục và quy ước đánh giá. Câu trả lời bị máy chủ ép theo một JSON schema: với mỗi Tiêu chí, model ghi `danh_gia` (thỏa / không thỏa / không rõ), lý do, tối đa 3 Trích dẫn, và giá trị số khi Tiêu chí cần. Hệ thống tự xử lý hai trường hợp lỗi:
   - JSON sai: gọi lại một lần, kèm thông báo lỗi.
   - Câu trả lời bị cắt vì quá dài: chia đôi danh sách Tiêu chí rồi gọi lại.

   Nếu vẫn không được, Mục ghi "chưa đánh giá được" và các Mục khác chạy tiếp.
4. Code quyết phần còn lại, không để model quyết:
   - Tiêu chí định lượng (ví dụ mức phạt so với 8%): model chỉ trích con số; code so với ngưỡng trong checklist.
   - Kiểm Trích dẫn: mỗi câu trích được tìm lại trong Văn bản hiệu lực. Việc so khớp bỏ qua khác biệt Unicode, kiểu ngoặc kép, dấu cách và nhãn redline. Kết quả là một trong ba trạng thái: *khớp*, *khớp nhưng sai số hiệu* (kèm số hiệu đúng) hoặc *không xác minh được*.
   - Tổng hợp Kết quả Mục theo quy tắc mức xấu nhất thắng:
     - Có Tiêu chí Vi phạm nào thỏa thì Mục là "Vi phạm".
     - Nếu không, khi có Tiêu chí Lưu ý thỏa, hoặc thiếu Tiêu chí Đạt, hoặc chưa loại trừ được một Tiêu chí, thì Mục là "Lưu ý".
     - Chỉ khi đủ mọi Tiêu chí Đạt thì Mục mới là "Đạt".
5. Lưu ngay sau mỗi Mục vào `data/tham-dinh.sqlite3`. Tắt máy giữa chừng không mất các Mục đã xong.

Dừng và chạy lại:

- Dừng: nút "Dừng" giữ lại các Mục đã xong.
- Chạy lại phần lỗi: chỉ chạy các Mục lỗi hoặc chưa chạy, trên cùng Lượt.
- Chạy lại cả Mục đã có kết quả: chọn thêm các Mục đó. Hệ thống tạo Lượt mới có ghi Lượt gốc; Lượt cũ và các Kết quả đã duyệt của nó giữ nguyên.

### Bước 3: Duyệt và báo cáo (trang "Kết quả")

1. Chọn Lượt thẩm định. Trang hiện bảng 17 Mục, tô màu theo Kết quả.
2. Xem chi tiết từng Mục: Đánh giá từng Tiêu chí kèm lý do của model, Trích dẫn kèm trạng thái xác minh, các Điều khoản model đã đọc, và cảnh báo nếu có.
3. Xem trang: nút này mở ảnh trang PDF và tô vùng Điều khoản chứa câu trích, để đối chiếu với bản gốc.
4. Duyệt: giữ hoặc sửa Kết quả, ghi giải thích, sửa Trích dẫn. Mỗi lần lưu tạo một phiên bản mới trong "Lịch sử duyệt". Kết quả đề xuất ban đầu không bao giờ bị ghi đè.
5. Tải báo cáo (.docx): báo cáo theo bố cục checklist.
   - Mục đã duyệt ghi Kết quả đã duyệt; Mục chưa duyệt ghi Kết quả đề xuất kèm "(đề xuất, chưa duyệt)".
   - Phụ lục liệt kê các Mục mà Người thẩm định đã đổi mức Kết quả.
   - Số hợp đồng được dò sẵn và sửa được trước khi tải.

> Kết quả đề xuất chỉ là bản nháp. Người thẩm định chịu trách nhiệm về Kết quả đã duyệt.

---

## 5. Dùng bằng dòng lệnh

Mọi việc trên giao diện đều làm được bằng script trong `scripts/`. Thay `<hop-dong.pdf>` bằng đường dẫn file Dự thảo.

| Việc | Lệnh |
|---|---|
| Chạy một Lượt | `.venv\Scripts\python scripts\chay_tham_dinh.py <hop-dong.pdf> [--che-do toan_van\|truy_xuat]` |
| Xem danh sách Lượt và mã Lượt | `.venv\Scripts\python scripts\chay_tham_dinh.py --danh-sach` |
| Chạy tiếp Mục lỗi hoặc chưa chạy | `... chay_tham_dinh.py <hop-dong.pdf> --tiep-tuc <mã Lượt>` |
| Chạy lại vài Mục đã có kết quả (tạo Lượt mới) | `... chay_tham_dinh.py <hop-dong.pdf> --tiep-tuc <mã Lượt> --chi-muc 3,14` |

Đo chất lượng bằng Bộ chuẩn. Bộ chuẩn là kết quả thẩm định do Người thẩm định điền tay cho một Hợp đồng, được coi là đúng.

| Việc | Lệnh |
|---|---|
| Tạo file mẫu Bộ chuẩn để điền tay | `scripts\tao_mau_bo_chuan.py <checklist.yaml> <hop-dong.pdf> <file_ra.yaml>` |
| Kiểm Bộ chuẩn đã điền đủ và đúng chưa | `scripts\kiem_tra_bo_chuan.py <bo_chuan.yaml> [checklist.yaml] [hop-dong.pdf]` |
| So hai chế độ với Bộ chuẩn, tạo danh sách gửi pháp chế | `scripts\so_sanh_ba_nguon.py <hop-dong.pdf>` |
| So hai lần chạy (trước và sau một thay đổi) | `scripts\so_sanh_lan_chay.py <hop-dong.pdf> --truoc <mã> --sau <mã> --muc 3,4` |
| Chấm lại mọi Lượt đã lưu bằng code hiện tại, không gọi model | `scripts\cham_lai_kho.py [--so-voi <commit>]` |
---

## 6. Dữ liệu được lưu ở đâu

Tất cả nằm trong `data/` (đổi được bằng `THAMDINH_DATA_DIR`). Thư mục này không được đưa vào git.

| Đường dẫn | Nội dung |
|---|---|
| `data/van-ban-hieu-luc/` | Văn bản hiệu lực theo hash PDF, kèm các bản đã sửa tay |
| `data/tham-dinh.sqlite3` | Lượt thẩm định, Kết quả đề xuất và Kết quả đã duyệt. Kết quả đề xuất không sửa hay xóa được |
| `data/chu-de/` | Chủ đề đã gắn cho Điều khoản (chế độ truy xuất), dùng lại giữa các lần chạy |
| `data/nhat-ky/` | Nhật ký từng Lượt |
| `data/dang-chay.json` | Trạng thái Lượt đang chạy nền |

`eval/` (Bộ chuẩn, báo cáo so sánh) và `sample/` (file Hợp đồng mẫu) cũng chứa dữ liệu Hợp đồng và không được đưa vào git. Hãy tự sao lưu các thư mục này.

---

## 7. Kiểm thử

```
.venv\Scripts\python -m pytest            # test thường, không cần model (mặc định)
.venv\Scripts\python -m pytest -m llm     # cần máy chủ Qwen đang chạy (mục 3.1)
.venv\Scripts\python -m pytest -m ocr     # cần model VietOCR, khoảng 3–4 phút
```

Chạy lại `pytest -m llm` mỗi khi cài hoặc đổi file model Qwen.

---

## 8. Kiến trúc

### 8.1. Các tiến trình khi chạy

```
Trình duyệt ──HTTP──▶ Streamlit (app.py, ui/)
                        │  trang Số hóa: gọi so_hoa() ngay trong tiến trình này
                        │  trang Kết quả: đọc kho, duyệt, xuất .docx
                        │
                        │  trang Thẩm định: chay_nen.khoi_chay()
                        ▼
                  Tiến trình nền: scripts/chay_tham_dinh.py → chay_luot()
                        │  trạng thái: data/dang-chay.json; nhật ký: data/nhat-ky/
                        │  in "Mã Lượt: …" để giao diện theo dõi tiến độ trong kho
                        │
                        ├──HTTP 127.0.0.1:8080──▶ llama-server Qwen3.5  (/v1/chat/completions, /tokenize, /health)
                        ├──HTTP 127.0.0.1:8081──▶ llama-server bge-m3   (/v1/embeddings, chỉ chế độ truy xuất)
                        └──▶ data/: tham-dinh.sqlite3, van-ban-hieu-luc/, chu-de/
```

- Lượt chạy ở tiến trình riêng, nên đóng trình duyệt hay tắt Streamlit thì Lượt vẫn chạy tiếp. Mỗi lúc chỉ chạy một Lượt, vì máy chủ Qwen chạy `-np 1`.
- Mọi kết nối đều tới `127.0.0.1`. Không có dịch vụ nào ra ngoài máy.

### 8.2. Phụ thuộc giữa các module

Mũi tên nghĩa là "gọi" hoặc "dùng". `checklist.py` (Phiên bản checklist) và `settings.py` (cấu hình `.env`) được nhiều module dùng nên không vẽ.

```
ui/so_hoa.py ─────────────▶ so_hoa/  (lop_text, ocr + anh, cau_truc, van_ban)
ui/tham_dinh.py ──────────▶ chay_nen ──(tiến trình nền)──▶ chay_luot
ui/ket_qua.py ────────────▶ kho_luot, bang_ket_qua, bao_cao, anh_trang, trich_dan

chay_luot ─┬─▶ so_hoa/          Văn bản hiệu lực (dùng lại bản đã lưu theo hash PDF)
           ├─▶ truy_xuat         chỉ chế độ truy xuất: gắn Chủ đề (gọi llm), BM25, bge-m3
           ├─▶ tham_dinh ─┬─▶ llm               gọi Qwen, ép JSON schema
           │              └─▶ ket_qua_de_xuat ─┬─▶ trich_dan   kiểm Trích dẫn
           │                                   └─▶ tong_hop    Đánh giá tiêu chí → Kết quả Mục
           └─▶ kho_luot          lưu sau mỗi Mục

Đo chất lượng (scripts/):  bo_chuan, so_sanh, cham_lai (gọi lại ket_qua_de_xuat), phap_che
```

Ba chỗ nối có thể thay bằng bản giả trong test: `LLMClient` (model), `BoNhung` (embedding) và `BoOCR` (OCR). Nên gần như toàn bộ test chạy được khi không có model.

### 8.3. Dữ liệu đi qua các bước

| Kiểu | Module | Nội dung |
|---|---|---|
| `PhienBanChecklist`, `MucChecklist`, `TieuChi` | `checklist.py` | Checklist đọc từ YAML: Mục, Tiêu chí Đạt/Lưu ý/Vi phạm, ngưỡng định lượng, Danh mục tham chiếu |
| `VanBanHieuLuc`, `DieuKhoan` | `so_hoa/` | Kết quả Số hóa: các trang và Điều khoản có số hiệu, trang, tọa độ, nhãn redline |
| `CacBen` | `luot.py` | Bên nào là Công ty, bên nào là Khách hàng |
| `KetQuaMucDeXuat`, `DanhGiaDeXuat`, `TrichDanDaKiemTra` | `ket_qua_de_xuat.py`, `trich_dan.py` | Kết quả đề xuất của một Mục: Đánh giá từng Tiêu chí, lý do, Trích dẫn đã kiểm |
| `KetQuaLuot` | `luot.py` | Một Lượt: chế độ, model, các bên, 17 Kết quả Mục đề xuất, Lượt gốc, hash Văn bản hiệu lực đã dùng |
| `KetQuaDuyet` | `kho_luot.py` | Một phiên bản duyệt của một Mục: Kết quả, giải thích, Trích dẫn, người duyệt, thời điểm |

Kho SQLite có ba bảng: `luot`, `muc_de_xuat` và `duyet`.

### 8.4. Các nguyên tắc thiết kế

- Dữ liệu Hợp đồng chỉ ở trên máy: model, OCR và embedding đều chạy trên máy; `data/`, `eval/`, `sample/`, `models/` không vào git.
- Truy xuất theo cấu trúc Hợp đồng: Hợp đồng được chia theo Điều/Khoản/Phụ lục, mỗi Mục lấy các Điều khoản mang Chủ đề của Mục; BM25 và embedding chỉ là lưới an toàn. Cách này giúp kiểm được cả các Tiêu chí về việc thiếu một điều khoản, điều mà tìm theo độ tương đồng không chứng minh được.
- Model đọc và trích, code quyết định: model chỉ trả Đánh giá từng Tiêu chí, lý do, Trích dẫn và con số. So con số với ngưỡng, kiểm Trích dẫn và tổng hợp Kết quả Mục đều do code làm, nên có test và chấm lại được các Lượt đã lưu (`cham_lai.py`) mà không gọi model.
- Kết quả đề xuất không bị ghi đè: chạy lại Mục đã có kết quả thì tạo Lượt mới; mỗi lần duyệt tạo một phiên bản `KetQuaDuyet` mới.

---

## 9. Cấu trúc thư mục

```
app.py                  Điểm vào giao diện Streamlit (3 trang)
ui/                     so_hoa.py, tham_dinh.py, ket_qua.py: ba trang giao diện
src/thamdinh/
  so_hoa/               Bước 1: lớp text, OCR, xử lý ảnh, dựng cấu trúc Điều khoản
  tham_dinh.py          Bước 2: dựng prompt, gọi model từng Mục, xử lý lỗi và chia đôi
  truy_xuat.py          Chế độ truy xuất: gắn Chủ đề, BM25, embedding
  ket_qua_de_xuat.py    Từ câu trả lời model ra Kết quả đề xuất của Mục
  tong_hop.py           Tổng hợp Kết quả Mục từ Đánh giá tiêu chí
  trich_dan.py          Kiểm Trích dẫn có thật trong Văn bản hiệu lực
  luot.py, kho_luot.py  Lượt thẩm định và kho SQLite
  chay_luot.py, chay_nen.py   Chạy một Lượt, chạy nền cho giao diện
  bao_cao.py            Báo cáo .docx
  bo_chuan.py, so_sanh.py, cham_lai.py, phap_che.py   Đo chất lượng theo Bộ chuẩn
  llm.py                Gọi máy chủ model trên máy
  settings.py           Đọc cấu hình từ .env
checklists/             Phiên bản checklist (YAML) và Danh mục tham chiếu
scripts/                Script dòng lệnh (mục 5)
tests/                  Test (pytest)
docs/                   Tài liệu cài đặt, quy trình
models/, data/, eval/, sample/   Không có trong git (model, dữ liệu Hợp đồng)
```

---

## 10. Sự cố thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| Trang Thẩm định báo "Chưa chạy máy chủ model" | Bật máy chủ ở mục 3.1 và chờ dòng `listening on`. Lúc mới bật, model cần vài phút để nạp |
| Báo Hợp đồng quá dài so với ngữ cảnh | Dùng chế độ truy xuất, hoặc tăng `-c` và `THAMDINH_NGU_CANH` cùng lúc (tốn thêm RAM) |
| Máy rất chậm hoặc treo khi thẩm định | Thiếu RAM: đóng trình duyệt và ứng dụng nặng; chỉ chạy bge-m3 khi dùng chế độ truy xuất |
| Một Mục "chưa đánh giá được" | Bấm **Chạy lại phần lỗi** trên trang Thẩm định |
| Không mở được một Lượt ("trường lạ…") | Lượt được lưu bằng một phiên bản code khác. Thông báo nêu rõ trường nào |
| Chế độ toàn văn chậm bất thường (mỗi Mục hơn 1 giờ) | Phần riêng của prompt Mục 1 quá dài nên model không dùng lại được phần đầu. Test `test_duoi_prompt_muc_1_du_ngan_de_dung_lai_cache` kiểm điều này |
| Lỗi in tiếng Việt trong cửa sổ lệnh | Đặt `set PYTHONIOENCODING=utf-8` trước khi chạy script |

---

## 11. Tài liệu thêm

- [GLOSSARY.md](GLOSSARY.md): thuật ngữ nghiệp vụ.
- [docs/chay-model-local.md](docs/chay-model-local.md): chạy model, số đo tốc độ và RAM.
- [docs/cai-ocr.md](docs/cai-ocr.md): cài và đo OCR, giới hạn đã biết.
- [docs/adr/](docs/adr/): các quyết định kiến trúc (dữ liệu chỉ ở trên máy, truy xuất theo cấu trúc).
- [docs/agents/thu-nghiem-model.md](docs/agents/thu-nghiem-model.md): quy trình thử nghiệm với model.
- [checklists/dau-ra-v1.1-khac-biet.md](checklists/dau-ra-v1.1-khac-biet.md): khác biệt của Checklist V1.1 so với V1.
