"""Biến thể giả lập scan từ TOSS (issue 14, S26)."""

import io
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium
import pytest
from test_anh_ocr import trang_chu

from thamdinh.bien_the import CAU_HINH, tao_bien_the, tao_pdf_bien_the
from thamdinh.so_hoa.anh import chinh_nghieng
from thamdinh.so_hoa.lop_text import danh_gia_lop_text, doc_trang

TOSS = next((Path(__file__).parent.parent / "Sample").glob("*TOSS*.pdf"))


def test_cac_bien_the_da_chot():
    assert list(CAU_HINH) == ["anh-300", "scan-200-nghieng-1", "scan-200-nghieng-3", "scan-150-xam", "den-trang-200"]


def test_cung_seed_ra_cung_anh():
    ch = CAU_HINH["scan-200-nghieng-3"]
    a, b, c = (tao_bien_the(trang_chu(), ch, seed) for seed in (1, 1, 2))
    assert a.tobytes() == b.tobytes()
    assert a.tobytes() != c.tobytes()


@pytest.mark.parametrize("ma", ["scan-200-nghieng-1", "scan-200-nghieng-3", "scan-150-xam"])
def test_trang_bi_xoay_dung_goc(ma):
    _, goc = chinh_nghieng(tao_bien_the(trang_chu(), CAU_HINH[ma], seed=1))
    assert goc == pytest.approx(CAU_HINH[ma].goc, abs=0.3)


def test_ban_den_trang_chi_con_hai_mau():
    anh = tao_bien_the(trang_chu(), CAU_HINH["den-trang-200"], seed=1)
    assert set(np.unique(np.asarray(anh.convert("L")))) <= {0, 255}


def test_ban_xam_khong_con_mau():
    anh = tao_bien_the(trang_chu(), CAU_HINH["scan-150-xam"], seed=1)
    assert anh.mode == "L"


def test_pdf_bien_the_chi_co_anh_cung_kho_trang(tmp_path):
    ra = tmp_path / "scan.pdf"
    tao_pdf_bien_the(TOSS, CAU_HINH["scan-200-nghieng-3"], ra, seed=1, trang=[2, 3])

    goc, bien_the = pdfium.PdfDocument(TOSS), pdfium.PdfDocument(ra)
    assert len(bien_the) == 2
    assert bien_the[0].get_size() == pytest.approx(goc[1].get_size(), abs=0.5)
    chu = "\n".join(d.noi_dung for d in doc_trang(bien_the[0], 1).dong)
    assert not danh_gia_lop_text(chu).dung_lop_text  # không có lớp text: Số hóa phải đi đường OCR
    assert ra.stat().st_size < 1.5e6  # ảnh JPEG nhúng nguyên, không phình
