"""Trang Số hóa: mở Văn bản đã số hóa, xem theo trang, lọc trang tin cậy thấp, sửa Điều khoản (issue 06)."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from thamdinh.so_hoa import TrangSoHoa, VanBanHieuLuc
from thamdinh.so_hoa.cau_truc import DieuKhoan
from thamdinh.so_hoa.van_ban import luu_van_ban, nap_van_ban

TRANG = str(Path(__file__).parent.parent / "ui" / "so_hoa.py")

VAN_BAN = VanBanHieuLuc(
    hash_pdf="abc123",
    ten_file="HĐ mẫu.pdf",
    trang=[
        TrangSoHoa(1, "ocr", True, ("có redline (1 đoạn đã gắn nhãn)",)),
        TrangSoHoa(2, "lop_text", False, ()),
    ],
    dieu_khoan=[
        DieuKhoan(0, "Điều 1", "dieu", "ĐỐI TƯỢNG", None, 1, 1, "ĐIỀU 1: ĐỐI TƯỢNG"),
        DieuKhoan(1, "1.1", "khoan", None, 0, 1, 2, "1.1. Giá [thêm: 294.000.000] [xóa: 1.918.900.000]"),
        DieuKhoan(2, "1.2", "khoan", None, 0, 2, 2, "1.2. Thời gian thực hiện: 06 tháng"),
    ],
    canh_bao=["Số hiệu '4.1' xuất hiện nhiều lần (2 lần, trang 3)"],
)


@pytest.fixture
def thu_muc(tmp_path, monkeypatch):
    luu_van_ban(VAN_BAN, tmp_path, ban_goc=True)
    monkeypatch.setenv("THAMDINH_DATA_DIR", str(tmp_path))
    return tmp_path


def mo() -> AppTest:
    return AppTest.from_file(TRANG, default_timeout=30).run()


def tieu_de_dieu_khoan(at: AppTest) -> list[str]:
    return [e.label for e in at.expander if not e.label.startswith("Cảnh báo")]


def test_mo_van_ban_da_so_hoa_hien_dieu_khoan_cua_trang(thu_muc):
    at = mo()

    assert not at.exception
    assert at.selectbox(key="van_ban").value == "abc123"
    assert tieu_de_dieu_khoan(at) == ["Điều 1 · ĐỐI TƯỢNG", "1.1"]
    assert any("xuất hiện nhiều lần" in m.value for m in at.markdown)  # cảnh báo cấu trúc

    at.selectbox(key="trang").set_value(2).run()
    assert tieu_de_dieu_khoan(at) == ["1.1", "1.2"]


def test_loc_chi_trang_tin_cay_thap_kem_ly_do(thu_muc):
    at = mo()

    at.checkbox(key="chi_tin_cay_thap").check().run()

    assert at.selectbox(key="trang").options == ["Trang 1 (tin cậy thấp)"]
    assert any("có redline" in w.value for w in at.warning)


def test_sua_dieu_khoan_luu_lai_va_mo_lai_van_thay(thu_muc):
    at = mo()

    at.text_area(key="noi_dung_abc123_1").set_value("1.1. Giá 294.000.000 đồng").run()
    at.button(key="luu_abc123_1").click().run()

    assert not at.error
    assert nap_van_ban("abc123", thu_muc).dieu_khoan[1].noi_dung == "1.1. Giá 294.000.000 đồng"
    lan_sau = mo()
    assert lan_sau.text_area(key="noi_dung_abc123_1").value == "1.1. Giá 294.000.000 đồng"
    assert "1.1 · đã sửa tay" in tieu_de_dieu_khoan(lan_sau)


def test_nhan_sai_bao_loi_va_khong_luu(thu_muc):
    at = mo()

    at.text_area(key="noi_dung_abc123_1").set_value("1.1. Giá [xóa: 1.918.900.000").run()
    at.button(key="luu_abc123_1").click().run()

    assert "thiếu dấu ]" in at.error[0].value
    assert nap_van_ban("abc123", thu_muc) == VAN_BAN


def test_chua_co_van_ban_nao(tmp_path, monkeypatch):
    monkeypatch.setenv("THAMDINH_DATA_DIR", str(tmp_path))
    at = mo()

    assert not at.exception
    assert any("Chưa có Văn bản" in i.value for i in at.info)
