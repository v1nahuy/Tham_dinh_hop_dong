"""Phép đo chất lượng Bước 1 (issue 14, S27): tỉ lệ lỗi ký tự, tỉ lệ từ có mặt, so sánh cấu trúc với bản đúng."""

import pytest

from thamdinh.do_chat_luong import cer, so_sanh_cau_truc, ty_le_tu
from thamdinh.so_hoa import VanBanHieuLuc
from thamdinh.so_hoa.cau_truc import DieuKhoan


def dk(ma, so_hieu, trang, noi_dung, den=None):
    return DieuKhoan(ma, so_hieu, "khoan", None, None, trang, den or trang, noi_dung)


THAM_CHIEU = VanBanHieuLuc("x", "x.pdf", [], [
    dk(0, "Điều 1", 1, "ĐIỀU 1: ĐỐI TƯỢNG"),
    dk(1, "1.1", 1, "1.1. Bên A thuê Dịch vụ “Hệ thống”"),
    dk(2, "1.2", 2, "1.2. Thời gian thực hiện: 06 tháng"),
    dk(3, "1.3", 2, "1.3. Bảo hành 12 tháng", den=3),  # sang trang 3: ngoài phạm vi đo trang 1–2
], [])


def test_cer_bo_nhan_redline_ngoac_kep_va_khoang_trang():
    assert cer("1.1. Giá [xóa: 1.918] 294", "1.1.Giá 1.918   294") == 0
    assert cer("Bên A thuê “Hệ thống”", "Bên A thuê ?Hệ thống?") == 0
    assert cer("abcd", "abxd") == pytest.approx(0.25)


def test_ty_le_tu_khong_xet_thu_tu():
    assert ty_le_tu("Kế hoạch triển khai 180 ngày", "180 ngày kế hoạch triển khai") == 1
    assert ty_le_tu("một hai ba bốn", "một hai") == 0.5


def test_so_sanh_cau_truc_trong_cac_trang_da_do():
    ocr = [dk(0, "Điều 1", 1, "ĐIỀU 1: ĐỐI TƯỢNG"), dk(1, "1.1", 1, "1.1. Bên A thuê Dịch vụ ?Hệ thông?"),
           dk(2, "12", 2, "12 Thời gian thực hiện: 06 tháng")]  # "1.2." đọc sai thành "12"

    kq = so_sanh_cau_truc(THAM_CHIEU, ocr, trang={1, 2})

    assert (kq.dung, kq.tong) == (2, 3)  # 1.3 sang trang 3 nên không tính
    assert kq.thieu == ["1.2"]
    assert kq.thua == ["12"]
    so_ky_tu = len("ĐIỀU1:ĐỐITƯỢNG") + len("1.1.BênAthuêDịchvụHệthống") + len("1.2.Thờigianthựchiện:06tháng")
    assert kq.cer == pytest.approx((1 + len("1.2.Thờigianthựchiện:06tháng")) / so_ky_tu)  # "thông" sai 1 ký tự
