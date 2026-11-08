"""Danh sách Tiêu chí ba nguồn không thống nhất, gửi pháp chế (issue 15)."""

import io
from dataclasses import replace

import pytest
from docx import Document
from docx.enum.section import WD_ORIENT
from test_so_sanh import chuan, luot, tl
from test_tham_dinh import CHECKLIST, VAN_BAN

from thamdinh.phap_che import ChuaDuBoChuanError, tao_danh_sach_phap_che
from thamdinh.so_sanh import so_sanh_nguon

BIA = {"so_hieu": "Điều 10", "nguyen_van": "Câu này không có trong hợp đồng"}


def so_sanh_du():
    """Bộ chuẩn đủ mọi Tiêu chí: 1.D1 khác cả hai chế độ, 3.D1 hai chế độ khác nhau, còn lại thống nhất."""
    tv = luot()
    tx = luot("truy_xuat", sua_muc={3: {"3.D1": {"danh_gia": "khong_ro", "ly_do": "Không đủ thông tin", "trich_dan": [BIA]}}})
    danh_gia = {t.ma: t.danh_gia for m in tv.muc for t in m.tieu_chi}
    bo = chuan({**danh_gia, "1.D1": "khong_thoa"})
    bo.danh_gia["1.D1"] = replace(bo.danh_gia["1.D1"], trich_dan=("Câu của người điền.",), vi_tri="Trang 12",
                                  ghi_chu="Cần giấy ủy quyền")
    return so_sanh_nguon(CHECKLIST, tv, tx, bo)


@pytest.fixture(scope="module")
def doc():
    return Document(io.BytesIO(tao_danh_sach_phap_che(so_sanh_du(), CHECKLIST, VAN_BAN)))


def hang(doc, ma: str):
    return next(r for r in doc.tables[0].rows if r.cells[0].text == ma)


def test_chi_liet_ke_tieu_chi_khong_thong_nhat_kem_cau_hoi_muc(doc):
    ma = [r.cells[0].text for r in doc.tables[0].rows]

    assert "1.D1" in ma and "3.D1" in ma
    assert "2.D1" not in ma
    assert any(r.cells[0].text.startswith("Mục 3") for r in doc.tables[0].rows)
    assert not any(r.cells[0].text.startswith("Mục 2") for r in doc.tables[0].rows)


def test_moi_nguon_co_danh_gia_va_trich_dan_rieng(doc):
    o = hang(doc, "1.D1").cells

    assert "Thỏa" in o[2].text and "Mức phạt không vượt quá 8%" in o[2].text  # toàn văn
    assert "Thỏa" in o[3].text  # truy xuất
    assert "Không thỏa" in o[4].text and "Câu của người điền." in o[4].text and "Trang 12" in o[4].text
    assert "Cần giấy ủy quyền" in o[4].text


def test_trich_dan_khong_xac_minh_duoc_duoc_danh_dau(doc):
    o = hang(doc, "3.D1").cells

    assert "Không đủ thông tin" in o[3].text
    assert "không xác minh được" in o[3].text


def test_co_cot_trong_cho_ket_luan_phap_che_va_kho_ngang(doc):
    tieu_de = doc.tables[0].rows[0].cells

    assert tieu_de[-1].text == "Kết luận pháp chế"
    assert hang(doc, "1.D1").cells[-1].text == ""
    assert doc.sections[0].orientation == WD_ORIENT.LANDSCAPE


def test_tieu_chi_co_gia_tri_ghi_con_so_cua_tung_nguon():
    tv = luot(sua_muc={7: {"7.D1": tl("thoa", gia_tri=5)}})
    tx = luot("truy_xuat", sua_muc={7: {"7.D1": tl("khong_thoa", gia_tri=12)}})
    danh_gia = {t.ma: t.danh_gia for m in tv.muc for t in m.tieu_chi}

    kq = so_sanh_nguon(CHECKLIST, tv, tx, chuan(danh_gia, gia_tri={"7.D1": 8}))
    doc = Document(io.BytesIO(tao_danh_sach_phap_che(kq, CHECKLIST, VAN_BAN)))

    o = hang(doc, "7.D1").cells
    assert "Giá trị: 5" in o[2].text and "Giá trị: 12" in o[3].text and "Giá trị: 8" in o[4].text


def test_bo_chuan_chua_du_thi_khong_tao_danh_sach():
    kq = so_sanh_nguon(CHECKLIST, luot(), luot("truy_xuat"), chuan({"1.D1": "thoa"}))

    with pytest.raises(ChuaDuBoChuanError, match="1/"):
        tao_danh_sach_phap_che(kq, CHECKLIST, VAN_BAN)
