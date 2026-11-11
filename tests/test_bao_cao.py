"""Báo cáo thẩm định .docx (issue 12)."""

import io
from dataclasses import replace

import pytest
from docx import Document
from docx.oxml.ns import qn
from test_tham_dinh import CHECKLIST, ModelGia
from test_ui_ket_qua import BIA, VB

from thamdinh.bao_cao import so_hop_dong, tao_bao_cao, ten_file_bao_cao
from thamdinh.kho_luot import KetQuaDuyet
from thamdinh.so_hoa.cau_truc import DieuKhoan
from thamdinh.trich_dan import TrichDanDaKiemTra
from thamdinh.tham_dinh import tham_dinh

# ---- S24: số hợp đồng ----


def van_ban_mo_dau(*dong: str):
    return replace(VB, dieu_khoan=[DieuKhoan(0, "Phần mở đầu", "mo_dau", None, None, 1, 1, "\n".join(dong))])


def test_so_hop_dong_o_phan_mo_dau():
    so = so_hop_dong(van_ban_mo_dau("HỢP ĐỒNG CUNG CẤP DỊCH VỤ", "Số: 125/2026/VNA-VTIT", "Căn cứ Bộ luật Dân sự"))
    assert (so.gia_tri, so.canh_bao) == ("125/2026/VNA-VTIT", None)


def test_so_hop_dong_con_de_trong_thi_giu_nguyen_van_kem_canh_bao():
    so = so_hop_dong(van_ban_mo_dau("Số: ……./2026/VNA-VTIT"))
    assert so.gia_tri == "……./2026/VNA-VTIT"
    assert "Không tìm thấy số hợp đồng" in so.canh_bao


def test_khong_co_dong_so_hop_dong():
    so = so_hop_dong(van_ban_mo_dau("HỢP ĐỒNG CUNG CẤP DỊCH VỤ"))
    assert so.gia_tri == ""
    assert "Không tìm thấy số hợp đồng" in so.canh_bao


def test_so_hop_dong_trong_cau_kem_theo_hop_dong_so():
    vb = replace(VB, dieu_khoan=[DieuKhoan(0, "Phụ lục 01", "phu_luc", None, None, 1, 1,
                                           "(Kèm theo Hợp đồng số: 125/2026/VNA-VTIT ký ngày 12/5/2026)")])
    assert so_hop_dong(vb).gia_tri == "125/2026/VNA-VTIT"


# ---- S23: tạo báo cáo ----

LUOT = tham_dinh(
    VB, CHECKLIST,
    ModelGia(loi_muc={7: 2}, sua_muc={1: {"1.D1": {"danh_gia": "thoa", "ly_do": "…", "trich_dan": [BIA]}}}),
    model="qwen3.5",
)
DE_XUAT_2 = LUOT.muc[1].ket_qua.ket_qua
DUYET_2 = "vi_pham" if DE_XUAT_2 != "vi_pham" else "dat"
DUYET = {
    2: KetQuaDuyet(2, DUYET_2, "Ngành nghề chưa đăng ký kinh doanh",
                   (TrichDanDaKiemTra("Điều 10", "Mức phạt không vượt quá 8%", "khop", None),),
                   "Nguyễn Văn A", "2026-10-31T09:30:00", 1),
    3: KetQuaDuyet(3, LUOT.muc[2].ket_qua.ket_qua, "Chỉ sửa giải thích", (), "Nguyễn Văn A", "2026-10-31T09:40:00", 1),
}
NEN = {"dat": "C6EFCE", "luu_y": "FFEB9C", "vi_pham": "FFC7CE"}


@pytest.fixture(scope="module")
def doc():
    du_lieu = tao_bao_cao(LUOT, DUYET, VB, CHECKLIST, "……./2026/VNA-VTIT", "Không tìm thấy số hợp đồng: còn để trống")
    return Document(io.BytesIO(du_lieu))


def toan_van(doc) -> str:
    return "\n".join([p.text for p in doc.paragraphs] + [c.text for t in doc.tables for r in t.rows for c in r.cells])


def bang_muc(doc, so: int):
    return next(t for t in doc.tables if t.cell(0, 0).text.startswith(f"{so}. "))


def hang(bang, nhan: str):
    return next(r for r in bang.rows if r.cells[0].text == nhan)


def nen(o) -> str | None:
    shd = o._tc.tcPr.find(qn("w:shd")) if o._tc.tcPr is not None else None
    return shd.get(qn("w:fill")) if shd is not None else None


def test_thong_tin_hop_dong_o_dau_bao_cao(doc):
    van_ban = toan_van(doc)
    assert "……./2026/VNA-VTIT" in van_ban and "Không tìm thấy số hợp đồng" in van_ban
    assert "VNA" in van_ban  # Khách hàng
    assert "Checklist thẩm định hợp đồng đầu ra V1.1" in van_ban
    assert "31/10/2026" in van_ban  # ngày duyệt gần nhất
    assert "2/17 Mục đã duyệt" in van_ban
    assert "Nguyễn Văn A" in van_ban


def test_moi_muc_mot_bang_theo_bo_cuc_checklist(doc):
    assert sorted(int(t.cell(0, 0).text.split(".")[0]) for t in doc.tables if t.cell(0, 0).text[0].isdigit()) == list(
        range(1, 18))
    b = bang_muc(doc, 1)
    assert b.cell(0, 0).text == "1. Người đại diện ký hợp đồng đã xác định đúng theo phân cấp, ủy quyền ký kết chưa?"
    assert "Người ký phía Công ty là Giám đốc" in hang(b, "Đạt").cells[1].text
    assert [r.cells[0].text for r in b.rows][1:] == ["Đạt", "Lưu ý", "Vi phạm", "Kết quả", "Giải thích", "Trích dẫn"]


def test_o_ket_qua_to_mau_theo_ket_qua(doc):
    o = hang(bang_muc(doc, 2), "Kết quả").cells[1]
    assert nen(o) == NEN[DUYET_2]
    assert "chưa duyệt" not in o.text


def test_muc_chua_duyet_ghi_ro_la_de_xuat(doc):
    o = hang(bang_muc(doc, 4), "Kết quả").cells[1]
    assert "(đề xuất, chưa duyệt)" in o.text
    assert nen(o) == NEN[LUOT.muc[3].ket_qua.ket_qua]
    assert "Chưa đánh giá được" in hang(bang_muc(doc, 7), "Kết quả").cells[1].text


def test_trich_dan_kem_vi_tri(doc):
    assert "“Mức phạt không vượt quá 8%” (Điều 10, trang 1)" in hang(bang_muc(doc, 2), "Trích dẫn").cells[1].text
    assert "(không xác minh được trong Văn bản hiệu lực)" in hang(bang_muc(doc, 1), "Trích dẫn").cells[1].text


def test_phu_luc_chi_gom_muc_doi_muc_ket_qua(doc):
    phu_luc = doc.tables[-1]
    assert phu_luc.cell(0, 0).text == "Mục"
    assert [r.cells[0].text for r in phu_luc.rows[1:]] == ["2"]
    assert "Ngành nghề chưa đăng ký kinh doanh" in phu_luc.rows[1].cells[4].text


def test_ten_file_bao_cao_khong_dau_kem_ngay_tham_dinh():
    assert ten_file_bao_cao(LUOT, DUYET) == "Bao-cao-tham-dinh_HD-TOSS_20261031.docx"


def test_ma_danh_muc_trong_tieu_chi_doi_thanh_ten_de_doc(doc):
    dat = hang(bang_muc(doc, 2), "Đạt").cells[1].text
    assert "danh mục “Ngành nghề kinh doanh đã đăng ký của Công ty”" in dat
    assert "nganh-nghe-dang-ky" not in toan_van(doc)
