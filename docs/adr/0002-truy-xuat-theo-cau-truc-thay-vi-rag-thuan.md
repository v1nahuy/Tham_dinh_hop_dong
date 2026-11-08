# Truy xuất theo cấu trúc hợp đồng thay vì RAG embedding thuần

Mô hình on-prem có ngữ cảnh hạn chế (giả định ~32k token khi chưa biết hạ tầng), nên Bước 2 không thể đưa toàn văn Hợp đồng vào. Chúng tôi không dùng RAG thuần (chia khối cố định + top-k theo độ tương đồng) vì nó không chứng minh được một điều khoản *không tồn tại*, trong khi rất nhiều Tiêu chí là kiểm tra sự vắng mặt (không có liability cap, không có non-solicitation…). Thay vào đó: chia Hợp đồng theo Điều/Khoản/Phụ lục, gắn Chủ đề cho từng Điều khoản bằng một lượt đọc toàn bộ, mỗi Mục checklist khai báo sẵn Chủ đề liên quan, và chỉ dùng BM25 + embedding làm lưới an toàn.

## Consequences

Checklist có cấu trúc phải mang danh sách Chủ đề cho từng Mục checklist. Bản demo chạy song song chế độ toàn văn (mốc trần) và chế độ truy xuất để đo khoảng cách trước khi chuyển sang on-prem.
