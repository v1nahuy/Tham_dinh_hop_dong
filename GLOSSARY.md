# Thẩm định hợp đồng đầu ra

Phần mềm hỗ trợ thẩm định hợp đồng đầu ra của VTIT: đối chiếu từng mục của một Checklist với nội dung Hợp đồng và đưa ra Kết quả kèm Trích dẫn.

## Các bên

**Công ty**:
VTIT, luôn là bên cung cấp dịch vụ/hàng hóa trong Hợp đồng đầu ra và là bên mà việc thẩm định bảo vệ quyền lợi.
_Avoid_: Bên B, VTIT (trong mô hình), nhà cung cấp

**Khách hàng**:
Bên đối tác ký Hợp đồng với Công ty, bất kể trong văn bản được gọi là Bên A hay Bên B.
_Avoid_: Bên A, đối tác, bên mua

## Hợp đồng

**Hợp đồng đầu ra**:
Hợp đồng mà Công ty bán hàng hóa hoặc cung cấp dịch vụ cho Khách hàng; là đối tượng duy nhất được thẩm định.
_Avoid_: Hợp đồng (khi cần phân biệt với hợp đồng đầu vào)

**Dự thảo**:
Phiên bản Hợp đồng đầu ra đang đàm phán, chưa ký, thường còn thay đổi theo dõi và bình luận; là đầu vào của việc thẩm định.
_Avoid_: bản nháp hợp đồng, draft

**Văn bản hiệu lực**:
Nội dung Hợp đồng sau khi chấp nhận mọi thay đổi theo dõi (bỏ phần bị xóa, giữ phần được chèn) và loại bỏ các bình luận bên lề; là văn bản duy nhất được dùng để thẩm định.
_Avoid_: bản sạch, bản cuối

**Điều khoản**:
Một đơn vị cấu trúc của Văn bản hiệu lực (Điều, Khoản hoặc Phụ lục), có số hiệu và số trang; là đơn vị mà Trích dẫn trỏ tới.
_Avoid_: đoạn, chunk, mục (dễ nhầm với Mục checklist)

**Chủ đề**:
Nhãn nội dung (ví dụ thanh toán, phạt vi phạm, sở hữu trí tuệ) gắn cho Điều khoản và được khai báo trong Mục checklist, dùng để xác định Điều khoản nào liên quan đến Mục checklist nào.

## Checklist

**Checklist**:
Bộ tiêu chí thẩm định có Phiên bản, gồm nhiều Mục checklist.
_Avoid_: bảng kiểm, danh mục

**Phiên bản checklist**:
Một bản cụ thể, bất biến của Checklist (ví dụ "Checklist đầu ra V1.1"); mọi thay đổi nội dung đều tạo phiên bản mới, và mỗi Lượt thẩm định gắn với đúng một Phiên bản checklist.

**Danh mục tham chiếu**:
Dữ liệu tra cứu đi kèm một Phiên bản checklist (ngành nghề đã đăng ký, ngành nghề kinh doanh có điều kiện, thuế suất GTGT, dấu hiệu EAR), thay cho việc tra cứu bên ngoài khi thẩm định.
_Avoid_: dữ liệu tra google, danh sách ngoài

**Mục checklist**:
Một câu hỏi thẩm định trong Checklist, kèm tiêu chí cho từng mức Kết quả và căn cứ pháp lý nếu có.
_Avoid_: câu hỏi, điều kiện, item

**Tiêu chí**:
Một điều kiện đơn lẻ, kiểm tra được, thuộc về đúng một mức Kết quả của một Mục checklist (tiêu chí Đạt, tiêu chí Lưu ý hoặc tiêu chí Vi phạm); mỗi mức gồm một danh sách Tiêu chí.
_Avoid_: điều kiện, yêu cầu

**Đánh giá tiêu chí**:
Nhận định một Tiêu chí là thỏa, không thỏa hoặc không rõ đối với một Hợp đồng, kèm Trích dẫn; Kết quả của Mục checklist được suy ra từ các Đánh giá tiêu chí, không được đánh giá trực tiếp.

## Thẩm định

**Lượt thẩm định**:
Một lần đối chiếu một Hợp đồng với một Phiên bản checklist, cho ra một Kết quả cho mỗi Mục checklist.
_Avoid_: phiên, lần chạy, review

**Kết quả**:
Đánh giá của một Mục checklist, nhận đúng một trong ba mức Đạt, Lưu ý hoặc Vi phạm. Mức xấu nhất thắng: có tiêu chí Vi phạm nào khớp thì là Vi phạm; nếu không, có tiêu chí Lưu ý nào khớp, thiếu tiêu chí Đạt nào, chưa loại trừ được một tiêu chí Lưu ý hoặc Vi phạm, hoặc thiếu thông tin ngoài Hợp đồng để kết luận thì là Lưu ý; chỉ khi đủ mọi tiêu chí Đạt mới là Đạt.
_Avoid_: trạng thái, verdict, đánh giá

**Trích dẫn**:
Đoạn văn trích nguyên văn từ Văn bản hiệu lực làm căn cứ cho một Kết quả.
_Avoid_: dẫn chứng, bằng chứng

**Kết quả đề xuất**:
Kết quả và Trích dẫn do hệ thống tạo ra; chỉ là bản nháp cho đến khi được Người thẩm định duyệt.
_Avoid_: kết quả AI

**Kết quả đã duyệt**:
Kết quả cuối cùng sau khi Người thẩm định giữ nguyên hoặc sửa Kết quả đề xuất; Kết quả đề xuất vẫn được lưu lại để đối chiếu.

**Người thẩm định**:
Chuyên viên (thường là pháp chế) chịu trách nhiệm duyệt Kết quả đề xuất.
_Avoid_: người dùng, reviewer

**Bộ chuẩn**:
Các Đánh giá tiêu chí kèm Trích dẫn do Người thẩm định điền tay cho một Hợp đồng; được coi là đúng khi đo chất lượng Kết quả đề xuất.
_Avoid_: golden set, đáp án
