"""OCR một trang scan giả lập (issue 14, S28): chậm, cần model trong models/vietocr.

Chạy: .venv/Scripts/python -m pytest -m ocr
"""

from pathlib import Path

import pypdfium2 as pdfium
import pytest

from thamdinh.bien_the import CAU_HINH, tao_pdf_bien_the
from thamdinh.do_chat_luong import cer
from thamdinh.settings import load_settings
from thamdinh.so_hoa.lop_text import doc_trang
from thamdinh.so_hoa.ocr import BoOCRMacDinh, ocr_trang

pytestmark = pytest.mark.ocr

TOSS = next((Path(__file__).parent.parent / "Sample").glob("*TOSS*.pdf"))


@pytest.fixture(scope="module")
def ket_qua(tmp_path_factory):
    settings = load_settings()
    if not (settings.thu_muc_model_ocr / f"{settings.ocr_model}.pth").exists():
        pytest.skip(f"Chưa có model VietOCR trong {settings.thu_muc_model_ocr}")
    ra = tao_pdf_bien_the(TOSS, CAU_HINH["scan-200-nghieng-3"], tmp_path_factory.mktemp("bien-the") / "scan.pdf",
                          trang=[3])
    pdf = pdfium.PdfDocument(ra)
    kq = ocr_trang(pdf[0], 3, BoOCRMacDinh(settings.thu_muc_model_ocr, settings.ocr_model))
    goc = pdfium.PdfDocument(TOSS)
    return kq, "\n".join(d.noi_dung for d in doc_trang(goc[2], 3).dong)


def test_do_duoc_goc_nghieng_cua_ban_scan(ket_qua):
    kq, _ = ket_qua
    assert kq.goc_nghieng == pytest.approx(-3, abs=0.3)


def test_cer_trang_scan_nghieng(ket_qua):
    kq, goc = ket_qua
    assert cer(goc, "\n".join(d.noi_dung for d in kq.dong)) < 0.10


def test_van_gan_nhan_xoa_va_khong_lan_comment(ket_qua):
    kq, _ = ket_qua
    van_ban = "\n".join(d.noi_dung for d in kq.dong)
    assert "[xóa:" in van_ban
    assert "Commented" not in van_ban and "Formatted" not in van_ban
