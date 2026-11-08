import pytest

from thamdinh.so_hoa.lop_text import danh_gia_lop_text

TOT = (
    "4.3.1. Thời hạn nộp bảo đảm thực hiện hợp đồng: Trong vòng 15 ngày kể từ ngày ký kết hợp đồng. "
    "4.3.2. Hình thức bảo đảm thực hiện hợp đồng: Bên B nộp Bảo đảm thực hiện dịch vụ theo hình thức "
    "Thư bảo lãnh (vô điều kiện, không hủy ngang) do Ngân hàng phát hành."
)


def test_lop_text_tieng_viet_tot_thi_dung_lop_text():
    danh_gia = danh_gia_lop_text(TOT)

    assert danh_gia.dung_lop_text
    assert danh_gia.ly_do is None


@pytest.mark.parametrize(
    "van_ban, ly_do",
    [
        # Font TCVN3 không có bảng ánh xạ Unicode
        ("Hîp ®ång dÞch vô gi÷a C«ng ty vµ Kh¸ch hµng vÒ viÖc thuª hÖ thèng tèi ­u ®iÒu hµnh khai th¸c " * 3, "ký tự lạ"),
        # Ký tự thay thế do mất bảng mã
        ("H�p đ�ng d�ch v� gi�a C�ng ty v� Kh�ch h�ng " * 3, "ký tự lỗi"),
        # Bản scan: chỉ còn header do máy in thêm vào
        ("Trang 3 / 52", "gần như không có chữ"),
        # Lớp text mất hết dấu
        ("Hop dong dich vu giua Cong ty va Khach hang ve viec thue he thong toi uu dieu hanh khai thac " * 3, "thiếu dấu"),
    ],
)
def test_lop_text_kem_thi_chuyen_ocr(van_ban, ly_do):
    danh_gia = danh_gia_lop_text(van_ban)

    assert not danh_gia.dung_lop_text
    assert ly_do in danh_gia.ly_do
