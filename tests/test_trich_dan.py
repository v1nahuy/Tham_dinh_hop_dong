import unicodedata

import pytest

from thamdinh.so_hoa import TrangSoHoa, VanBanHieuLuc
from thamdinh.so_hoa.cau_truc import DieuKhoan
from thamdinh.trich_dan import TrichDan, kiem_tra_trich_dan

VAN_BAN = VanBanHieuLuc(
    hash_pdf="x",
    ten_file="x.pdf",
    trang=[TrangSoHoa(3, "lop_text", False, ())],
    dieu_khoan=[
        DieuKhoan(0, "Điều 4", "dieu", "ĐƠN GIÁ", None, 3, 3, "ĐIỀU 4: ĐƠN GIÁ, THỜI HẠN VÀ PHƯƠNG THỨC THANH TOÁN"),
        DieuKhoan(1, "4.3.1", "khoan", None, 0, 3, 3,
                  "4.3.1. Thời hạn nộp bảo đảm thực hiện hợp đồng: Trong vòng 15 ngày kể từ ngày\nký kết hợp đồng."),
        DieuKhoan(2, "4.3.2", "khoan", None, 0, 3, 3,
                  "Giá trị bảo đảm thực hiện hợp đồng: 294.000.000 [xóa: 1.918.900.000 ]\n"
                  "[xóa: 767.560.000 đồn][thêm: đồng][xóa: g] (Bằng chữ: Hai trăm chín mươi tư triệu đồng chẵn./.),"
                  " tương đương 0[thêm: 3][xóa: 2]% giá trị phần dịch vụ triển khai ban đầu."),
        DieuKhoan(3, "Điều 10", "dieu", "PHẠT VI PHẠM", None, 9, 9,
                  "ĐIỀU 10: PHẠT VI PHẠM HỢP ĐỒNG\nBên B chịu phạt “8% giá trị phần nghĩa vụ” bị vi phạm – theo Luật Thương mại."),
        DieuKhoan(4, "4.5", "khoan", None, None, 4, 4,
                  "[sửa: 4.5. Những nội dung thay đổi được gọi là “Yêu cầu ]\n[sửa: thay đổi (CR)”. Bên B thực hiện miễn phí ]\n"
                  "[sửa: các CR.]"),
        DieuKhoan(5, "Mục B", "khoan", None, None, 5, 5,
                  "10.Đầu mối tiếp nhận yêu cầu của Bên B: - Hotline: 0336501838 - Email: [thêm: qa@vtit.vn]"),
    ],
    canh_bao=[],
)


@pytest.mark.parametrize(
    "so_hieu, nguyen_van",
    [
        # Khớp nguyên văn, kể cả khi câu xuống dòng trong Văn bản hiệu lực
        ("4.3.1", "Trong vòng 15 ngày kể từ ngày ký kết hợp đồng."),
        # Trích Điều cha, câu nằm trong khoản con
        ("Điều 4", "Trong vòng 15 ngày kể từ ngày ký kết hợp đồng"),
        # Cùng chữ nhưng khác dạng Unicode (NFD)
        ("4.3.1", unicodedata.normalize("NFD", "Thời hạn nộp bảo đảm thực hiện hợp đồng")),
        # Khác kiểu ngoặc kép và gạch ngang
        ("Điều 10", 'Bên B chịu phạt "8% giá trị phần nghĩa vụ" bị vi phạm - theo Luật Thương mại'),
        # Trích bản đã chấp nhận thay đổi
        ("4.3.2", "Giá trị bảo đảm thực hiện hợp đồng: 294.000.000 đồng (Bằng chữ: Hai trăm chín mươi tư triệu đồng chẵn./.), tương đương 03%"),
        # Trích bản còn nguyên chữ redline
        ("4.3.2", "294.000.000 1.918.900.000 767.560.000 đồnđồngg"),
        # Lược bớt bằng dấu "…"
        ("4.3.1", "Thời hạn nộp bảo đảm … Trong vòng 15 ngày … ký kết hợp đồng"),
        # Số hiệu ghi kèm chữ "khoản"
        ("Khoản 4.3.1", "Trong vòng 15 ngày"),
        # Số hiệu chép kèm dấu "###" đánh dấu Điều khoản trong prompt (Qwen3.5 hay làm vậy)
        ("### 4.3.1", "Trong vòng 15 ngày"),
        ("### Khoản 4.3.1", "Trong vòng 15 ngày"),
        # Câu trích chép cả nhãn sửa đổi
        ("4.3.2", "tương đương 0[thêm: 3]% giá trị phần dịch vụ"),
        ("4.3.2", "tương đương 0[thêm: 3][xóa: 2]% giá trị"),
        # Gộp các dòng [sửa: …] liền nhau thành một nhãn
        ("4.5", "[sửa: 4.5. Những nội dung thay đổi được gọi là “Yêu cầu thay đổi (CR)”.]"),
        # Như trên, nhưng bị lược nên nhãn không đóng
        ("4.5", "[sửa: 4.5. Những nội dung thay đổi được gọi là “Yêu cầu thay đổi (CR)”. Bên B … các CR."),
        # Thêm hoặc bớt dấu cách sát dấu câu so với Hợp đồng
        ("Mục B", "10. Đầu mối tiếp nhận yêu cầu của Bên B: - Hotline: 0336501838 - Email: [thêm: qa@vtit.vn]"),
        ("4.3.1", "4.3.1.Thời hạn nộp bảo đảm thực hiện hợp đồng : Trong vòng 15 ngày"),
    ],
)
def test_trich_dan_khop(so_hieu, nguyen_van):
    kq = kiem_tra_trich_dan(TrichDan(so_hieu, nguyen_van), VAN_BAN)

    assert kq.trang_thai == "khop"


def test_khop_nhung_sai_so_hieu_thi_bao_so_hieu_dung():
    kq = kiem_tra_trich_dan(TrichDan("4.3.1", "tương đương 03% giá trị phần dịch vụ"), VAN_BAN)

    assert kq.trang_thai == "khop_sai_so_hieu"
    assert kq.so_hieu_dung == "4.3.2"


@pytest.mark.parametrize(
    "nguyen_van",
    [
        # Lệch dấu tiếng Việt thật
        "Trong vong 15 ngay ke tu ngay ky ket hop dong",
        # Bịa: con số khác Hợp đồng
        "Trong vòng 30 ngày kể từ ngày ký kết hợp đồng",
        # Bịa hoàn toàn
        "Bên A được miễn trừ mọi trách nhiệm bồi thường",
        # Các đoạn lược bớt đúng chữ nhưng sai thứ tự
        "ký kết hợp đồng … Thời hạn nộp bảo đảm",
        # Bịa, có nhãn cũng không được tính là khớp
        "[sửa: Trong vòng 30 ngày kể từ ngày ký kết hợp đồng",
        "Trong vòng [thêm: 30] ngày kể từ ngày ký kết hợp đồng",
        # Chữ dính liền: chỉ bỏ qua dấu cách sát dấu câu, không bỏ dấu cách giữa hai chữ
        "Trong vòng 15 ngày kể từ ngàyký kết hợp đồng",
        # Trích rỗng
        "",
    ],
)
def test_trich_dan_khong_xac_minh_duoc(nguyen_van):
    kq = kiem_tra_trich_dan(TrichDan("4.3.1", nguyen_van), VAN_BAN)

    assert kq.trang_thai == "khong_xac_minh_duoc"
    assert kq.so_hieu_dung is None


# ---- Vị trí Trích dẫn trên trang (issue 11): tô vùng Điều khoản chứa câu trích ----
from thamdinh.trich_dan import TrichDanDaKiemTra  # noqa: E402
from thamdinh.trich_dan import vung_trich_dan  # noqa: E402

CO_TOA_DO = VanBanHieuLuc(
    hash_pdf="abc",
    ten_file="HĐ.pdf",
    trang=[],
    dieu_khoan=[
        DieuKhoan(0, "Điều 10", "dieu", "PHẠT", None, 9, 10, "ĐIỀU 10: PHẠT", ((9, 70.0, 700.0, 500.0, 712.0),)),
        DieuKhoan(1, "10.1", "khoan", None, 0, 9, 9, "10.1. Mức phạt không vượt quá 8% giá trị",
                  ((9, 70.0, 650.0, 500.0, 698.0),)),
        DieuKhoan(2, "10.2", "khoan", None, 0, 9, 10, "10.2. Bồi thường thiệt hại thực tế",
                  ((9, 70.0, 80.0, 500.0, 120.0), (10, 70.0, 760.0, 500.0, 790.0))),
        DieuKhoan(3, "10.3", "khoan", None, 0, 10, 10, "10.3. Không có tọa độ"),
    ],
    canh_bao=[],
)


def test_vung_cua_dieu_khoan_con_chua_cau_trich():
    td = TrichDanDaKiemTra("Điều 10", "Mức phạt không vượt quá 8%", "khop", None)
    assert vung_trich_dan(td, CO_TOA_DO) == [(9, 70.0, 650.0, 500.0, 698.0)]


def test_sai_so_hieu_thi_to_theo_so_hieu_dung_qua_nhieu_trang():
    td = TrichDanDaKiemTra("Điều 5", "Bồi thường thiệt hại thực tế", "khop_sai_so_hieu", "10.2")
    assert vung_trich_dan(td, CO_TOA_DO) == [(9, 70.0, 80.0, 500.0, 120.0), (10, 70.0, 760.0, 500.0, 790.0)]


def test_cau_trich_trai_qua_nhieu_dieu_khoan_thi_to_ca_pham_vi():
    td = TrichDanDaKiemTra("Điều 10", "8% giá trị … Bồi thường thiệt hại", "khop", None)
    assert [v[0] for v in vung_trich_dan(td, CO_TOA_DO)] == [9, 9, 9, 10]


def test_khong_xac_minh_duoc_hoac_khong_co_toa_do_thi_khong_to():
    assert vung_trich_dan(TrichDanDaKiemTra("Điều 10", "câu bịa", "khong_xac_minh_duoc", None), CO_TOA_DO) == []
    assert vung_trich_dan(TrichDanDaKiemTra("10.3", "Không có tọa độ", "khop", None), CO_TOA_DO) == []
