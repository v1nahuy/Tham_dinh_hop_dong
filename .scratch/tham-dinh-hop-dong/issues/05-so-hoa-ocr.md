# 05 - Số hóa: OCR, cắt khung comment, phát hiện redline

Status: done
Blocked by: 04

## Việc cần làm

- Render trang ~300 dpi (pypdfium2).
- Phát hiện và cắt khung comment (dải nền xám bên phải trang).
- Chỉnh nghiêng, khử nhiễu.
- OCR tiếng Việt: RapidOCR (PP-OCRv4) phát hiện dòng, VietOCR nhận dạng (Q38, thay PaddleOCR) → dòng kèm tọa độ và độ tin cậy. Đưa kết quả vào bộ dựng cấu trúc của issue 04.
- Phát hiện redline trên ảnh: chữ màu, nét ngang giữa thân chữ (gạch xóa) hoặc sát chân chữ (gạch chân). **Không gỡ redline**; gắn nhãn `[xóa: …]` / `[thêm: …]` / `[sửa: …]` cùng định dạng với lớp text (issue 04, `lop_text.py`). Bản scan đen trắng chỉ còn nét gạch làm tín hiệu. Đánh dấu trang tin cậy thấp kèm lý do; trang có độ tin cậy OCR trung bình thấp cũng bị đánh dấu.
- Thay `CanOCRError` trong `so_hoa()` bằng đường OCR cho các trang lớp text kém.

## Tiêu chí hoàn thành

- TOSS là PDF có lớp text tốt, nên kiểm thử OCR bằng cách ép đi đường OCR và bằng bản scan giả lập ở issue 14: ra được Điều 1–15 và các Phụ lục, không lẫn nội dung comment.
- Các trang có redline của TOSS (ví dụ trang 3, 4, 5) bị đánh dấu tin cậy thấp; nhãn `[xóa: …]` xuất hiện ở khoản 4.3.2.

## Comments

**2026-10-29, tạm dừng.** Người dùng sẽ cài lại PaddleOCR + VietOCR ở mạng ngoài công ty rồi tiếp tục. Chưa viết code chính thức hay test nào cho issue này; chỉ có script chạy thử trong `.scratch/tham-dinh-hop-dong/spike-ocr/` (chạy từ thư mục gốc repo: `.venv/Scripts/python .scratch/tham-dinh-hop-dong/spike-ocr/thu_ocr2.py 2 3 8`).

### Kết quả chạy thử (RapidOCR phát hiện + VietOCR `vgg_seq2seq` nhận dạng, CPU)

| Trang TOSS | CER so với lớp text | Thời gian |
|---|---|---|
| 2 (văn bản) | 4,7% | 17 s |
| 3 (có redline) | 4,5% | 14 s |
| 8 (có bảng) | 9,0% | 12 s |

- Ước tính cả 52 trang khoảng 13 phút. Phát hiện ở 150 dpi (3 s/trang thay vì 10–14 s ở 300 dpi), nhận dạng trên ảnh 300 dpi.
- Lỗi chính: số hiệu khoản mất dấu chấm ("1.1." → "11", "1.2.2." → "122."); dấu ngoặc kép cong “ ” thành `?` (không có trong vocab VietOCR); đôi khi mất dấu `:`.
- Cần ghép các vùng chữ cùng dòng (số hiệu khoản bị tách thành vùng riêng).
- Spike cắt khung comment thô bằng ngưỡng 68% bề ngang; bản chính thức cần dò dải xám trên ảnh.

### Lỗi môi trường đã gặp

1. **PaddleOCR không tải được model**: `Exception: No available model hosting platforms detected`. Mạng công ty chặn huggingface.co, paddle-model-ecology.bj.bcebos.com, modelscope.cn, aistudio.baidu.com (curl trả 000). Chỉ vào được github.com, raw.githubusercontent.com, pypi.org, drive.google.com.
2. **VietOCR**: vocr.vn bị chặn, cả weights lẫn file cấu hình. Đã lấy `base.yml`, `vgg-seq2seq.yml` từ raw.githubusercontent.com/pbcquoc/vietocr; weights `vgg_seq2seq` từ Google Drive id `1nTKlEog9YFK74kPyX0qLwCWi60_YHHk4` (89 MB). Id `vgg_transformer` cũ (`13327Y1tz1ohsm5YZMyXVMPIOjoOA0OaA`) trả về trang HTML, chưa tải được. Tất cả trong `models/vietocr/` (đã thêm `models/` vào `.gitignore`).
3. **download.pytorch.org bị chặn** → cài torch 2.15.0+cpu từ PyPI, cần `--timeout 180 --retries 10` vì tải 110 MB bị read timeout.
4. **gdown (VietOCR phụ thuộc) cần `pkg_resources`**, setuptools 84 đã bỏ → hạ `setuptools<81`.
5. **VietOCR 0.3.12 dùng `Image.ANTIALIAS`**, Pillow 13 đã bỏ → vá `Image.ANTIALIAS = Image.LANCZOS` trước khi gọi VietOCR.
6. **Xung đột phiên bản**: `rapidocr_onnxruntime==1.3.24` hạ numpy xuống 1.26.4; đang có cả `opencv-python` và `opencv-contrib-python` (khác phiên bản). Nên dọn khi cài lại.
7. Máy không có GPU NVIDIA (AMD Radeon tích hợp), Ryzen 5 6 nhân, 15,5 GB RAM, còn khoảng 11 GB ổ C.

### Gợi ý khi cài ở nhà

- PaddleOCR 3.x tải model vào `~/.paddlex/official_models/` (ví dụ `PP-OCRv5_server_det`, `PP-OCRv5_mobile_det`). Chép thư mục đó về máy công ty để chạy offline.
- Tải thêm VietOCR `vgg_transformer.pth` từ vocr.vn (chính xác hơn `vgg_seq2seq`, chậm hơn) cùng các file `.yml`, để so CER.
- Nên so CER trên trang 2, 3, 8 giữa PaddleOCR (PP-OCRv5) và RapidOCR (PP-OCRv4) cho bước phát hiện, giữ nguyên VietOCR.

### Câu hỏi đang chờ người dùng trả lời

- **Q38 - Công cụ OCR**: dùng RapidOCR (PP-OCRv4, ONNX Runtime, model có sẵn trong gói PyPI) thay PaddleOCR + paddlepaddle; VietOCR `vgg_seq2seq` từ `models/`; nạp weights `weights_only`; gỡ paddlepaddle/paddleocr/paddlex. Đề xuất: đồng ý. *(Người dùng muốn thử cài lại PaddleOCR trước; quyết định sau khi so CER.)*
- **Q39 - Số hiệu khoản đọc sai**: (a) chấp nhận + cảnh báo; (b) vùng chữ ngắn ở lề trái chỉ gồm số và dấu chấm được đọc lại bằng model nhận dạng PP-OCR (đọc số tốt hơn), có chữ cái thì giữ kết quả VietOCR; (c) đoán theo ngữ cảnh. Đề xuất: (b).
- **Q40 - Test chậm**: test OCR đánh dấu `ocr`, mặc định không chạy (`pytest -m ocr` để chạy, vài trang TOSS, khoảng 1 phút); script riêng đo CER cả 52 trang. Đề xuất: đồng ý.
- **Q41 - Seam TDD**:
  - S11 `cat_khung_comment(anh)`;
  - S12 `tim_redline(anh_vung)` với ảnh tổng hợp (chữ đỏ gạch ngang, chữ xanh gạch chân, ảnh đen trắng);
  - S13 `chinh_nghieng(anh)` (xoay 2°, sai số ±0,3°);
  - S14 `ghep_dong(vung)`;
  - S15 tích hợp `-m ocr` trên trang 2–4 TOSS: CER < 8%, Điều 1–5, khoản 1.1/1.2.2, có `[xóa:` ở trang 3, không lẫn "Commented".

  Đề xuất: đồng ý.

**2026-10-29, ghi chú môi trường:** khi cài lại package dự án (issue 08), numpy được nâng lên 2.5.4, trong khi `rapidocr_onnxruntime 1.3.24` yêu cầu numpy < 2. Kiểm tra lại khi tiếp tục issue 05.

**2026-10-30, tiếp tục ở mạng ngoài công ty.**

Mạng này vào được huggingface.co, modelscope.cn, aistudio.baidu.com, vocr.vn. Đã tải các file sau.

| File | SHA-256 |
|---|---|
| PaddleOCR `PP-OCRv5_mobile_det` (4,8 MB, trong `~/.paddlex/official_models/`) | `afa1820c…` (inference.pdiparams) |
| PaddleOCR `PP-OCRv5_server_det` (85 MB) | `183146fe…` |
| PaddleOCR `PP-OCRv5_server_rec` (82 MB) | `63853f06…` |
| VietOCR `models/vietocr/vgg_transformer.pth` (152 MB) | `380512193a8b6cbf6fad80deacdc9b6939d10d473d199892fc6408d13775ea59` |
| VietOCR `models/vietocr/vgg-transformer.yml` | từ vocr.vn |
| VietOCR `models/vietocr/vgg_seq2seq.pth` (đã có từ trước) | `0921503a41375a0584268e23ef3d414ea478a8fe8777865c7745d38f2d0bc5db` |

- PaddleOCR 3.x trên Windows CPU bị lỗi `NotImplementedError: ConvertPirAttribute2RuntimeAttribute not support [pir::ArrayAttribute<pir::DoubleAttribute>]` (oneDNN). Khắc phục bằng `enable_mkldnn=False`.
- Script so sánh: `spike-ocr/thu_ocr3.py` (3 bộ phát hiện × 2 bộ nhận dạng) và `thu_ocr4.py` (đọc lại số hiệu bằng phần nhận dạng có sẵn của RapidOCR).
- Thông số chung: phát hiện ở 150 dpi, nhận dạng ở 300 dpi. Cột "số hiệu" là tỉ lệ số hiệu khoản (dạng `1.2.2.`) của lớp text đọc ra được; cột "+đọc lại" là tỉ lệ đó khi vùng ngắn đầu dòng chỉ gồm số và dấu chấm được đọc lại (Q39 b).

| Phát hiện | Nhận dạng | CER trang 2/3/8 | Số hiệu | + đọc lại bằng PP-OCRv5 rec | + đọc lại bằng RapidOCR rec |
|---|---|---|---|---|---|
| RapidOCR v4 | vgg_seq2seq | 4,7 / 4,5 / 9,0% | 50 / 14 / 33% | 86 / 14 / 67% | 79 / 14 / 67% |
| RapidOCR v4 | vgg_transformer | 2,0 / 1,6 / 6,8% | 43 / 86 / 100% | 86 / 86 / 100% | 79 / 86 / 100% |
| PP-OCRv5 mobile | vgg_transformer | 1,7 / 2,3 / 8,5% | 64 / 86 / 100% | 93 / 86 / 100% | (chưa đo) |
| PP-OCRv5 server | vgg_transformer | 1,5 / 1,9 / 7,1% | 57 / 71 / 100% | 86 / 71 / 100% | (chưa đo) |

- Thời gian: vgg_transformer mất 33–52 giây/trang khi chỉ nạp RapidOCR, và 80–155 giây/trang khi nạp cả model Paddle (tranh CPU). vgg_seq2seq mất khoảng 10 giây/trang. Ước tính TOSS 52 trang với vgg_transformer khoảng 40 phút.
- Kết luận:
  - Bước nhận dạng quyết định độ chính xác: transformer có CER thấp hơn khoảng 2–3 lần.
  - Bước phát hiện chênh không đáng kể.
  - Đọc lại số hiệu bằng phần nhận dạng có sẵn của RapidOCR gần bằng PP-OCRv5 rec.
- numpy 2.5.4 vẫn chạy được với `rapidocr_onnxruntime 1.3.24`, dù metadata của gói ghi yêu cầu numpy < 2.

**2026-10-30, người dùng chốt:** Q38 đồng ý: RapidOCR phát hiện, VietOCR nhận dạng, RapidOCR đọc lại số hiệu; đã gỡ paddlepaddle, paddleocr, paddlex và xóa `~/.paddlex`. Q68: mặc định `vgg_transformer`, đổi được qua `THAMDINH_OCR_MODEL`. Q39: (b). Q40 và Q41 đồng ý, ngưỡng CER hạ từ 8% xuống 5%.

### Đã làm (TDD)

- **`so_hoa/anh.py`**: các bước xử lý ảnh, không cần model, test bằng ảnh tổng hợp trong `tests/test_anh_ocr.py` (24 test, chạy mặc định).
  - S11 `cat_khung_comment(anh)`: cắt dải nền xám chạy hết chiều cao, sát lề phải.
  - S13 `chinh_nghieng(anh)`: chỉnh nghiêng bằng hình chiếu theo hàng, phạm vi ±5°.
  - S14 `ghep_dong(hop)`: ghép các hộp chữ trên cùng một dòng.
  - S12 `tim_redline(anh_vung)`: chia một hộp chữ thành các đoạn liên tiếp có nhãn `xóa` / `thêm` / `sửa` / không có nhãn, kèm cờ `cach_truoc` (có dấu cách trước đoạn).
- **Cách `tim_redline` dò redline**, rút ra khi chạy thử trên TOSS:
  - Chữ redline là chữ có lõi nét không đen. Chữ xám (lõi khoảng 85/255) cũng tính, giống `NGUONG_DEN` của lớp text, vì chữ thêm vào trong TOSS có màu xám.
  - Nhãn gắn theo từng chữ: mảnh mực chồng nhau theo chiều ngang được gộp thành một chữ, sau khi đã tách nét gạch ra.
  - Một chữ là gạch ngang khi nét gạch xuyên qua nó. Nét gạch dừng giữa chữ "4" của "4.3.4." có thể nối liền nét ngang của chữ, nên phải kiểm có nét gạch ở sát cả hai bên.
  - Bỏ các thứ không phải chữ: phần chữ của dòng trên hoặc dưới lọt vào hộp, nét đứt của đường nối comment, dấu chấm, vạch neo comment mảnh 2 px.
  - Gạch chân màu đen coi là định dạng thường, không phải redline.
- **`so_hoa/ocr.py`**:
  - `BoOCR` (Protocol) có `phat_hien`, `nhan_dang`, `doc_so`.
  - `BoOCRMacDinh(thu_muc_model, model)` chỉ nạp model ở lần dùng đầu, chạy CPU. VietOCR nạp weights bằng `torch.load`, và torch 2.15 mặc định `weights_only`.
  - `ocr_trang(trang, so, bo)` trả về `TrangOCR(dong, so_doan_redline, co_khung_comment, do_tin_cay, goc_nghieng)`. Các bước:
    1. Render 300 dpi.
    2. Cắt khung comment.
    3. Chỉnh nghiêng.
    4. Tô trắng nền màu nhạt. Highlight vàng làm VietOCR đọc "294" thành "094".
    5. Phát hiện hộp chữ ở 150 dpi, có lọc trung vị.
    6. Bỏ vạch dọc đánh dấu thay đổi ở lề.
    7. Ghép dòng.
    8. Cắt hộp theo đoạn redline rồi nhận dạng từng đoạn.
    9. Đọc lại mảnh đầu dòng bằng RapidOCR. Cụm số ở đầu kết quả VietOCR được thay bằng số hiệu do RapidOCR đọc.
  - Bước đọc lại mở rộng Q39(b): số hiệu thường nằm chung hộp với nội dung, và VietOCR có lúc đọc thừa dấu chấm ("4.1..", "3.3.3.3.").
- **`so_hoa()`**:
  - Có thêm tham số `bo_ocr`, `ep_ocr` và `tien_trinh`.
  - Trang có lớp text kém, hoặc trang nằm trong `ep_ocr`, đi đường OCR.
  - Trang OCR bị đánh dấu tin cậy thấp khi có redline, có khung comment, hoặc độ tin cậy nhận dạng dưới 85% (`NGUONG_TIN_CAY_OCR`).
  - Không có bộ OCR thì vẫn báo `CanOCRError`. Dùng `ep_ocr` thì không đọc và không ghi bản lưu.
- **Cấu hình**: thêm `THAMDINH_OCR_MODEL` và `THAMDINH_OCR_MODEL_DIR`. `pyproject.toml` có thêm nhóm phụ thuộc `ocr`.
- **`scripts/chay_tham_dinh.py`** truyền `BoOCRMacDinh` vào `so_hoa`.
- **S15** `tests/test_ocr_toss.py` (marker `ocr`) ép trang 2–4 đi đường OCR, kiểm:
  - CER dưới 5% mỗi trang.
  - Không lẫn comment.
  - Trang 3 có `[xóa:`, trang 2 không có redline.
  - Tọa độ dòng nằm trong trang.
  - `so_hoa(ep_ocr={2,3,4})` vẫn đủ Điều 1–15, khoản 4.3.2 có `[xóa:`.
  - Kết quả: 8 test qua.
- **`scripts/do_cer_ocr.py`** đo CER từng trang. Khi đo cả file, script dựng thêm cấu trúc từ kết quả OCR và so với lớp text.
- **Tài liệu**: `docs/cai-ocr.md` (cài đặt, SHA-256 model, giới hạn đã biết). Phần công nghệ trong spec đã sửa thành RapidOCR + VietOCR.
- **Script thử cũ**: `spike-ocr/thu_ocr3.py` và `thu_ocr4.py` còn import paddleocr, nên không chạy được nữa sau khi gỡ Paddle. Hai file chỉ giữ làm hồ sơ.

### Kết quả `ocr_trang` trên TOSS (vgg_transformer)

| Trang | CER | Đoạn redline (OCR / lớp text) | Độ tin cậy | Thời gian |
|---|---|---|---|---|
| 2 | 1,4% | 0 / 0 | 0,92 | 45 s |
| 3 | 1,5% | 18 / 19 | 0,91 | 75 s |
| 4 | 1,4% | 20 / 19 | 0,93 | 55 s |

Ví dụ trang 3 sau OCR: `Giá trị bảo đảm thực hiện hợp đồng: 294.000.000 [xóa: 1.918.900.000]` / `[xóa: 767.560.000 đồn][thêm: đồng]… (Bằng chữ: [xóa: Bảy trăm sáu mươi bảy triệu, năm trăm]` / `hiệu lực trong vòng 06[xóa: 23] tháng` / `[xóa: 4.3.3] [thêm: 4.3.4. - Trường hợp bảo đảm…]`.

### Ép OCR cả 52 trang TOSS (`scripts/do_cer_ocr.py`), lần 1

- **Cấu trúc:**
  - Đọc đủ Điều 1–15 và Phụ lục 01–05.
  - Có 143 số hiệu, so với 148 ở lớp text.
  - Thiếu: `8.2.1`, `8.3.1–8.3.3`, `Phụ lục 01, Mục D`, `Phụ lục 03, 2.3`, `2.4`.
  - Thừa: `Phụ lục 03, 2.3.1`, `2.4.1`.
- **Có lẫn chữ khung comment.** Ở trang 14, 15 (khổ ngang) và 47 (khổ Letter), dải xám không chạm mép phải trang, mà cách mép một lề trắng khoảng 50 px. Vì vậy `cat_khung_comment` không tìm thấy khung.
  - Đã sửa: cho phép bỏ qua lề trắng ở mép phải, tối đa 3% bề ngang. Có thêm test.
  - Sau khi sửa, cả 52 trang đều tìm thấy khung; OCR lại các trang 12–16 và 47–52 không còn chữ comment.
- **CER trung bình 4,89%.** Trang văn bản đạt 1–4%. Các trang bảng cao hơn nhiều: trang 14 là 45%, trang 47 là 61%, trang 51 là 40%, trang 48–49 khoảng 24%.
  - CER cao ở trang bảng chủ yếu do thứ tự đọc các ô khác lớp text: tỉ lệ từ của lớp text có trong OCR, không xét thứ tự, là 96%, 99% và 94% ở trang 14, 47 và 51.
  - Ở trang 47, thứ tự OCR còn tự nhiên hơn: lớp text đặt mục "II." lên trước bảng.
  - `do_cer_ocr.py` đã thêm cột "từ" cho chỉ số này.

### Ép OCR cả 52 trang TOSS, lần 2 (sau khi sửa phần cắt khung comment): đạt tiêu chí

- **Đạt tiêu chí của issue:** đọc đủ Điều 1–15 và Phụ lục 01–05, không lẫn chữ khung comment.
- **Số hiệu:** 142, so với 148 ở lớp text.
  - Thiếu: `8.2.1`, `8.3.1–8.3.3`, `Phụ lục 01, Mục D`, `Phụ lục 03, 2.2`, `2.7`.
  - Thừa: `Phụ lục 03, 2.2.1`.
  - Cả hai lần chạy đều thiếu nhóm 8.2.1 và 8.3.x; cần xem lại khi làm issue 14.
- **CER:**
  - Trung bình 4,76%. 38/52 trang dưới 5%.
  - Các trang còn lại hầu hết là trang bảng, CER cao do thứ tự đọc các ô.
  - Tỉ lệ từ của lớp text có trong OCR (không xét thứ tự): trung bình 97,8%, thấp nhất 94% (trang 51).
- **Thời gian:** cả 52 trang mất khoảng 32 phút, trung bình khoảng 36 giây/trang. Trang văn bản dày mất khoảng 1 phút.
- **Tiêu chí thứ hai** (trang có redline bị đánh dấu tin cậy thấp, khoản 4.3.2 có nhãn `[xóa:`) đã kiểm bằng test S15.
