# 33 - Chạy lại vài Mục ở chế độ toàn văn có bị chậm không

Status: needs-info

## Vấn đề

Ở chế độ toàn văn, Qwen3.5 dùng lại phần đầu prompt nhờ điểm lưu trạng thái tạo ở Mục chạy đầu tiên; điều kiện là đuôi prompt của Mục đó dưới 516 token. Mục 1 thỏa (issue 28 có test). Khi chạy lại một số Mục (`--chi-muc`, nút "Chạy lại phần lỗi"), Mục chạy đầu tiên có thể không phải Mục 1, đuôi của nó vượt 516 token (Mục 2 khoảng 9.800 ký tự), nên có thể các Mục sau phải đọc lại cả Hợp đồng, mỗi Mục khoảng 80 phút.

## Cần thông tin

Chưa đo: các lần thử gần đây đều chạy chế độ truy xuất. Muốn biết chắc phải chạy model (cần người dùng đồng ý riêng). Nếu đúng là chậm, một cách sửa có thể là chạy một lượt "mồi" ngắn với đuôi Mục 1 trước khi chạy các Mục được chọn.
