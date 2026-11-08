# Checklist đầu ra: khác biệt V1 → V1.1 (để pháp chế duyệt)

V1.1 chuyển Checklist V1 (260716) sang dạng có cấu trúc để hệ thống thẩm định đọc được. File gốc: [dau-ra-v1.1.yaml](dau-ra-v1.1.yaml). Tài liệu này liệt kê **mọi chỗ V1.1 khác với V1** và **những điểm cần pháp chế quyết định**.

## 1. Thay đổi về hình thức (không đổi ý nghĩa)

- **Tách tiêu chí.** Mỗi ô Đạt / Lưu ý / Vi phạm trong V1 được tách thành các Tiêu chí đơn lẻ, mỗi tiêu chí có mã (ví dụ `7.D1`, `7.L1`, `7.V1`: D là Đạt, L là Lưu ý, V là Vi phạm).
- **Cách tính Kết quả** của một Mục:
  - Có Tiêu chí Vi phạm nào thỏa → **Vi phạm**.
  - Nếu không: có Tiêu chí Lưu ý nào thỏa, hoặc có Tiêu chí Đạt nào không thỏa/không rõ → **Lưu ý**.
  - Chỉ khi mọi Tiêu chí Đạt đều thỏa → **Đạt**.
- **"Công ty" / "Khách hàng"** thay cho "VTIT" / "Bên A". Trong Hợp đồng, Công ty có thể là Bên A hoặc Bên B.
- **Tiêu chí bắt đầu bằng "Nếu ..."** (ví dụ 4.D2–4.D5, 6.D2, 11.D3) được coi là thỏa khi điều kiện không xảy ra.
- **Tiêu chí định lượng.** Hệ thống chỉ trích xuất con số từ Hợp đồng, còn phép so sánh do code thực hiện. Gồm: 7.D1/7.V1 (phạt ≤ / > 8%), 8.D2 (báo trước chấm dứt ≥ 30 ngày), 10.L1 (thời hạn thanh toán < 30 ngày), 13.D3 (service credit ≤ 15%), 13.L1 (uptime ≥ 99,9%), 16.D4/16.D5 (báo bất khả kháng 7–15 ngày), 17.D2 (báo trước thay nhân sự ≥ 15 ngày), 17.D5 (bảo hành ≥ 12 tháng), 17.D7 (non-solicitation ≥ 12 tháng).
- **Tiêu chí có điều kiện.** Tiêu chí 1.V2 chỉ áp dụng khi giá trị Hợp đồng trên 2 tỷ đồng; hệ thống trích xuất giá trị, code so sánh.
- **Tiêu chí cần thông tin ngoài Hợp đồng** (2.V2, 9.V1, 13.V2, 14.D1, 14.V1). Nếu Mục ra Vi phạm do một trong các tiêu chí này, kết quả kèm thông báo "**các tiêu chí này cần thông tin ngoài Hợp đồng**".
- **Ngành nghề đã đăng ký** ở Mục 2 (44 mã ngành) được chuyển sang danh mục tham chiếu [nganh-nghe-dang-ky.yaml](danh-muc/nganh-nghe-dang-ky.yaml), nội dung giữ nguyên.

## 2. Thay đổi về nội dung (đã chốt, cần pháp chế xác nhận)

| Mục | V1 | V1.1 |
|---|---|---|
| 2 | "Tìm trên google" ngành nghề có điều kiện | Tra theo danh mục [nganh-nghe-co-dieu-kien.yaml](danh-muc/nganh-nghe-co-dieu-kien.yaml) (bản nháp). |
| 6 | "Cần tìm đề xuất trên mạng"; Đạt = "đã kiểm tra không thuộc EAR" | Tra theo danh mục [dau-hieu-ear.yaml](danh-muc/dau-hieu-ear.yaml) (bản nháp). Thêm Lưu ý **6.L1**: khớp dấu hiệu EAR thì ghi "**cần xác minh lại EAR**". |
| 11 | Đạt: "dịch vụ phát triển phần mềm nội địa: **0%**; dịch vụ khác liên quan đến phần mềm: 10%" | Đạt **11.D2**: sản phẩm/dịch vụ phần mềm **không chịu thuế GTGT**; dịch vụ khác 10%. Thêm Lưu ý **11.L3**: dịch vụ hỗn hợp hoặc không phân loại rõ. "Cần tìm đề xuất trên mạng" được thay bằng danh mục [thue-gtgt.yaml](danh-muc/thue-gtgt.yaml). |
| 11 | (không có căn cứ) | Căn cứ: **khoản 21 Điều 5 Luật Thuế GTGT số 48/2024/QH15**; **khoản 13 Điều 4 Nghị định 181/2025/NĐ-CP**. ⚠️ Mới xác minh qua nguồn thứ cấp (MISA, Thư viện Pháp luật, PwC); **cần đối chiếu bản gốc** trên Công báo. |
| 1 | Lưu ý: "HĐ trên 2 tỷ phải do Giám đốc ký"; Vi phạm: "Phó Giám đốc ký HĐ trên 2 tỷ" | Bỏ Lưu ý. Giá trị trên 2 tỷ mà người ký không phải Giám đốc/Tổng Giám đốc → **Vi phạm** (1.V2), kể cả khi ký theo ủy quyền. Từ 2 tỷ trở xuống → xét tiếp các tiêu chí Đạt. |
| 11 | "Điều khoản điều chỉnh thuế gây bất lợi" ở cả Lưu ý lẫn Vi phạm | Xếp ở **Vi phạm** (11.V3). |
| 7 | (không có căn cứ) | Thêm căn cứ: Điều 301 Luật Thương mại 2005 (mức phạt ≤ 8%). |

## 3. Các điểm pháp chế đã quyết định (2026-10-27)

| # | Điểm | Quyết định |
|---|---|---|
| 1, 2 | Mục 1: 1.L1, 1.V2 | Bỏ 1.L1. Giá trị > 2 tỷ: người ký không phải Giám đốc/Tổng Giám đốc → Vi phạm; ≤ 2 tỷ: xét tiếp tiêu chí Đạt. |
| 3 | Mục 10.L1 "thời hạn thanh toán dưới 30 ngày" | Giữ nguyên chữ của V1. |
| 4 | Mục 10, ô Vi phạm | Đồng ý cách tách của V1.1. |
| 5 | Mục 11, 11.L4 | Chuyển thành Vi phạm 11.V3. |
| 6 | Mục 14.D1 và các tiêu chí cần thông tin ngoài Hợp đồng | Giữ. Nếu ra Vi phạm, kèm thông báo "các tiêu chí này cần thông tin ngoài Hợp đồng". |
| 7 | Mục 16, khoảng [7, 15] ngày | Đồng ý. |
| 8 | Mục 17.D2, tối thiểu 15 ngày | Đồng ý. |
| 9 | Mục 4, căn cứ pháp lý | Giữ nguyên chữ của V1. |

Căn cứ pháp lý Mục 11 vẫn **cần đối chiếu bản gốc** (xem bảng ở phần 2).

## 4. Danh mục tham chiếu (bản nháp, cần pháp chế duyệt)

Mọi mục trong danh mục đều ghi nguồn. Các nguồn tiếng Việt mới tra qua trang thứ cấp, **cần đối chiếu bản gốc**.

- [nganh-nghe-co-dieu-kien.yaml](danh-muc/nganh-nghe-co-dieu-kien.yaml): 25 ngành, nghề gần lĩnh vực của Công ty, trích từ **Phụ lục IV Luật Đầu tư số 143/2025/QH15**. Phụ lục này có hiệu lực từ 01/7/2026 và thay bản của Luật Đầu tư 2020. Mỗi ngành nghề kèm mã ngành đã đăng ký của Công ty có thể liên quan.
  - ⚠️ Theo nguồn thứ cấp, Phụ lục IV mới không còn "dịch vụ việc làm" và "cho thuê lại lao động". Công ty đã đăng ký 7821 và 7822, nên cần xác nhận hai hoạt động này còn là ngành nghề có điều kiện không.
- [thue-gtgt.yaml](danh-muc/thue-gtgt.yaml): phần mềm (không chịu thuế), gói hỗn hợp, dịch vụ khác (10%), viễn thông (10%, không giảm), mức 8%.
  - ⚠️ **Nghị định 174/2025/NĐ-CP** giảm thuế GTGT còn 8% từ 01/7/2025 đến hết 31/12/2026, và đã **bỏ nhóm CNTT khỏi danh sách không được giảm**. Dịch vụ CNTT chịu thuế 10% (ví dụ phần cứng, thuê hạ tầng) vì vậy có thể ghi 8%.
  - Cần xác nhận: thuê hạ tầng hoặc điện toán đám mây có được coi là dịch vụ phần mềm không.
- [dau-hieu-ear.yaml](danh-muc/dau-hieu-ear.yaml): 9 dấu hiệu sàng lọc, gồm xuất xứ Mỹ, phần cứng, nội dung Mỹ (de minimis), mã hóa (Category 5 Part 2), tính toán tiên tiến/AI, mục đích quân sự, bên bị hạn chế, tái xuất, chuyển giao công nghệ. Mỗi dấu hiệu dẫn điều khoản của 15 CFR. Danh mục chỉ dùng để sàng lọc: khớp dấu hiệu thì nhận Lưu ý "cần xác minh lại EAR", không phải kết luận phân loại.

## 5. Nội dung các điểm (bản gửi pháp chế ban đầu)

1. **Mục 1, Lưu ý 1.L1.** Theo đúng chữ của V1, mọi hợp đồng trên 2 tỷ đồng đều nhận **Lưu ý**, kể cả khi Giám đốc đã ký đúng thẩm quyền. Đây có phải ý định không, hay chỉ cần Lưu ý khi người ký không phải Giám đốc (trường hợp này đã có 1.V2 xếp Vi phạm)?
2. **Mục 1, Vi phạm 1.V2** ("Phó Giám đốc ký HĐ trên 2 tỷ") cần kết hợp hai dữ kiện là người ký và giá trị. Hiện hệ thống để LLM tự đánh giá tiêu chí này thay vì so sánh số bằng code như các tiêu chí định lượng khác, vì cấu trúc checklist chưa hỗ trợ tiêu chí có điều kiện.
3. **Mục 10, Lưu ý 10.L1** "Thời hạn thanh toán ngắn (dưới 30 ngày)". Từ góc độ Công ty là bên nhận tiền, thời hạn thanh toán ngắn thường là có lợi. Ý của V1 có phải là "thời hạn để Công ty chuẩn bị/nộp hồ sơ thanh toán ngắn"? V1.1 đang giữ nguyên chữ của V1.
4. **Mục 10, ô Vi phạm** của V1 có câu chung "Điều khoản thanh toán gây bất lợi cho Công ty". Câu này quá rộng để kiểm tra được nên V1.1 bỏ; chỉ giữ hai trường hợp cụ thể là 10.V1 và 10.V2. Ngoài ra, "hồ sơ thanh toán phức tạp" trong V1 xuất hiện ở cả Lưu ý lẫn Vi phạm: V1.1 giữ phần chung ở Lưu ý (10.L3), phần "tài liệu không phát sinh khi nghiệm thu / tài liệu đơn phương của Khách hàng" ở Vi phạm (10.V1).
5. **Mục 11, Lưu ý 11.L4 và Vi phạm.** V1 ghi "điều khoản điều chỉnh thuế gây bất lợi cho Công ty" ở cả Lưu ý lẫn Vi phạm. V1.1 xếp câu này ở **Lưu ý**, còn **Vi phạm** chỉ là "không cho điều chỉnh khi thuế suất thay đổi" (11.V2).
6. **Mục 14, tiêu chí 14.D1** ("đã đối chiếu với năng lực thực tế") không thể kiểm chứng từ Hợp đồng, nên Mục 14 **sẽ không bao giờ đạt Đạt**, tối đa là Lưu ý kèm ghi chú cần xác minh. Tương tự với 2.V2, 9.V1, 13.V2, 14.V1: các tiêu chí này cần thông tin ngoài Hợp đồng.
7. **Mục 16, Đạt 16.D4/16.D5.** V1 ghi "thông báo trong 7–15 ngày". V1.1 hiểu là thời hạn thông báo bất khả kháng phải nằm trong khoảng [7, 15] ngày. Hợp đồng quy định ngắn hơn 7 ngày (bất lợi cho Công ty) sẽ không đạt; dài hơn 15 ngày cũng không đạt. Có đúng ý không?
8. **Mục 17, Đạt 17.D2** "thông báo trước 15–30 ngày" được hiểu là **tối thiểu 15 ngày**.
9. **Mục 4, căn cứ pháp lý** giữ nguyên chữ của V1 ("Luật Bảo vệ dữ liệu cá nhân; Luật An ninh mạng hiện hành"), chưa ghi số hiệu văn bản. Pháp chế bổ sung nếu cần.
