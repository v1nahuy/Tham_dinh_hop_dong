"""Trang Kết quả: mở Lượt, bảng 17 Mục, chi tiết Mục, xem vị trí Trích dẫn, duyệt (issue 11)."""

from dataclasses import replace
from pathlib import Path

import pypdfium2 as pdfium
import pytest
from streamlit.testing.v1 import AppTest
from test_tham_dinh import CHECKLIST, VAN_BAN, ModelGia

from thamdinh.kho_luot import KhoLuot
from thamdinh.so_hoa.van_ban import duong_dan_pdf, luu_van_ban
from thamdinh.tham_dinh import tham_dinh

TRANG = str(Path(__file__).parent.parent / "ui" / "ket_qua.py")
BIA = {"so_hieu": "Điều 1", "nguyen_van": "Câu này không có trong hợp đồng"}

# Điều 10 nằm ở trang 1 và có tọa độ, để xem được vị trí Trích dẫn trên ảnh trang
DIEU_10 = replace(VAN_BAN.dieu_khoan[1], trang_bat_dau=1, trang_ket_thuc=1, vung=((1, 70.0, 650.0, 500.0, 712.0),))
VB = replace(VAN_BAN, dieu_khoan=[VAN_BAN.dieu_khoan[0], DIEU_10])


def tao_du_lieu(thu_muc: Path) -> str:
    """Thư mục dữ liệu có một Lượt (Mục 7 lỗi, Mục 1 có Trích dẫn bịa), Văn bản hiệu lực và PDF một trang."""
    luu_van_ban(VB, thu_muc, ban_goc=True)
    pdf = pdfium.PdfDocument.new()
    pdf.new_page(595, 842)
    duong_dan_pdf(VB.hash_pdf, thu_muc).parent.mkdir(parents=True, exist_ok=True)
    pdf.save(duong_dan_pdf(VB.hash_pdf, thu_muc))
    kho = KhoLuot(thu_muc)
    model = ModelGia(loi_muc={7: 2}, sua_muc={1: {"1.D1": {"danh_gia": "thoa", "ly_do": "…", "trich_dan": [BIA]}}})
    return tham_dinh(VB, CHECKLIST, model, model="qwen3.5", sau_moi_buoc=kho.luu).ma


@pytest.fixture
def du_lieu(tmp_path, monkeypatch):
    monkeypatch.setenv("THAMDINH_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("THAMDINH_NGUOI_DUYET", "")
    return tmp_path, tao_du_lieu(tmp_path)


def mo() -> AppTest:
    return AppTest.from_file(TRANG, default_timeout=30).run()


def bang(at: AppTest):
    return at.dataframe[0].value.set_index("Mục")


def test_mo_luot_hien_bang_17_muc(du_lieu):
    _, ma = du_lieu
    at = mo()

    assert not at.exception
    assert at.selectbox(key="luot").value == ma
    b = bang(at)
    assert list(b.index) == list(range(1, 18))
    assert b.loc[7, "Đề xuất"] == "Chưa đánh giá được" and "JSON sai" in b.loc[7, "Lỗi"]
    assert b.loc[1, "Trích dẫn không xác minh được"] == 1
    assert b.loc[2, "Đã duyệt"] == ""


def test_chi_tiet_muc_danh_dau_trich_dan_khong_xac_minh_duoc(du_lieu):
    at = mo()

    noi_dung = " ".join(m.value for m in at.markdown)
    assert "Câu này không có trong hợp đồng" in noi_dung
    assert ":red[không xác minh được]" in noi_dung


def test_bam_xem_trang_hien_anh_trang_co_vung_trich(du_lieu):
    at = mo()

    at.button(key="xem_2_0_0").click().run()

    assert not at.exception
    assert len(at.image) == 1


def test_duyet_muc_mo_lai_van_thay_ca_de_xuat_va_da_duyet(du_lieu):
    thu_muc, ma = du_lieu
    at = mo()
    de_xuat = bang(at).loc[2, "Đề xuất"]

    at.text_input(key="nguoi_duyet").set_value("Nguyễn Văn A")
    at.segmented_control(key=f"kq_{ma}_2").set_value("vi_pham")
    at.text_area(key=f"giai_thich_{ma}_2").set_value("Ngành nghề chưa đăng ký")
    at.form_submit_button(key=f"luu_duyet_{ma}_2").click().run()

    assert not at.exception
    assert not [e for e in at.error if "lưu" in e.value]  # lỗi sẵn có của Mục 7 thì vẫn hiện
    duyet = KhoLuot(thu_muc).nap_duyet(ma)[2]
    assert (duyet.ket_qua, duyet.giai_thich, duyet.nguoi_duyet) == ("vi_pham", "Ngành nghề chưa đăng ký", "Nguyễn Văn A")
    lan_sau = mo()
    assert bang(lan_sau).loc[2, "Đề xuất"] == de_xuat
    assert bang(lan_sau).loc[2, "Đã duyệt"] == "Vi phạm"
    assert any("Phiên bản 1" in m.value and "Nguyễn Văn A" in m.value for m in lan_sau.markdown)  # lịch sử duyệt


def test_chua_co_nguoi_duyet_thi_khong_luu(du_lieu):
    thu_muc, ma = du_lieu
    at = mo()

    at.segmented_control(key=f"kq_{ma}_2").set_value("vi_pham")
    at.form_submit_button(key=f"luu_duyet_{ma}_2").click().run()

    assert any("người thẩm định" in e.value for e in at.error)
    assert KhoLuot(thu_muc).nap_duyet(ma) == {}


def test_chua_co_luot_nao(tmp_path, monkeypatch):
    monkeypatch.setenv("THAMDINH_DATA_DIR", str(tmp_path))
    at = mo()

    assert not at.exception
    assert any("Chưa có Lượt thẩm định" in i.value for i in at.info)


def test_tai_bao_cao_docx(du_lieu, monkeypatch):
    import io

    import streamlit as st
    from docx import Document

    goc, da_goi = st.download_button, []

    def ghi_lai(*args, **kwargs):  # AppTest không đọc được file của nút tải xuống, nên ghi lại đối số
        da_goi.append(kwargs)
        return goc(*args, **kwargs)

    monkeypatch.setattr(st, "download_button", ghi_lai)
    at = mo()

    assert not at.exception
    assert at.text_input(key=f"so_hop_dong_{du_lieu[1]}").value == ""
    assert any("Không tìm thấy số hợp đồng" in w.value for w in at.warning)
    nut = da_goi[-1]
    assert nut["file_name"].startswith("Bao-cao-tham-dinh_HD-TOSS_") and nut["file_name"].endswith(".docx")
    bang_dau = Document(io.BytesIO(nut["data"])).tables[0]
    assert bang_dau.cell(0, 0).text == "Số hợp đồng"


def lam_hong_luot(thu_muc, ma: str) -> None:
    """Như Lượt lưu bằng code thử nghiệm đã revert: thêm một trường cấp Lượt mà code hiện tại không biết."""
    import json
    import sqlite3

    with sqlite3.connect(KhoLuot(thu_muc).duong_dan) as db:
        (chung,) = db.execute("SELECT chung FROM luot WHERE ma = ?", (ma,)).fetchone()
        db.execute("UPDATE luot SET chung = ? WHERE ma = ?", (json.dumps({**json.loads(chung), "suy_luan": True}), ma))


def test_luot_sai_dinh_dang_thi_bao_loi_ro_rang_khong_vo_trang(du_lieu):
    thu_muc, ma = du_lieu
    lam_hong_luot(thu_muc, ma)

    at = mo()

    assert not at.exception
    assert any("suy_luan" in e.value and ma in e.value for e in at.error)
