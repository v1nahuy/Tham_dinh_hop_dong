"""Test tích hợp: số hóa file HĐ TOSS mẫu."""

import re
from pathlib import Path

import pypdfium2 as pdfium
import pytest

from thamdinh.bo_chuan import doc_trich_dan_chuan
from thamdinh.so_hoa import so_hoa
from thamdinh.so_hoa.lop_text import doc_trang
from thamdinh.trich_dan import KHONG_XAC_MINH_DUOC, TrichDan, chuan_hoa, kiem_tra_trich_dan

GOC = Path(__file__).parent.parent
TOSS = next((GOC / "Sample").glob("*TOSS*.pdf"))


@pytest.fixture(scope="module")
def van_ban():
    return so_hoa(TOSS)


@pytest.fixture(scope="module")
def toan_van(van_ban):
    return "\n".join(dk.noi_dung for dk in van_ban.dieu_khoan)


def test_toss_dung_lop_text_cho_moi_trang(van_ban):
    assert len(van_ban.trang) == 52
    assert {t.nguon for t in van_ban.trang} == {"lop_text"}


def test_bo_khung_comment(toan_van):
    assert "Commented [" not in toan_van
    assert "Formatted:" not in toan_van


def test_giu_chu_than_bai_tran_qua_mep_khung_comment():
    """Trang 21 (bảng Phụ lục 02): chữ cuối dòng trong ô bảng lố qua mép khung comment vài điểm."""
    pdf = pdfium.PdfDocument(TOSS)
    chu = chuan_hoa(" ".join(d.noi_dung for d in doc_trang(pdf[20], 21).dong))
    pdf.close()

    assert "mã nguồn hệ thống thuộc quyền sở hữu của Vietnam Airlines" in chu
    assert "sau khi hết thời gian thuê dịch vụ phần mềm" in chu


def test_moi_trich_dan_bo_chuan_co_trong_van_ban(van_ban):
    """Người thẩm định chép nguyên văn từ PDF (eval/chuan/toss.yaml); câu nào không tìm thấy là Văn bản hiệu lực sai."""
    trich_dan = doc_trich_dan_chuan(GOC / "eval" / "chuan" / "toss.yaml")

    khong_thay = {
        (ma, cau) for ma, ds in trich_dan.items() for cau in ds
        if kiem_tra_trich_dan(TrichDan("", cau), van_ban).trang_thai == KHONG_XAC_MINH_DUOC
    }

    assert not khong_thay


def test_danh_dau_trang_co_redline(van_ban):
    trang = {t.so: t for t in van_ban.trang}
    assert trang[3].tin_cay_thap
    assert any("redline" in ly_do for ly_do in trang[3].ly_do)
    assert not trang[9].tin_cay_thap


def test_trang_chi_co_khung_comment_khong_tin_cay_thap_nhung_van_ghi_ly_do(van_ban):
    # Trang 2 có comment, không có redline: comment đã bị bỏ nên không làm text kém tin cậy
    trang_2 = next(t for t in van_ban.trang if t.so == 2)
    assert not trang_2.tin_cay_thap
    assert trang_2.ly_do == ("có khung comment (đã bỏ)",)


def test_gan_nhan_redline_tai_cho(toan_van):
    # Trang 3, khoản 4.3.2: giá trị bảo đảm mới 294.000.000, hai giá trị cũ bị gạch
    assert re.search(r"\[xóa: [^\]]*767\.560\.000", toan_van)
    assert re.search(r"294\.000\.000", toan_van)
    assert "[xóa: 4.3.3.]" in toan_van


def test_nhan_du_dieu_va_phu_luc(van_ban):
    so_hieu = [dk.so_hieu for dk in van_ban.dieu_khoan]
    assert [s for s in so_hieu if re.fullmatch(r"Điều \d+", s)] == [f"Điều {n}" for n in range(1, 16)]
    assert [s for s in so_hieu if re.fullmatch(r"Phụ lục \d+", s)] == [f"Phụ lục 0{n}" for n in range(1, 6)]
    assert "Phụ lục 03, Điều 4" in so_hieu
    assert "4.3.4" in so_hieu


def test_dieu_khoan_co_toa_do(van_ban):
    dieu_1 = next(dk for dk in van_ban.dieu_khoan if dk.so_hieu == "Điều 1")
    assert dieu_1.vung and dieu_1.vung[0][0] == 2
