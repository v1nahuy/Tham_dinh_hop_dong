# Cài OCR (trang có lớp text kém)

Trang PDF có lớp text tốt (như TOSS) không cần OCR. Trang lớp text kém (bản scan, lỗi bảng mã) được OCR trên máy, không gửi dữ liệu ra ngoài (ADR 0001):

- **Phát hiện dòng chữ:** RapidOCR (PP-OCRv4 chạy bằng ONNX Runtime). Model có sẵn trong gói PyPI.
- **Nhận dạng tiếng Việt:** VietOCR. Model nằm trong `models/vietocr/`.
- **Đọc lại số hiệu khoản ở đầu dòng:** phần nhận dạng của RapidOCR. VietOCR hay mất hoặc thừa dấu chấm, ví dụ "1.1." đọc thành "11".

## 1. Cài gói

```
.venv\Scripts\python -m pip install --timeout 180 --retries 10 -e .[dev,ocr]
```

- torch bản CPU cài thẳng từ PyPI, vì mạng công ty chặn download.pytorch.org. Gói nặng khoảng 110 MB nên cần `--timeout`.
- VietOCR 0.3.12 cần `setuptools<81`, vì gói gdown của nó dùng `pkg_resources`.
- `pip check` báo `rapidocr-onnxruntime` yêu cầu numpy < 2. Cảnh báo này bỏ qua được: gói đã chạy thử và chạy đúng với numpy 2.5.4.

## 2. File model VietOCR

Mạng công ty chặn vocr.vn, nên phải tải ở mạng ngoài rồi chép cả thư mục `models/vietocr/` sang.

| File | Nguồn | SHA-256 |
|---|---|---|
| `vgg_transformer.pth` (152 MB, mặc định) | vocr.vn/data/vietocr/vgg_transformer.pth | `380512193a8b6cbf6fad80deacdc9b6939d10d473d199892fc6408d13775ea59` |
| `vgg_seq2seq.pth` (89 MB, nhanh hơn, kém chính xác hơn) | Google Drive id `1nTKlEog9YFK74kPyX0qLwCWi60_YHHk4` | `0921503a41375a0584268e23ef3d414ea478a8fe8777865c7745d38f2d0bc5db` |
| `base.yml`, `vgg-transformer.yml`, `vgg-seq2seq.yml` | raw.githubusercontent.com/pbcquoc/vietocr (thư mục `config/`) | |

Cấu hình trong `.env`:

```
THAMDINH_OCR_MODEL=vgg_transformer   # hoặc vgg_seq2seq
THAMDINH_OCR_MODEL_DIR=models/vietocr
```

## 3. Cách OCR một trang

1. Render trang ở 300 dpi.
2. Chỉnh nghiêng trong khoảng ±5°. Bước này làm trước bước cắt khung, vì bản scan nghiêng thì dải xám cũng nghiêng.
3. Cắt dải nền xám bên phải, tức khung comment. Cách nhận dải xám:
   - So độ sáng của từng cột với nền giấy, không dùng ngưỡng cố định, nên vẫn chạy với bản scan có nhiễu và nén JPEG.
   - Phần bảng tràn sang vùng nền xám được giữ lại.
4. Tô trắng nền màu nhạt, như highlight vàng.
5. Phát hiện hộp chữ ở 150 dpi, có lọc trung vị để khử nhiễu.
6. Ghép các hộp cùng dòng.
7. Với mỗi hộp, dò redline trên ảnh rồi cắt thành các đoạn có cùng nhãn, sau đó nhận dạng từng đoạn. Cách gắn nhãn:
   - Chữ màu, gồm cả chữ xám, có gạch ngang: `[xóa: …]`.
   - Chữ màu có gạch chân: `[thêm: …]`.
   - Chữ màu không có gạch: `[sửa: …]`.
   - Bản đen trắng có gạch ngang: `[xóa: …]`.
8. Ra danh sách dòng kèm tọa độ trên trang, đưa vào bộ dựng cấu trúc dùng chung với lớp text.

Trang OCR bị đánh dấu tin cậy thấp khi có redline, có khung comment, hoặc độ tin cậy nhận dạng trung bình dưới 85%. Với TOSS, độ tin cậy là 91–93%.

Kết quả số hóa được lưu theo hash PDF trong `data/van-ban-hieu-luc/`, nên mỗi file PDF chỉ OCR một lần.

## 4. Kiểm tra

```
.venv\Scripts\python -m pytest -m ocr
.venv\Scripts\python scripts\do_cer_ocr.py "Sample\HĐ TOSS v 12.5.2026.pdf" --trang 2,3,8
```

- **`pytest -m ocr`** ép trang 2–4 của TOSS đi đường OCR rồi so với lớp text. Yêu cầu CER dưới 5% mỗi trang, không lẫn comment, có nhãn `[xóa:` ở khoản 4.3.2, và cấu trúc Điều 1–15 vẫn đủ. Mất khoảng 3–4 phút.
- **`do_cer_ocr.py`** đo CER, số hiệu khoản đọc đúng và số đoạn redline cho từng trang. Bỏ `--trang` để đo cả file.

## 5. Số đo (TOSS, CPU Ryzen 5 6 nhân, 2026-10-30)

| | CER trang 2 / 3 / 4 | Cả 52 trang |
|---|---|---|
| `vgg_transformer` | 1,4 / 1,5 / 1,4% | CER trung bình 4,8%; tỉ lệ từ có mặt 97,8%; khoảng 32 phút |

- Trang bảng có CER cao (24–61%) chủ yếu vì OCR đọc các ô theo thứ tự khác lớp text. Tỉ lệ từ có mặt, không xét thứ tự, ở các trang này vẫn từ 94% trở lên.
- Ép OCR cả TOSS vẫn ra đủ Điều 1–15 và Phụ lục 01–05, không lẫn chữ của khung comment. Còn thiếu 6/148 số hiệu, trong đó có 8.2.1 và 8.3.1–8.3.3.

## 6. Giới hạn đã biết

- VietOCR không có ký tự ngoặc kép cong “ ”, nên đọc thành `?` hoặc bỏ mất.
- **Redline chỉ một ký tự** (ví dụ "0[thêm: 3][xóa: 2]%") thường không nhận ra được nét gạch, vì nét quá ngắn. Đoạn đó ra nhãn `[sửa: …]` gộp chung.
- **Chữ xám được coi là redline** (giống lớp text). Bản scan có chữ đen bị nhạt, với lõi nét chữ sáng hơn khoảng 50/255, có thể bị gắn nhầm `[sửa: …]`. Cần kiểm lại với bản scan giả lập ở issue 14.
- **Bản scan đen trắng (fax) mất nền xám của khung comment**, nên không cắt được khung, và chữ trong comment lẫn vào văn bản. Bản scan xám có nhiễu rất mạnh cũng có lúc không cắt được. Số liệu đo nằm ở `eval/bien-the/bao-cao.md` (issue 14).
- **Gạch chân màu đen** coi là định dạng thường, không gắn nhãn. Vì vậy chữ thêm vào trên bản scan đen trắng sẽ không có nhãn.
