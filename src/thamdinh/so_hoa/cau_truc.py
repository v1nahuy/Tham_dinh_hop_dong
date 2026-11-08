"""Dựng cấu trúc Điều khoản từ các dòng đã số hóa (dùng chung cho lớp text và OCR)."""

import re
from collections import Counter
from dataclasses import dataclass, field

HEADER_FOOTER = re.compile(r"^\s*Trang\s+\d+\s*/\s*\d+\s*$")
DIEU = re.compile(r"^ĐIỀU\s+(\d+)\s*[:.]?\s*(.*)$")
PHU_LUC = re.compile(r"^PHỤ LỤC\s+(\S+)\s*$")
# Mỗi cấp khoản tối đa 2 chữ số, để số tiền như "4.000.000" không bị nhận là khoản.
KHOAN = re.compile(r"^(\d{1,2}(?:\.\d{1,2})+)\.?\s+\S")
MUC_PHU_LUC = re.compile(r"^([A-Z]|[IVX]+)\s*[.\-–]\s+(.*)$")
NHAN_XOA = re.compile(r"\[xóa: [^\]]*\]")
NHAN_GIU = re.compile(r"\[(?:thêm|sửa): ([^\]]*)\]")

# Vùng trên trang: (trang, trái, dưới, phải, trên) theo điểm PDF.
Vung = tuple[int, float, float, float, float]


@dataclass(frozen=True)
class Dong:
    trang: int
    noi_dung: str
    toa_do: tuple[float, float, float, float] | None = None


@dataclass(frozen=True)
class DieuKhoan:
    ma: int
    so_hieu: str
    loai: str  # mo_dau | dieu | khoan | phu_luc | muc_phu_luc
    tieu_de: str | None
    cha: int | None
    trang_bat_dau: int
    trang_ket_thuc: int
    noi_dung: str
    vung: tuple[Vung, ...] = ()


@dataclass(frozen=True)
class KetQuaCauTruc:
    dieu_khoan: list[DieuKhoan]
    canh_bao: list[str]


@dataclass
class _Nut:
    ma: int
    so_hieu: str
    loai: str
    tieu_de: str | None
    cha: int | None
    trang_bat_dau: int
    trang_ket_thuc: int = 0
    dong: list[str] = field(default_factory=list)
    vung: dict[int, list[float]] = field(default_factory=dict)

    def them(self, d: Dong) -> None:
        self.dong.append(d.noi_dung)
        self.trang_ket_thuc = d.trang
        if d.toa_do:
            l, b, r, t = d.toa_do
            v = self.vung.setdefault(d.trang, [l, b, r, t])
            v[:] = [min(v[0], l), min(v[1], b), max(v[2], r), max(v[3], t)]

    def dong_bang(self) -> DieuKhoan:
        return DieuKhoan(
            ma=self.ma,
            so_hieu=self.so_hieu,
            loai=self.loai,
            tieu_de=self.tieu_de,
            cha=self.cha,
            trang_bat_dau=self.trang_bat_dau,
            trang_ket_thuc=self.trang_ket_thuc,
            noi_dung="\n".join(self.dong),
            vung=tuple((trang, *v) for trang, v in sorted(self.vung.items())),
        )


def ban_sach(dong: str) -> str:
    """Bản đã chấp nhận redline của một dòng: bỏ phần [xóa: …], giữ phần [thêm: …] / [sửa: …]."""
    return NHAN_GIU.sub(r"\1", NHAN_XOA.sub("", dong)).strip()


def dung_cau_truc(dong: list[Dong]) -> KetQuaCauTruc:
    nut: list[_Nut] = []
    canh_bao: list[str] = []
    phu_luc: _Nut | None = None
    dieu: _Nut | None = None
    so_dieu: int | None = None
    dieu_truoc: dict[str | None, int] = {}  # Điều cuối cùng theo phạm vi (thân Hợp đồng hoặc từng Phụ lục)
    cho_tieu_de: _Nut | None = None

    def mo(so_hieu: str, loai: str, tieu_de: str | None, cha: _Nut | None, d: Dong) -> _Nut:
        n = _Nut(len(nut), so_hieu, loai, tieu_de, cha.ma if cha else None, d.trang)
        nut.append(n)
        n.them(d)
        return n

    for d in dong:
        if HEADER_FOOTER.match(d.noi_dung):
            continue
        sach = ban_sach(d.noi_dung)
        tien_to = f"Phụ lục {phu_luc.so_hieu.removeprefix('Phụ lục ')}, " if phu_luc else ""

        if cho_tieu_de is not None:
            n, cho_tieu_de = cho_tieu_de, None
            if sach and sach == sach.upper() and any(c.isalpha() for c in sach) and not DIEU.match(sach):
                n.tieu_de = sach
                n.them(d)
                continue

        if m := PHU_LUC.match(sach):
            phu_luc = mo(f"Phụ lục {m[1]}", "phu_luc", None, None, d)
            dieu, so_dieu = None, None
            cho_tieu_de = phu_luc
            continue

        if m := DIEU.match(sach):
            n = int(m[1])
            pham_vi = phu_luc.so_hieu if phu_luc else None
            truoc = dieu_truoc.get(pham_vi)
            if truoc is not None and n != truoc + 1:
                canh_bao.append(f"{tien_to}Điều {n} đứng sau Điều {truoc} (trang {d.trang})")
            dieu_truoc[pham_vi] = n
            dieu = mo(f"{tien_to}Điều {n}", "dieu", m[2].strip() or None, phu_luc, d)
            so_dieu = n
            continue

        if dieu and (m := KHOAN.match(sach)) and int(m[1].split(".")[0]) == so_dieu:
            so_hieu = f"{tien_to}{m[1]}"
            cha = _tim_cha(nut, so_hieu, dieu)
            if cha is dieu and m[1].count(".") > 1:
                canh_bao.append(f"Khoản {so_hieu} không có khoản cha (trang {d.trang})")
            mo(so_hieu, "khoan", None, cha, d)
            continue

        if phu_luc and dieu is None and (m := MUC_PHU_LUC.match(sach)):
            mo(f"{tien_to}Mục {m[1]}", "muc_phu_luc", m[2].strip() or None, phu_luc, d)
            continue

        if not nut:
            mo("Phần mở đầu", "mo_dau", None, None, d)
        else:
            nut[-1].them(d)

    dem = Counter(n.so_hieu for n in nut)
    for so_hieu, lan in dem.items():
        if lan > 1:
            trang = sorted({n.trang_bat_dau for n in nut if n.so_hieu == so_hieu})
            canh_bao.append(f"Số hiệu '{so_hieu}' xuất hiện nhiều lần ({lan} lần, trang {', '.join(map(str, trang))})")

    return KetQuaCauTruc([n.dong_bang() for n in nut], canh_bao)


def _tim_cha(nut: list[_Nut], so_hieu: str, dieu: _Nut) -> _Nut:
    """Khoản cha gần nhất có số hiệu là tiền tố, ví dụ 1.2.1 → 1.2; không có thì là Điều."""
    phan = so_hieu.split(".")
    for do_dai in range(len(phan) - 1, 1, -1):
        tien_to = ".".join(phan[:do_dai])
        for n in reversed(nut[dieu.ma :]):
            if n.so_hieu == tien_to:
                return n
    return dieu
