# Thử nghiệm với model

Dùng khi một issue cần chạy Qwen3.5 thật (đổi prompt, đổi cách gọi model, đo một Mục) hoặc chấm lại các Lượt đã lưu.

Dữ liệu Hợp đồng chỉ đi tới máy chủ model ở `127.0.0.1` (ADR 0001). Agent cloud và API ngoài chỉ được nhận code và số đo, không nhận nội dung Hợp đồng.

## Các bước

1. **Đo offline trước.** Nếu thay đổi chỉ nằm ở code sau model (tổng hợp, Trích dẫn, luật chấm), chấm lại các Lượt đã lưu bằng code mới, không gọi model: `scripts/cham_lai_kho.py --so-voi HEAD` (so code đang sửa với commit gần nhất). Đủ số đo thì bỏ qua các bước chạy model.
   Xong khi: có bảng chuyển trạng thái (đúng→sai, sai→đúng) trên mọi Lượt nạp được.
2. **Ghi quy tắc giữ vào issue trước khi chạy:** Lượt gốc để so, các Mục chạy lại, ngưỡng tăng tối thiểu, số đúng→sai tối đa, thời gian tối đa (mốc ở Lượt gốc).
   Xong khi: người dùng đã đồng ý quy tắc và đồng ý riêng cho lần chạy này. Mỗi lần chạy model cần một lần đồng ý.
3. **Commit code trước khi chạy,** để mỗi Lượt thử ứng với một commit. Commit file issue riêng với code, để revert code không kéo theo file issue.
4. **Bật máy chủ** Qwen (cổng 8080) và bge-m3 (cổng 8081) theo `docs/chay-model-local.md`, ghi stderr vào `data/llama-server.log` và `data/bge-m3-server.log`, chờ `/health` trả `ok`.
5. **Chạy chuỗi nền** bằng `scripts/do_thu_nghiem.py`: chạy tiếp Lượt gốc với các Mục chọn, tự dừng khi quá thời gian tối đa, rồi so với Lượt gốc bằng `scripts/so_sanh_lan_chay.py` và in từng Tiêu chí so với Bộ chuẩn. Nhật ký vào `data/nhat-ky/`.
6. **Kiểm tra mỗi giờ** bằng một lịch cron (phút lẻ, không phải :00): đọc nhật ký chuỗi, nhật ký Lượt, đuôi `data/llama-server.log`, xem tiến trình còn sống không. Báo người dùng ngắn gọn mỗi lần.
7. **Khi chuỗi in "Xong chuỗi":** hủy lịch, tắt hai máy chủ, ghi số đo và quyết định giữ/bỏ theo quy tắc ở bước 2 vào Comments của issue, rồi báo người dùng.
   Xong khi: không còn lịch, không còn tiến trình `llama-server`, issue có số đo.
8. **Bỏ thay đổi:** revert commit code, đặt issue `Status: wontfix`. Nếu code đó đổi dạng dữ liệu lưu trong kho (thêm trường vào Tiêu chí, Mục…), xóa các Lượt chạy bằng code đó khỏi `data/tham-dinh.sqlite3`: sao lưu file kho trước, tạm gỡ trigger `khong_xoa_de_xuat`, xóa dòng `luot` và `muc_de_xuat`, dựng lại trigger bằng `SCHEMA` trong `kho_luot.py`. Kiểm lại: mọi Lượt trong kho nạp được bằng `KhoLuot.nap`.

## Ghi chú

- Sau khi cài hoặc đổi file model Qwen, chạy lại `pytest -m llm`.
- Bộ chuẩn `eval/chuan/toss.yaml` là chuẩn đúng (người dùng điền tay). Thấy chỗ nghi sai thì ghi vào issue, không sửa file.
- Máy chỉ có CPU: viết khoảng 2,5 token/giây, đọc prompt khoảng 8–13 token/giây. Phần đuôi prompt sau đoạn dùng chung phải dưới khoảng 516 token thì mới dùng lại được cache.
