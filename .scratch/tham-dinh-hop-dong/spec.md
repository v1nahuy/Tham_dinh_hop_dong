# Spec: Thẩm định Dự thảo Hợp đồng đầu ra (bản demo)

Thuật ngữ theo [GLOSSARY.md](../../GLOSSARY.md). Quyết định kiến trúc: [ADR 0001](../../docs/adr/0001-on-premise-cho-du-lieu-hop-dong.md), [ADR 0002](../../docs/adr/0002-truy-xuat-theo-cau-truc-thay-vi-rag-thuan.md).

## Mục tiêu

Người thẩm định tải lên một Dự thảo (PDF), chọn một Phiên bản checklist và nhận Kết quả đề xuất (Đạt / Lưu ý / Vi phạm) cho từng Mục checklist, kèm Trích dẫn đã xác minh từ Văn bản hiệu lực. Người thẩm định sửa thành Kết quả đã duyệt và xuất báo cáo .docx.

Việc thẩm định luôn đứng về phía **Công ty** (VTIT). Hệ thống tự xác định Công ty là bên nào trong Hợp đồng; **Khách hàng** là bên còn lại.

## Ngoài phạm vi bản demo

- Đăng nhập, phân quyền, nhiều người dùng. Bản demo chạy local trên một máy tính.
- Tự động gỡ redline từ ảnh.
- Tra cứu web khi thẩm định; thay bằng Danh mục tham chiếu.
- Nhập dữ kiện ngoài Hợp đồng (giấy ủy quyền, năng lực thực tế…). Những Tiêu chí cần dữ kiện này cho Đánh giá tiêu chí "không rõ".
- Triển khai on-prem. Bản demo cũng chạy local: Qwen3.5 qua llama.cpp, sau lớp trung gian `LLMClient` (ADR 0001).

## Luồng người dùng (Streamlit, local)

1. Tải PDF lên, chọn Phiên bản checklist.
2. **Số hóa** → Văn bản hiệu lực.
3. (Tùy chọn) Xem và sửa Văn bản hiệu lực: ảnh trang đặt cạnh text, các trang tin cậy thấp được đánh dấu.
4. **Thẩm định** → Kết quả đề xuất.
5. Bảng các Mục checklist có màu theo Kết quả. Mở từng Mục để xem các Đánh giá tiêu chí, Trích dẫn và vị trí (Điều khoản, trang).
6. Sửa thành Kết quả đã duyệt.
7. Xuất .docx.

## Bước 1: Số hóa (không dùng LLM)

- **Lớp text trước:** đọc lớp text của PDF và đo chất lượng (tỷ lệ ký tự tiếng Việt có dấu hợp lệ, ký tự lỗi `�`). Đánh giá theo từng trang; đạt ngưỡng thì dùng lớp text, không đạt thì OCR. Lớp text của TOSS tốt (đọc bằng pypdfium2), nên TOSS đi qua lớp text. Khung comment được loại theo tọa độ: bỏ chữ nằm trong dải nền xám bên phải trang.
- **OCR:** render trang ~300 dpi → cắt khung comment (dải nền xám bên phải) → bỏ header/footer ("Trang x / y") → chỉnh nghiêng, khử nhiễu → OCR tiếng Việt → dòng kèm tọa độ và độ tin cậy.
- **Redline:** không gỡ, mà gắn nhãn tại chỗ. Chữ màu có nét gạch ngang thành `[xóa: …]`, có nét gạch chân thành `[thêm: …]`, có màu nhưng không có nét gạch thành `[sửa: …]`. Lớp text và OCR dùng cùng định dạng nhãn. Trang có redline (hoặc trang OCR có độ tin cậy nhận dạng thấp) được đánh dấu tin cậy thấp kèm lý do; trang có khung comment chỉ được ghi chú "có khung comment (đã bỏ)", không bị đánh dấu. Bước kiểm tra Trích dẫn bỏ qua các nhãn khi so khớp.
- **Cấu trúc:** ghép dòng thành đoạn; nhận diện ĐIỀU / Khoản (4.3.2.) / Phụ lục bằng quy tắc → danh sách Điều khoản {số hiệu, tiêu đề, trang, nội dung, tọa độ}. Phụ lục trong file là một phần của Văn bản hiệu lực.
  - Số hiệu giữ như in trong Hợp đồng; số hiệu lấy theo bản mới (bỏ phần `[xóa: …]`). Mỗi Điều khoản có mã nội bộ theo thứ tự, nên hai khoản cùng số hiệu không đè nhau. Số hiệu trùng, Điều nhảy cóc, khoản không có khoản cha được ghi cảnh báo.
  - Phần trước Điều 1 là "Phần mở đầu". Điểm a), b) gộp vào khoản chứa nó. Điều khoản biết Điều khoản cha; nội dung chỉ gồm phần của chính nó.
  - Trong Phụ lục: tách theo ĐIỀU và khoản nếu có, nếu không thì theo mục A./B./I./II. Không tách bảng và danh sách đánh số. Số hiệu ghi kèm Phụ lục, ví dụ "Phụ lục 03, Điều 2".
- **Lưu và tái sử dụng:** Văn bản hiệu lực (kể cả bản đã sửa tay) được lưu theo hash file PDF và dùng lại ở các lần chạy sau.

## Bước 2: Thẩm định

1. **Gắn Chủ đề:** LLM đọc từng Điều khoản (vừa ngữ cảnh ~32k) và gắn các Chủ đề từ danh sách Chủ đề của Phiên bản checklist. Việc này làm một lần cho mỗi Văn bản hiệu lực.
2. **Chọn Điều khoản cho mỗi Mục checklist**, có hai chế độ:
   - *Toàn văn:* đưa toàn bộ Văn bản hiệu lực vào (TOSS khoảng 38k token, cần ngữ cảnh 64k). Prompt có phần đầu cố định (hướng dẫn + toàn văn) để llama-server dùng lại phần đã đọc giữa các Mục. Vượt ngữ cảnh thì báo lỗi, không tự cắt.
   - *Truy xuất:* lấy mọi Điều khoản mang Chủ đề mà Mục checklist khai báo (kèm các Điều khoản con cháu; Điều khoản cha chỉ đưa dòng tiêu đề), cộng thêm top-5 BM25 + top-5 embedding (bge-m3) làm lưới an toàn. Luôn đưa nguyên Điều khoản, không cắt nhỏ. Ngân sách mặc định 16k token văn bản mỗi Mục; vượt thì bỏ nguyên các Điều khoản ưu tiên thấp nhất (lưới an toàn trước, rồi điểm liên quan thấp) và ghi cảnh báo. Ngữ cảnh khác nhau giữa các Mục nên không dùng lại được bộ nhớ đệm như chế độ toàn văn.
3. **Đánh giá tiêu chí:** LLM trả về JSON cho từng Tiêu chí của Mục: `thỏa | không thỏa | không rõ`, lý do, Trích dẫn (số hiệu Điều khoản + nguyên văn). Với Tiêu chí định lượng, LLM chỉ trích xuất giá trị (kèm Trích dẫn) và code thực hiện phép so sánh.
4. **Tổng hợp Kết quả (code):** mức xấu nhất thắng.
   - Có Tiêu chí Vi phạm nào thỏa → **Vi phạm**.
   - Nếu không: có Tiêu chí Lưu ý nào thỏa, có Tiêu chí Đạt nào không thỏa hoặc không rõ, hoặc có Tiêu chí Lưu ý/Vi phạm nào không rõ → **Lưu ý**. Ghi chú khi không rõ: dùng `ghi_chu_khong_ro` của Mục nếu có, nếu không thì "chưa xác định được: <mô tả tiêu chí>".
   - Chỉ khi mọi Tiêu chí Đạt đều thỏa → **Đạt**.
   - Tiêu chí "không rõ" do thiếu thông tin ngoài Hợp đồng hoặc tài liệu viện dẫn không đính kèm (HSĐX, HSYC…) → Lưu ý, kèm ghi chú "cần đối chiếu/xác minh …".
5. **Kiểm tra Trích dẫn:** so khớp nguyên văn với Điều khoản được trích và các Điều khoản con. Trước khi so: chuẩn hóa Unicode NFC, khoảng trắng, các kiểu ngoặc kép và gạch ngang, bỏ nhãn redline (bản có chữ đã xóa và bản đã chấp nhận thay đổi đều được tính). Vẫn phân biệt dấu tiếng Việt và chữ hoa/thường. Trích dẫn có "…" được tách đoạn, mỗi đoạn phải khớp theo đúng thứ tự. Tìm thấy ở Điều khoản khác → "khớp nhưng sai số hiệu" kèm số hiệu đúng. Không tìm thấy → "không xác minh được". Khi không có điều khoản tương ứng, Trích dẫn để trống kèm lý do "Không tìm thấy điều khoản về …".

## Checklist có cấu trúc

- Lưu thành file YAML có phiên bản trong `checklists/`. Phiên bản là bất biến.
- Mỗi Mục checklist gồm: số thứ tự, câu hỏi, Chủ đề, căn cứ pháp lý, danh sách Tiêu chí cho từng mức (Đạt / Lưu ý / Vi phạm). Mỗi Tiêu chí có mã, mô tả, loại (`định tính` | `định lượng` với trường trích xuất, phép so sánh, ngưỡng), và ghi chú khi "không rõ".
- **V1.1** = V1 cộng các thay đổi đã chốt:
  - Mục 11: thay "0%" bằng "không chịu thuế GTGT" theo khoản 21 Điều 5 Luật Thuế GTGT 48/2024/QH15 và khoản 13 Điều 4 NĐ 181/2025/NĐ-CP. Dịch vụ không phải phần mềm áp dụng 10%. Gắn cờ: cần pháp chế đối chiếu bản gốc. Tiêu chí: giá trước thuế và GTGT ghi tách riêng; LLM phân loại dịch vụ (phần mềm / hạ tầng-phần cứng / hỗn hợp); code đối chiếu phân loại với cách xử lý thuế; hỗn hợp hoặc không rõ → Lưu ý.
  - Mục 6: (1) có cung cấp hàng hóa/thiết bị không; (2) nếu có, có điều khoản cấm tái xuất và dùng cho quân sự không; (3) có khớp dấu hiệu EAR nào trong Danh mục tham chiếu không. Không có hàng hóa và không khớp dấu hiệu → thỏa. Khớp dấu hiệu → không rõ, Lưu ý "cần xác minh lại EAR".
  - Mục 2, 6, 11: "tìm trên mạng" được thay bằng Danh mục tham chiếu.
- **Danh mục tham chiếu** đi kèm phiên bản: ngành nghề đã đăng ký (lấy từ V1), ngành nghề kinh doanh có điều kiện (Phụ lục IV Luật Đầu tư), thuế GTGT theo loại dịch vụ, dấu hiệu EAR.
- Kèm theo file khác biệt V1 → V1.1 để pháp chế duyệt.

## Lưu trữ (local)

SQLite cùng thư mục `data/`. Lượt thẩm định lưu: PDF (theo hash), Phiên bản checklist, Văn bản hiệu lực, chế độ chạy, mô hình, Kết quả đề xuất (gồm Đánh giá tiêu chí), Kết quả đã duyệt và thời điểm.

## Báo cáo .docx

Bố cục bảng giống checklist. Mỗi Mục checklist gồm: câu hỏi, Kết quả đã duyệt (nền xanh/vàng/đỏ như checklist), giải thích, Trích dẫn kèm vị trí. Phụ lục cuối báo cáo liệt kê những Mục mà Kết quả đã duyệt khác Kết quả đề xuất.

## Đo chất lượng

- **Bộ chuẩn TOSS:** người dùng tự làm bằng tay theo V1.1, ghi Đánh giá tiêu chí cho từng Tiêu chí.
- **Biến thể đầu vào:** từ TOSS tạo bản giả lập scan (nghiêng, nhiễu, dpi thấp) và bản đã gỡ redline thủ công, để kiểm thử Bước 1.
- **So sánh ba nguồn:** bộ chuẩn, chế độ toàn văn, chế độ truy xuất. Những Tiêu chí mà ba nguồn không thống nhất được xuất thành danh sách gửi pháp chế xem.

## Công nghệ (bản demo)

Python 3.12, Streamlit, pypdfium2 (render và lớp text), RapidOCR (PP-OCRv4 qua ONNX Runtime: phát hiện dòng, đọc lại số hiệu khoản) + VietOCR `vgg_transformer` (nhận dạng), Qwen3.5 (4B/9B, GGUF Q4_K_M) chạy bằng llama.cpp `llama-server` (API chuẩn OpenAI tại 127.0.0.1, ép JSON schema) sau một interface `LLMClient`, BM25 (tách theo âm tiết + bigram), bge-m3 bản GGUF chạy bằng `llama-server --embedding`, SQLite, python-docx, pytest.
