"""Trang Thẩm định: chạy Lượt ở tiến trình nền, theo dõi tiến độ, chạy lại phần lỗi (issue 11)."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest
from test_ui_ket_qua import VB, tao_du_lieu

from thamdinh import chay_nen
from thamdinh.chay_nen import TrangThaiChay
from thamdinh.llm import LocalClient
from thamdinh.so_hoa.van_ban import duong_dan_pdf

TRANG = str(Path(__file__).parent.parent / "ui" / "tham_dinh.py")


@pytest.fixture
def khoi_chay(monkeypatch):
    """Thay tiến trình nền bằng bản ghi lại đối số; máy chủ model coi như đã sẵn sàng."""
    goi = []
    monkeypatch.setattr(chay_nen, "khoi_chay", lambda doi_so, thu_muc: goi.append(doi_so))
    monkeypatch.setattr(chay_nen, "trang_thai", lambda thu_muc: None)
    monkeypatch.setattr(LocalClient, "san_sang", lambda self: True)
    return goi


@pytest.fixture
def du_lieu(tmp_path, monkeypatch):
    monkeypatch.setenv("THAMDINH_DATA_DIR", str(tmp_path))
    return tmp_path, tao_du_lieu(tmp_path)


def mo() -> AppTest:
    return AppTest.from_file(TRANG, default_timeout=30).run()


def test_chay_tham_dinh_moi_o_tien_trinh_nen(du_lieu, khoi_chay):
    thu_muc, _ = du_lieu
    at = mo()

    at.segmented_control(key="che_do").set_value("truy_xuat")
    at.button(key="chay").click().run()

    assert not at.exception
    doi_so = khoi_chay[0]
    assert doi_so[0] == str(duong_dan_pdf(VB.hash_pdf, thu_muc))
    assert Path(doi_so[doi_so.index("--checklist") + 1]).name == "dau-ra-v1.1.yaml"
    assert doi_so[doi_so.index("--che-do") + 1] == "truy_xuat"


def test_may_chu_model_chua_chay_thi_khong_khoi_chay(du_lieu, khoi_chay, monkeypatch):
    monkeypatch.setattr(LocalClient, "san_sang", lambda self: False)
    at = mo()

    at.button(key="chay").click().run()

    assert khoi_chay == []
    assert any("llama-server" in e.value for e in at.error)


def test_luot_co_muc_loi_hien_loi_va_chay_lai_phan_loi(du_lieu, khoi_chay):
    _, ma = du_lieu
    at = mo()

    assert at.selectbox(key="luot_chay_lai").value == ma
    assert any("Mục 7" in e.value and "JSON sai" in e.value for e in at.error)

    at.button(key="chay_lai").click().run()

    doi_so = khoi_chay[0]
    assert doi_so[doi_so.index("--tiep-tuc") + 1] == ma
    assert "--chi-muc" not in doi_so


def test_chon_them_muc_da_co_ket_qua_de_chay_lai(du_lieu, khoi_chay):
    at = mo()

    at.multiselect(key="chay_lai_them").set_value([14, 2]).run()
    assert any("tạo Lượt mới" in c.value for c in [*at.caption, *at.info, *at.warning])
    at.button(key="chay_lai").click().run()

    doi_so = khoi_chay[0]
    assert doi_so[doi_so.index("--chi-muc") + 1] == "2,14"


def test_dang_chay_thi_hien_tien_do_va_khong_cho_chay_them(du_lieu, khoi_chay, monkeypatch):
    thu_muc, ma = du_lieu
    monkeypatch.setattr(chay_nen, "trang_thai", lambda thu_muc: TrangThaiChay(
        True, 4242, ("x.pdf",), "2026-10-30T10:15:00", thu_muc / "nhat-ky" / "a.log", ma,
        ("[ 12.5 phút] Mục 8/17",),
    ))
    at = mo()

    assert not at.exception
    assert any("16/17" in i.value for i in at.info)  # Lượt mẫu có 16 Mục đã có kết quả
    assert any("Mục 8/17" in c.value for c in at.code)
    assert at.button(key="chay").disabled
    assert at.button(key="chay_lai").disabled
