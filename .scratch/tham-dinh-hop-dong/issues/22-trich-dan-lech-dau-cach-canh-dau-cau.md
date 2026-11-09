# 22 - Trích dẫn lệch dấu cách cạnh dấu câu

Status: done

## Vấn đề

Model chép câu trích thêm hoặc bớt dấu cách cạnh dấu câu so với Hợp đồng, ví dụ "10. Đầu mối" trong khi Hợp đồng ghi "10.Đầu mối". Kiểm tra Trích dẫn so chuỗi chính xác (chỉ gộp khoảng trắng) nên báo "không xác minh được" dù câu trích đúng.

Đo trên 16 Lượt đã lưu (không gọi model): bỏ dấu cách sát dấu câu ở nội dung câu trích và Điều khoản thì 37/217 Trích dẫn "không xác minh được" thành khớp (8.D1, 8.D2, 8.V1 ở mọi Lượt truy xuất, 17.D1, 17.V3, …); không Trích dẫn nào đang khớp đổi trạng thái.

## Cách làm (Q186)

- Khi so nội dung câu trích với Điều khoản, bỏ dấu cách nằm sát dấu câu ở cả hai bên. Dấu cách giữa hai chữ giữ nguyên.
- Không chuẩn hóa số hiệu (chuẩn hóa cả số hiệu làm "Phụ lục 02, Mục A" lệch số hiệu Điều khoản: 446 Trích dẫn đổi thành sai số hiệu khi thử).

## Test (Q187)

- Seam `kiem_tra_trich_dan` (`tests/test_trich_dan.py`): "10. Đầu mối" khớp Điều khoản ghi "10.Đầu mối"; "4.3.1.Thời hạn" khớp "4.3.1. Thời hạn"; chữ dính liền ("ngàyký") vẫn không khớp.
- Chấm lại Trích dẫn 15 Lượt còn lại từ dữ liệu đã lưu, so với số đo trên.

## Tiêu chí hoàn thành

- Test xanh; số Trích dẫn khớp lại khớp số đo; không Trích dẫn nào đang khớp đổi trạng thái.

## Comments

**2026-11-09, đã làm và đo.**
- TDD qua `kiem_tra_trich_dan`: hai ca khớp mới ("10. Đầu mối" so với "10.Đầu mối"; "4.3.1.Thời hạn … hợp đồng :" so với "4.3.1. Thời hạn … hợp đồng:") đỏ rồi xanh; ca chữ dính liền "ngàyký" vẫn không khớp. `_chuan_hoa_noi_dung` dùng cho nội dung câu trích và Điều khoản; `chuan_hoa` (dùng cho số hiệu) không đổi. 356 test thường xanh.
- Chấm lại 15 Lượt (code HEAD so với code mới, không gọi model): 37 Trích dẫn "không xác minh được" thành khớp; 180 vẫn không xác minh được; 1480 khớp và 444 sai số hiệu không đổi. Đạt tiêu chí hoàn thành.
- Lượt đã lưu giữ trạng thái Trích dẫn lúc chạy; Lượt mới dùng cách so mới.
