import pytest

from thamdinh.so_hoa.cau_truc import Dong, dung_cau_truc

# Dòng chép tay từ HĐ TOSS v 12.5.2026 (đã gắn nhãn redline như bước đọc lớp text tạo ra).
TOSS = {
    1: [
        "Trang 1 / 52",
        "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
        "HỢP ĐỒNG DỊCH VỤ",
        "BÊN A: TỔNG CÔNG TY HÀNG KHÔNG VIỆT NAM - CTCP",
    ],
    2: [
        "Trang 2 / 52",
        "ĐIỀU 1: ĐỐI TƯỢNG CỦA HỢP ĐỒNG",
        "1.1. Bên A thuê Dịch vụ “Hệ thống Tối ưu Điều hành khai thác - Transformative",
        "Operations Support System (TOSS) giai đoạn T8/2026-T8/2031” của Bên B.",
        "1.2. Thời gian thực hiện Hợp đồng:",
        "1.2.1. Thời gian triển khai dịch vụ: 06 tháng kể từ ngày HĐ có hiệu lực.",
        "1.2.2. Thời gian thuê dịch vụ: 60 tháng kể từ Ngày đưa vào vận hành.",
        "ĐIỀU 2: THÀNH PHẦN HỢP ĐỒNG",
        "ĐIỀU 3: TRIỂN KHAI HỢP ĐỒNG",
        "Điều 1 và các yêu cầu kỹ thuật tại Phụ lục 02: Yêu cầu kỹ thuật.",
    ],
    3: [
        "Trang 3 / 52",
        "a) Biên bản nghiệm thu đào tạo: Hai Bên thống nhất sẽ ký biên bản nghiệm thu",
        "3.3.2. Nghiệm thu chất lượng Dịch vụ hàng tháng:",
        "ĐIỀU 4: ĐƠN GIÁ, THỜI HẠN VÀ PHƯƠNG THỨC THANH TOÁN",
        "4.1. Chi phí dịch vụ triển khai ban đầu, đơn giá thuê Dịch vụ và kỳ thanh toán",
        "4.1 Bảo đảm thực hiện hợp đồng:",
        "4.3.1. Thời hạn nộp bảo đảm thực hiện hợp đồng: Trong vòng 15 ngày",
        "Giá trị bảo đảm thực hiện hợp đồng: [thêm: 294.000.000] [xóa: 1.918.900.000]",
        "[xóa: 4.3.3.][thêm: 4.3.4.] Trường hợp bảo đảm thực hiện hợp đồng hết hiệu lực",
    ],
    4: [
        "Trang 4 / 52",
        "ĐIỀU 5: BẢN QUYỀN VÀ SỞ HỮU TRÍ TUỆ",
        "5.1. Quyền sở hữu trí tuệ đối với phần mềm thuộc về Bên B.",
    ],
    7: [
        "Trang 7 / 52",
        "ĐIỀU 9. GIẢM TRỪ DỊCH VỤ",
        "9.1. Trường hợp dịch vụ không đạt mức cam kết quy định tại khoản",
    ],
    8: [
        "Trang 8 / 52",
        "8.1 Điều 8, Bên B sẽ giảm trừ phí dịch vụ của tháng có dịch vụ không đạt mức cam kết",
    ],
    13: [
        "Trang 13 / 52",
        "PHỤ LỤC 01",
        "ĐƠN GIÁ DỊCH VỤ VÀ THANH TOÁN",
        "(Kèm theo Hợp đồng số: …….……./2026/VNA-VTIT ký ngày………/……../2026)",
        "A. ĐƠN GIÁ HÀNG HÓA DỊCH VỤ VÀ GIÁ TRỊ HỢP ĐỒNG DỰ KIẾN",
        "2 DV thuê phần mềm Tháng 60 454.848.484,85 27.290.909.091",
    ],
    14: [
        "Trang 14 / 52",
        "B- THANH TOÁN",
        "I DỊCH VỤ TRIỂN KHAI BAN ĐẦU",
        "I.2",
    ],
    43: [
        "Trang 43 / 52",
        "PHỤ LỤC 03",
        "BẢO MẬT THÔNG TIN VÀ XỬ LÝ DỮ LIỆU CÁ NHÂN",
        "ĐIỀU 1: ĐỊNH NGHĨA",
        "1.1. Thông Tin",
        "a. Các thông tin đã hoặc sẽ trở thành thông tin được phổ biến công khai;",
    ],
}


@pytest.fixture(scope="module")
def ket_qua():
    dong = [Dong(trang, noi_dung) for trang, ds in TOSS.items() for noi_dung in ds]
    return dung_cau_truc(dong)


@pytest.fixture(scope="module")
def theo_so_hieu(ket_qua):
    return {dk.so_hieu: dk for dk in ket_qua.dieu_khoan}


def test_nhan_dien_dieu_khoan_phu_luc_theo_thu_tu(ket_qua):
    assert [dk.so_hieu for dk in ket_qua.dieu_khoan] == [
        "Phần mở đầu",
        "Điều 1", "1.1", "1.2", "1.2.1", "1.2.2",
        "Điều 2",
        "Điều 3", "3.3.2",
        "Điều 4", "4.1", "4.1", "4.3.1", "4.3.4",
        "Điều 5", "5.1",
        "Điều 9", "9.1",
        "Phụ lục 01", "Phụ lục 01, Mục A", "Phụ lục 01, Mục B",
        "Phụ lục 03", "Phụ lục 03, Điều 1", "Phụ lục 03, 1.1",
    ]


def test_bo_header_footer_so_trang(ket_qua):
    for dk in ket_qua.dieu_khoan:
        assert "Trang " not in dk.noi_dung


def test_dieu_khoan_cha(ket_qua, theo_so_hieu):
    ma = {dk.ma: dk for dk in ket_qua.dieu_khoan}
    assert ma[theo_so_hieu["1.2.1"].cha].so_hieu == "1.2"
    assert ma[theo_so_hieu["1.2"].cha].so_hieu == "Điều 1"
    assert ma[theo_so_hieu["3.3.2"].cha].so_hieu == "Điều 3"
    assert ma[theo_so_hieu["Phụ lục 01, Mục A"].cha].so_hieu == "Phụ lục 01"
    assert ma[theo_so_hieu["Phụ lục 03, 1.1"].cha].so_hieu == "Phụ lục 03, Điều 1"
    assert theo_so_hieu["Điều 1"].cha is None


def test_tieu_de_va_noi_dung(theo_so_hieu):
    assert theo_so_hieu["Điều 4"].tieu_de == "ĐƠN GIÁ, THỜI HẠN VÀ PHƯƠNG THỨC THANH TOÁN"
    assert theo_so_hieu["Điều 9"].tieu_de == "GIẢM TRỪ DỊCH VỤ"
    assert theo_so_hieu["Phụ lục 01"].tieu_de == "ĐƠN GIÁ DỊCH VỤ VÀ THANH TOÁN"
    assert "BÊN A: TỔNG CÔNG TY HÀNG KHÔNG VIỆT NAM" in theo_so_hieu["Phần mở đầu"].noi_dung
    assert "Operations Support System (TOSS)" in theo_so_hieu["1.1"].noi_dung
    # Điểm a), b) gộp vào Điều khoản chứa nó
    assert "a) Biên bản nghiệm thu đào tạo" in theo_so_hieu["Điều 3"].noi_dung
    assert "a. Các thông tin đã hoặc sẽ" in theo_so_hieu["Phụ lục 03, 1.1"].noi_dung


def test_dong_viec_dan_dieu_khoan_khac_khong_bi_nhan_nham(theo_so_hieu):
    assert "Điều 1 và các yêu cầu kỹ thuật" in theo_so_hieu["Điều 3"].noi_dung
    # Dòng xuống hàng bắt đầu bằng "8.1" nằm trong Điều 9, không phải khoản mới
    assert "8.1 Điều 8, Bên B sẽ giảm trừ" in theo_so_hieu["9.1"].noi_dung
    # Bảng trong Phụ lục không bị tách thành khoản
    assert "2 DV thuê phần mềm" in theo_so_hieu["Phụ lục 01, Mục A"].noi_dung


def test_giu_nhan_redline_trong_noi_dung_va_so_hieu_lay_ban_moi(theo_so_hieu):
    assert "[xóa: 4.3.3.][thêm: 4.3.4.] Trường hợp" in theo_so_hieu["4.3.4"].noi_dung
    assert "[thêm: 294.000.000] [xóa: 1.918.900.000]" in theo_so_hieu["4.3.1"].noi_dung


def test_trang_bat_dau_va_ket_thuc(theo_so_hieu):
    assert (theo_so_hieu["Điều 3"].trang_bat_dau, theo_so_hieu["Điều 3"].trang_ket_thuc) == (2, 3)
    assert (theo_so_hieu["9.1"].trang_bat_dau, theo_so_hieu["9.1"].trang_ket_thuc) == (7, 8)


def test_canh_bao_so_hieu_trung_va_dieu_nhay_coc(ket_qua):
    canh_bao = " | ".join(ket_qua.canh_bao)
    assert "Số hiệu '4.1' xuất hiện nhiều lần" in canh_bao
    assert "Điều 9 đứng sau Điều 5" in canh_bao
