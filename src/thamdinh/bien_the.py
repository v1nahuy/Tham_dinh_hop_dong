"""Biến thể giả lập scan của một PDF (issue 14): render ảnh, xoay, thêm nhiễu, giảm dpi, nén JPEG, ghép thành PDF chỉ
có ảnh (không có lớp text), để đo Bước 1 trên đường OCR. Cùng seed thì ra cùng file."""

import io
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium
from PIL import Image


@dataclass(frozen=True)
class CauHinhBienThe:
    ma: str
    mo_ta: str
    dpi: int
    goc: float  # độ, ngược chiều kim đồng hồ (như PIL.Image.rotate)
    nhieu: float  # độ lệch chuẩn nhiễu Gauss, thang 0–255
    jpeg: int  # chất lượng JPEG khi nhúng vào PDF
    mau: str  # mau | xam | den_trang


CAU_HINH = {
    ch.ma: ch
    for ch in (
        CauHinhBienThe("anh-300", "ảnh 300 dpi, không làm xấu (mốc)", 300, 0.0, 0.0, 95, "mau"),
        CauHinhBienThe("scan-200-nghieng-1", "200 dpi, xoay +1°, nhiễu nhẹ, JPEG 85", 200, 1.0, 6.0, 85, "mau"),
        CauHinhBienThe("scan-200-nghieng-3", "200 dpi, xoay −3°, nhiễu vừa, JPEG 75", 200, -3.0, 12.0, 75, "mau"),
        CauHinhBienThe("scan-150-xam", "150 dpi, xám, xoay +2°, nhiễu mạnh, JPEG 60", 150, 2.0, 20.0, 60, "xam"),
        CauHinhBienThe("den-trang-200", "200 dpi, đen trắng như fax (mất màu redline)", 200, 0.0, 0.0, 95, "den_trang"),
    )
}
NGUONG_DEN_TRANG = 170


def tao_bien_the(anh: Image.Image, ch: CauHinhBienThe, seed: int) -> Image.Image:
    """Làm xấu một ảnh trang (đã render ở `ch.dpi`): xoay, nhiễu, chuyển xám / đen trắng. Chưa nén JPEG."""
    anh = anh.convert("RGB")
    if ch.goc:
        anh = anh.rotate(ch.goc, resample=Image.Resampling.BICUBIC, fillcolor="white")
    if ch.mau != "mau":
        anh = anh.convert("L")
    if ch.nhieu:
        x = np.asarray(anh).astype(np.float32)
        x += np.random.default_rng(seed).normal(0, ch.nhieu, x.shape)
        anh = Image.fromarray(np.clip(x, 0, 255).astype(np.uint8))
    if ch.mau == "den_trang":
        anh = anh.point(lambda v: 255 if v >= NGUONG_DEN_TRANG else 0)
    return anh


def tao_pdf_bien_the(
    pdf_goc: str | Path, ch: CauHinhBienThe, ra: str | Path, seed: int = 1, trang: Collection[int] | None = None
) -> Path:
    """PDF chỉ có ảnh JPEG (nhúng nguyên, không nén lại), cùng khổ trang với bản gốc. `trang`: chỉ lấy các trang này."""
    goc = pdfium.PdfDocument(pdf_goc)
    moi = pdfium.PdfDocument.new()
    bo_dem = []  # pdfium đọc JPEG khi lưu file (inline=False), nên giữ các bộ đệm đến lúc đó
    try:
        for so in trang or range(1, len(goc) + 1):
            trang_goc = goc[so - 1]
            rong, cao = trang_goc.get_size()
            anh = tao_bien_the(trang_goc.render(scale=ch.dpi / 72).to_pil(), ch, seed + so)
            jpeg = io.BytesIO()
            anh.save(jpeg, "JPEG", quality=ch.jpeg)
            jpeg.seek(0)
            bo_dem.append(jpeg)
            trang_moi = moi.new_page(rong, cao)
            hinh = pdfium.PdfImage.new(moi)
            hinh.load_jpeg(jpeg, inline=False, autoclose=False)
            hinh.set_matrix(pdfium.PdfMatrix().scale(rong, cao))
            trang_moi.insert_obj(hinh)
            trang_moi.gen_content()
        Path(ra).parent.mkdir(parents=True, exist_ok=True)
        moi.save(ra)
    finally:
        moi.close()
        goc.close()
    return Path(ra)
