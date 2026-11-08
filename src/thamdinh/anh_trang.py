"""Ảnh một trang PDF để xem trên giao diện, có thể tô các vùng (vị trí Trích dẫn)."""

from collections.abc import Iterable
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageDraw

from thamdinh.so_hoa.cau_truc import Vung

DPI_XEM = 110
MAU_TO = (255, 200, 0, 70)
MAU_VIEN = (230, 120, 0, 255)
LE = 3  # điểm PDF: tọa độ Điều khoản lấy theo hộp ký tự, nới ra để không cắt sát chữ


def anh_trang(pdf: str | Path, so: int, vung: Iterable[Vung] = (), dpi: int = DPI_XEM) -> Image.Image:
    """Render trang `so` (đếm từ 1); tô các vùng (trang, trái, dưới, phải, trên theo điểm PDF) nằm trên trang đó."""
    tai_lieu = pdfium.PdfDocument(pdf)
    try:
        trang = tai_lieu[so - 1]
        cao = trang.get_height()
        anh = trang.render(scale=dpi / 72).to_pil().convert("RGB")
    finally:
        tai_lieu.close()
    k = dpi / 72
    ve = ImageDraw.Draw(anh, "RGBA")
    for t, trai, duoi, phai, tren in vung:
        if t == so:
            ve.rectangle(
                ((trai - LE) * k, (cao - tren - LE) * k, (phai + LE) * k, (cao - duoi + LE) * k),
                fill=MAU_TO, outline=MAU_VIEN, width=3,
            )
    return anh
