"""OCR một trang PDF: RapidOCR (PP-OCRv4, ONNX) phát hiện hộp chữ, VietOCR nhận dạng tiếng Việt.

Redline được gắn nhãn [xóa: …] / [thêm: …] / [sửa: …] tại chỗ, cùng định dạng với lớp text. Model nạp khi dùng lần đầu
(VietOCR từ `models/vietocr/`, RapidOCR có sẵn trong gói PyPI), chỉ chạy trên máy (ADR 0001).
"""

import re
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np
import pypdfium2 as pdfium
import yaml
from PIL import Image, ImageFilter

from thamdinh.so_hoa.anh import Hop, cat_khung_comment, chinh_nghieng, ghep_dong, tim_redline
from thamdinh.so_hoa.cau_truc import Dong

DPI = 300
# Phát hiện hộp chữ trên ảnh thu nhỏ một nửa: nhanh hơn khoảng 3 lần, hộp vẫn đủ chính xác để cắt ở 300 dpi.
THU_NHO_PHAT_HIEN = 2
LE_CAT = 6
# Số hiệu khoản đầu dòng: VietOCR hay mất hoặc thừa dấu chấm ("1.1." thành "11", "4.1." thành "4.1.."), nên mảnh đầu
# mỗi dòng được đọc lại bằng phần nhận dạng của RapidOCR (đọc số tốt hơn). Cụm số đầu dòng của VietOCR được thay bằng
# số hiệu RapidOCR đọc được; chữ phía sau vẫn lấy của VietOCR.
CHI_SO = re.compile(r"^\d+(\.\d+)*\.?$")
SO_HIEU_DAU = re.compile(r"^(\d{1,2}(?:\.\d{1,2})+\.?)(?![\d.])")
CUM_SO_DAU = re.compile(r"^[\d.,]+")
# Nền màu nhạt (highlight vàng, nền cam của đoạn bị xóa) làm VietOCR đọc sai ("294" thành "094"): tô trắng các điểm
# sáng có màu. Chữ màu đậm hơn ngưỡng này nên không bị ảnh hưởng.
NEN_SANG = 180
NEN_LECH_MAU = 40
# Vạch dọc đánh dấu thay đổi ở lề trái: hộp hẹp hơn tỉ lệ này của chiều cao thì không phải chữ.
HOP_HEP = 0.45


class BoOCR(Protocol):
    def phat_hien(self, anh: Image.Image) -> list[Hop]:
        """Các hộp chữ trên ảnh, theo pixel của ảnh đưa vào."""

    def nhan_dang(self, cac_anh: list[Image.Image]) -> list[tuple[str, float]]:
        """Chữ đọc được và độ tin cậy (0–1) của từng ảnh một dòng chữ."""

    def doc_so(self, cac_anh: list[Image.Image]) -> list[str]:
        """Đọc lại các ảnh đầu dòng (để lấy số hiệu khoản) bằng model nhận dạng thứ hai."""


class BoOCRMacDinh:
    """RapidOCR phát hiện + VietOCR nhận dạng, chạy CPU."""

    def __init__(self, thu_muc_model: str | Path, model: str = "vgg_transformer"):
        self._thu_muc = Path(thu_muc_model)
        self._model = model
        self._rapid = None
        self._vietocr = None

    def _rapid_ocr(self):
        if self._rapid is None:
            from rapidocr_onnxruntime import RapidOCR

            self._rapid = RapidOCR()
        return self._rapid

    def _viet_ocr(self):
        if self._vietocr is None:
            Image.ANTIALIAS = Image.LANCZOS  # VietOCR 0.3.12 dùng tên cũ đã bỏ ở Pillow 10
            with warnings.catch_warnings():  # cảnh báo API cũ (pkg_resources, torchvision) trong VietOCR
                warnings.simplefilter("ignore")
                from vietocr.tool.config import Cfg
                from vietocr.tool.predictor import Predictor

            trong_so = self._thu_muc / f"{self._model}.pth"
            if not trong_so.exists():
                raise FileNotFoundError(f"Chưa có model VietOCR {trong_so} (xem docs/cai-ocr.md)")
            cau_hinh = yaml.safe_load((self._thu_muc / "base.yml").read_text(encoding="utf-8"))
            cau_hinh.update(
                yaml.safe_load((self._thu_muc / f"{self._model.replace('_', '-')}.yml").read_text(encoding="utf-8"))
            )
            cfg = Cfg(cau_hinh)
            cfg["weights"] = str(trong_so)
            cfg["device"] = "cpu"
            cfg["cnn"]["pretrained"] = False
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self._vietocr = Predictor(cfg)
        return self._vietocr

    def phat_hien(self, anh: Image.Image) -> list[Hop]:
        hop, _ = self._rapid_ocr()(_bgr(anh), use_det=True, use_cls=False, use_rec=False)
        ra = []
        for diem in hop if hop is not None else []:
            xs = [p[0] for p in diem]
            ys = [p[1] for p in diem]
            ra.append((min(xs), min(ys), max(xs), max(ys)))
        return ra

    def nhan_dang(self, cac_anh: list[Image.Image]) -> list[tuple[str, float]]:
        if not cac_anh:
            return []
        chu, tin_cay = self._viet_ocr().predict_batch(cac_anh, return_prob=True)
        return list(zip(chu, (float(t) for t in tin_cay)))

    def doc_so(self, cac_anh: list[Image.Image]) -> list[str]:
        ra = []
        for anh in cac_anh:
            kq, _ = self._rapid_ocr()(_bgr(anh), use_det=False, use_cls=False, use_rec=True)
            ra.append(kq[0][0] if kq else "")
        return ra


def _bgr(anh: Image.Image) -> np.ndarray:
    return np.ascontiguousarray(np.asarray(anh.convert("RGB"))[:, :, ::-1])


@dataclass(frozen=True)
class TrangOCR:
    dong: list[Dong]
    so_doan_redline: int
    co_khung_comment: bool
    do_tin_cay: float  # trung bình độ tin cậy nhận dạng, theo số ký tự
    goc_nghieng: float


@dataclass
class _Manh:
    dong: int
    hop: int
    anh: Image.Image
    nhan: str | None
    cach_truoc: bool  # có dấu cách với mảnh trước trong cùng hộp
    dau_dong: bool
    chu: str = ""
    tin_cay: float = 0.0


def ocr_trang(trang: pdfium.PdfPage, so_trang: int, bo: BoOCR) -> TrangOCR:
    rong_pt, cao_pt = trang.get_size()
    anh = trang.render(scale=DPI / 72).to_pil().convert("RGB")
    # Chỉnh nghiêng trước: bản scan nghiêng thì dải xám của khung comment cũng xiên, cắt theo cột sẽ bỏ sót.
    anh, goc = chinh_nghieng(anh)
    anh, co_khung = cat_khung_comment(anh)
    anh = _tay_nen_mau(anh)

    # Khử nhiễu (đốm của bản scan) chỉ trên ảnh dùng để phát hiện; nhận dạng và dò redline dùng ảnh gốc.
    nho = anh.resize((anh.width // THU_NHO_PHAT_HIEN, anh.height // THU_NHO_PHAT_HIEN))
    nho = nho.filter(ImageFilter.MedianFilter(3))
    hop = [tuple(v * THU_NHO_PHAT_HIEN for v in h) for h in bo.phat_hien(nho)]
    dong = ghep_dong(_loc_hop(hop))

    manh: list[_Manh] = []
    for i, cac_hop in enumerate(dong):
        for j, (x0, y0, x1, y1) in enumerate(cac_hop):
            khung = (max(0, int(x0) - LE_CAT), max(0, int(y0) - LE_CAT),
                     min(anh.width, int(x1) + LE_CAT), min(anh.height, int(y1) + LE_CAT))
            vung = anh.crop(khung)
            for k, d in enumerate(tim_redline(vung)):
                anh_manh = vung.crop((d.x0, 0, d.x1, vung.height))
                manh.append(_Manh(i, j, anh_manh, d.nhan, d.cach_truoc, j == 0 and k == 0))

    for m, (chu, tin_cay) in zip(manh, bo.nhan_dang([m.anh for m in manh])):
        m.chu, m.tin_cay = chu.strip(), tin_cay
    dau_dong = [m for m in manh if m.dau_dong]
    for m, chu in zip(dau_dong, bo.doc_so([m.anh for m in dau_dong])):
        m.chu = _sua_so_hieu(m.chu, chu.strip())

    ket_qua: list[Dong] = []
    so_doan = 0
    ty_le = 72 / DPI
    for i, cac_hop in enumerate(dong):
        phan = []
        for j in range(len(cac_hop)):
            van_ban_hop = ""
            for m in (m for m in manh if m.dong == i and m.hop == j and m.chu):
                doan = f"[{m.nhan}: {m.chu}]" if m.nhan else m.chu
                so_doan += m.nhan is not None
                van_ban_hop += (" " if m.cach_truoc and van_ban_hop else "") + doan
            if van_ban_hop:
                phan.append(van_ban_hop)
        if not phan:
            continue
        x0 = min(h[0] for h in cac_hop)
        y0 = min(h[1] for h in cac_hop)
        x1 = max(h[2] for h in cac_hop)
        y1 = max(h[3] for h in cac_hop)
        toa_do = (x0 * ty_le, cao_pt - y1 * ty_le, min(x1 * ty_le, rong_pt), cao_pt - y0 * ty_le)
        ket_qua.append(Dong(so_trang, " ".join(phan), toa_do))

    so_ky_tu = sum(len(m.chu) for m in manh)
    do_tin_cay = sum(m.tin_cay * len(m.chu) for m in manh) / so_ky_tu if so_ky_tu else 0.0
    return TrangOCR(ket_qua, so_doan, co_khung, do_tin_cay, goc)


def _tay_nen_mau(anh: Image.Image) -> Image.Image:
    x = np.asarray(anh).copy()
    sang = x @ np.array([0.299, 0.587, 0.114])
    x[(sang > NEN_SANG) & (x.max(2).astype(np.int16) - x.min(2) > NEN_LECH_MAU)] = 255
    return Image.fromarray(x)


def _sua_so_hieu(viet_ocr: str, rapid_ocr: str) -> str:
    if CHI_SO.match(rapid_ocr) and "." in rapid_ocr and not any(c.isalpha() for c in viet_ocr):
        return rapid_ocr
    so_hieu, cum_so = SO_HIEU_DAU.match(rapid_ocr), CUM_SO_DAU.match(viet_ocr)
    if so_hieu and cum_so:
        return so_hieu.group(1) + viet_ocr[cum_so.end() :]
    return viet_ocr


def _loc_hop(hop: list[Hop]) -> list[Hop]:
    """Bỏ hộp không phải chữ: vạch dọc đánh dấu thay đổi ở lề (hẹp và cao hơn hẳn dòng chữ)."""
    if not hop:
        return []
    cao_dong = float(np.median([h[3] - h[1] for h in hop]))
    return [h for h in hop if h[3] - h[1] <= 2.5 * cao_dong and (h[2] - h[0]) >= HOP_HEP * (h[3] - h[1])]
