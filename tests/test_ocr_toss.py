"""Test tích hợp OCR (chậm, cần model trong models/vietocr): ép trang 2–4 của TOSS đi đường OCR, so với lớp text.

Chạy: .venv/Scripts/python -m pytest -m ocr
"""

import hashlib
import re
from pathlib import Path

import pypdfium2 as pdfium
import pytest

from thamdinh.do_chat_luong import cer
from thamdinh.settings import load_settings
from thamdinh.so_hoa import so_hoa
from thamdinh.so_hoa.lop_text import doc_trang
from thamdinh.so_hoa.ocr import BoOCRMacDinh, ocr_trang

pytestmark = pytest.mark.ocr

TOSS = next((Path(__file__).parent.parent / "Sample").glob("*TOSS*.pdf"))
TRANG = (2, 3, 4)
CER_TOI_DA = 0.05


class BoOCRNho:
    """Bọc bộ OCR thật, nhớ kết quả theo nội dung ảnh để hai fixture không OCR lại cùng một trang."""

    def __init__(self, bo):
        self._bo = bo
        self._nho = {}

    def _goi(self, ten, anh):
        khoa = (ten, *(hashlib.md5(a.tobytes()).hexdigest() for a in (anh if isinstance(anh, list) else [anh])))
        if khoa not in self._nho:
            self._nho[khoa] = getattr(self._bo, ten)(anh)
        return self._nho[khoa]

    def phat_hien(self, anh):
        return self._goi("phat_hien", anh)

    def nhan_dang(self, cac_anh):
        return self._goi("nhan_dang", cac_anh)

    def doc_so(self, cac_anh):
        return self._goi("doc_so", cac_anh)


@pytest.fixture(scope="module")
def bo_ocr():
    settings = load_settings()
    if not (settings.thu_muc_model_ocr / f"{settings.ocr_model}.pth").exists():
        pytest.skip(f"Chưa có model VietOCR trong {settings.thu_muc_model_ocr}")
    return BoOCRNho(BoOCRMacDinh(settings.thu_muc_model_ocr, settings.ocr_model))


@pytest.fixture(scope="module")
def pdf():
    tai_lieu = pdfium.PdfDocument(TOSS)
    yield tai_lieu
    tai_lieu.close()


@pytest.fixture(scope="module")
def ocr(pdf, bo_ocr):
    return {so: ocr_trang(pdf[so - 1], so, bo_ocr) for so in TRANG}


def van_ban_trang(dong) -> str:
    return "\n".join(d.noi_dung for d in dong)


@pytest.mark.parametrize("so", TRANG)
def test_cer_so_voi_lop_text(pdf, ocr, so):
    goc = van_ban_trang(doc_trang(pdf[so - 1], so).dong)
    assert cer(goc, van_ban_trang(ocr[so].dong)) < CER_TOI_DA


def test_khong_lan_noi_dung_comment(ocr):
    for kq in ocr.values():
        assert kq.co_khung_comment
        assert "Commented" not in van_ban_trang(kq.dong)
        assert "Formatted" not in van_ban_trang(kq.dong)


def test_gan_nhan_redline_trang_3(ocr):
    assert ocr[3].so_doan_redline > 0
    assert "[xóa:" in van_ban_trang(ocr[3].dong)
    assert ocr[2].so_doan_redline == 0


def test_dong_co_toa_do_trong_trang(pdf, ocr):
    rong, cao = pdf[1].get_size()
    for d in ocr[2].dong:
        l, b, r, t = d.toa_do
        assert 0 <= l < r <= rong and 0 <= b < t <= cao


@pytest.fixture(scope="module")
def van_ban(ocr, bo_ocr):
    return so_hoa(TOSS, bo_ocr=bo_ocr, ep_ocr=set(TRANG))


def test_so_hoa_ep_ocr_giu_cau_truc(van_ban):
    trang = {t.so: t for t in van_ban.trang}
    assert {so for so, t in trang.items() if t.nguon == "ocr"} == set(TRANG)
    assert trang[3].tin_cay_thap
    so_hieu = [dk.so_hieu for dk in van_ban.dieu_khoan]
    assert [s for s in so_hieu if re.fullmatch(r"Điều \d+", s)] == [f"Điều {n}" for n in range(1, 16)]
    assert {"1.1", "1.2.2", "2.1.3", "3.3.1", "4.3.1"} <= set(so_hieu)


def test_nhan_xoa_o_khoan_4_3_2(van_ban):
    khoan = next(dk for dk in van_ban.dieu_khoan if dk.so_hieu == "4.3.2")
    assert "[xóa:" in khoan.noi_dung
