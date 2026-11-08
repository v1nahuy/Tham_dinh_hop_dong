"""Đọc lớp text của PDF và đánh giá có dùng được không."""

import ctypes
from dataclasses import dataclass

import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_c

from thamdinh.so_hoa.cau_truc import Dong

CHU_VIET = set(
    "aàáạảãâầấậẩẫăằắặẳẵeèéẹẻẽêềếệểễiìíịỉĩoòóọỏõôồốộổỗơờớợởỡuùúụủũưừứựửữyỳýỵỷỹđ"
    "bcdfghjklmnpqrstvwxz"
)
CO_DAU = CHU_VIET - set("abcdefghijklmnopqrstuvwxyz")
# Ký hiệu Latin-1 hợp lệ trong hợp đồng; các ký tự khác trong dải U+00A0–U+024F là dấu hiệu sai bảng mã.
KY_HIEU_HOP_LE = set(" §°±×²³µ·«»¼½¾")

TOI_THIEU_CHU = 30
NGUONG_KY_TU_LOI = 0.005
NGUONG_KY_TU_LA = 0.02
NGUONG_CO_DAU = 0.05


@dataclass(frozen=True)
class DanhGiaLopText:
    dung_lop_text: bool
    ly_do: str | None
    ty_le_co_dau: float
    ty_le_ky_tu_la: float
    ty_le_ky_tu_loi: float


def danh_gia_lop_text(van_ban: str) -> DanhGiaLopText:
    """Đo chất lượng lớp text của một trang; không đạt thì trang phải đi qua OCR."""
    chu = [c.lower() for c in van_ban if c.isalpha()]
    so_chu = max(len(chu), 1)
    co_dau = sum(c in CO_DAU for c in chu) / so_chu
    la = sum(
        " " <= c <= "ɏ" and c.lower() not in CHU_VIET and c not in KY_HIEU_HOP_LE for c in van_ban
    ) / so_chu
    loi = van_ban.count("�") / max(len(van_ban), 1)

    if len(chu) < TOI_THIEU_CHU:
        ly_do = f"gần như không có chữ ({len(chu)} chữ cái)"
    elif loi > NGUONG_KY_TU_LOI:
        ly_do = f"ký tự lỗi � chiếm {loi:.1%}"
    elif la > NGUONG_KY_TU_LA:
        ly_do = f"ký tự lạ (sai bảng mã) chiếm {la:.1%}"
    elif co_dau < NGUONG_CO_DAU:
        ly_do = f"thiếu dấu tiếng Việt (chữ có dấu chỉ chiếm {co_dau:.1%})"
    else:
        ly_do = None
    return DanhGiaLopText(ly_do is None, ly_do, co_dau, la, loi)

# Kênh màu lớn nhất dưới ngưỡng này coi là chữ/nét đen (không phải redline).
NGUONG_DEN = 50
# Vị trí nét ngang tính theo chiều cao ô ký tự: gần đáy là gạch chân, giữa là gạch ngang.
GACH_CHAN_TOI_DA = 0.2
GACH_NGANG_TOI_DA = 0.75
# Chữ thân bài (ô bảng) có thể lố qua mép khung comment: ký tự cùng dòng, cách ký tự thân bài vừa đọc không quá khoảng
# này (điểm) vẫn là thân bài. Đo trên TOSS: phần lố liền sát (khe 0–2 điểm), chữ comment cùng dòng cách gần 500 điểm.
KHE_LIEN_MACH = 3.0


@dataclass(frozen=True)
class TrangLopText:
    dong: list[Dong]
    so_doan_redline: int
    co_khung_comment: bool


def doc_trang(trang: pdfium.PdfPage, so_trang: int) -> TrangLopText:
    """Đọc lớp text một trang: bỏ khung comment, gắn nhãn [xóa: …] / [thêm: …] / [sửa: …] cho redline."""
    rong, cao = trang.get_size()
    khung_comment, net_ngang = _quet_hinh(trang, rong, cao)
    tp = trang.get_textpage()

    ky_tu = []  # (chữ, hộp, nhãn)
    co_comment = False
    truoc = None  # hộp của ký tự thân bài vừa giữ
    for i in range(pdfium_c.FPDFText_CountChars(tp)):
        chu = chr(pdfium_c.FPDFText_GetUnicode(tp, i))
        hop = _hop_ky_tu(tp, i)
        if (
            khung_comment is not None and hop and (hop[0] + hop[2]) / 2 >= khung_comment
            and not _lien_mach(hop, truoc)
        ):
            co_comment = co_comment or bool(chu.strip())
            truoc = None
            continue
        if hop and chu.strip():
            truoc = hop
        nhan = _nhan_redline(tp, i, hop, net_ngang) if chu.strip() else None
        ky_tu.append((chu, hop, nhan))

    dong, so_doan = _ghep_dong(ky_tu, so_trang)
    return TrangLopText(dong, so_doan, co_comment)


def _lien_mach(hop, truoc) -> bool:
    """Ký tự cùng dòng với ký tự thân bài vừa giữ và nối tiếp sát nó."""
    return truoc is not None and hop[1] < truoc[3] and truoc[1] < hop[3] and hop[0] - truoc[2] <= KHE_LIEN_MACH


def _quet_hinh(trang, rong: float, cao: float) -> tuple[float | None, list[tuple[float, float, float]]]:
    """Tìm khung comment (dải nền xám bên phải) và các nét ngang mảnh có màu (gạch ngang/gạch chân redline)."""
    khung = None
    net = []
    for obj in trang.get_objects(filter=[pdfium_c.FPDF_PAGEOBJ_PATH]):
        l, b, r, t = obj.get_bounds()
        mau = _mau(pdfium_c.FPDFPageObj_GetFillColor, obj.raw)
        if (
            t - b > cao * 0.5
            and l > rong * 0.5
            and r >= rong - 2
            and mau[0] == mau[1] == mau[2]
            and 220 <= mau[0] < 255
        ):
            khung = l if khung is None else min(khung, l)
        elif t - b < 1.0 and r - l > 1.0 and max(mau) > NGUONG_DEN:
            net.append((l, r, (b + t) / 2))
    return khung, net


def _mau(ham, *doi_so) -> tuple[int, int, int]:
    r, g, b, a = (ctypes.c_uint() for _ in range(4))
    ham(*doi_so, r, g, b, a)
    return r.value, g.value, b.value


def _hop_ky_tu(tp, i: int) -> tuple[float, float, float, float] | None:
    hop = pdfium_c.FS_RECTF()
    if not pdfium_c.FPDFText_GetLooseCharBox(tp, i, hop):
        return None
    return hop.left, hop.bottom, hop.right, hop.top


def _nhan_redline(tp, i: int, hop, net_ngang) -> str | None:
    if max(_mau(pdfium_c.FPDFText_GetFillColor, tp, i)) <= NGUONG_DEN:
        return None
    if hop is None:
        return "sửa"
    l, b, r, t = hop
    giua = (l + r) / 2
    cao = max(t - b, 1e-6)
    nhan = "sửa"
    for nl, nr, y in net_ngang:
        if nl <= giua <= nr and b - 1 <= y <= t:
            vi_tri = (y - b) / cao
            if GACH_CHAN_TOI_DA < vi_tri <= GACH_NGANG_TOI_DA:
                return "xóa"
            if vi_tri <= GACH_CHAN_TOI_DA:
                nhan = "thêm"
    return nhan


def _ghep_dong(ky_tu, so_trang: int) -> tuple[list[Dong], int]:
    # Khoảng trắng nằm giữa hai ký tự cùng nhãn thì theo nhãn đó, để không cắt vụn một đoạn redline.
    nhan = [n for _, _, n in ky_tu]
    for i, (chu, _, n) in enumerate(ky_tu):
        if not chu.strip() and chu != "\n":
            truoc = nhan[i - 1] if i else None
            sau = next((nhan[j] for j in range(i + 1, len(ky_tu)) if ky_tu[j][0].strip()), None)
            nhan[i] = truoc if truoc == sau else None

    dong: list[Dong] = []
    so_doan = 0
    phan: list[str] = []
    hop_dong: list[float] | None = None
    nhan_hien_tai = None

    def dong_nhan():
        nonlocal nhan_hien_tai
        if nhan_hien_tai is not None:
            phan.append("]")
            nhan_hien_tai = None

    def ket_thuc_dong():
        nonlocal phan, hop_dong
        dong_nhan()
        noi_dung = "".join(phan).strip()
        if noi_dung:
            dong.append(Dong(so_trang, noi_dung, tuple(hop_dong) if hop_dong else None))
        phan, hop_dong = [], None

    for (chu, hop, _), n in zip(ky_tu, nhan):
        if chu in "\r\n":
            if chu == "\n":
                ket_thuc_dong()
            continue
        if n != nhan_hien_tai:
            dong_nhan()
            if n is not None:
                phan.append(f"[{n}: ")
                nhan_hien_tai = n
                so_doan += 1
        phan.append(chu)
        if hop and chu.strip():
            l, b, r, t = hop
            hop_dong = [l, b, r, t] if hop_dong is None else [
                min(hop_dong[0], l), min(hop_dong[1], b), max(hop_dong[2], r), max(hop_dong[3], t)
            ]
    ket_thuc_dong()
    return dong, so_doan
