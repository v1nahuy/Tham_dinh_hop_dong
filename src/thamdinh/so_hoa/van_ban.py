"""Văn bản hiệu lực và việc lưu/nạp theo hash file PDF.

Mỗi lần lưu ghi bản mới nhất (`<hash_pdf>.json`) và một bản theo nội dung (`<hash_pdf>-<hash_noi_dung>.json`), để
Lượt thẩm định chạy trước khi sửa tay vẫn mở lại được đúng văn bản lúc chạy. Bản do Số hóa tạo ra còn được ghi thêm
thành bản gốc (`<hash_pdf>-goc.json`), để biết Điều khoản nào đã sửa tay.
"""

import hashlib
import json
import re
import shutil
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from thamdinh.so_hoa.cau_truc import DieuKhoan

THU_MUC_CON = "van-ban-hieu-luc"
THU_MUC_PDF = "pdf"


@dataclass(frozen=True)
class TrangSoHoa:
    so: int
    nguon: str  # lop_text | ocr
    tin_cay_thap: bool
    ly_do: tuple[str, ...]


@dataclass(frozen=True)
class VanBanHieuLuc:
    hash_pdf: str
    ten_file: str
    trang: list[TrangSoHoa]
    dieu_khoan: list[DieuKhoan]
    canh_bao: list[str]


def hash_noi_dung(van_ban: VanBanHieuLuc) -> str:
    """Mã nội dung Văn bản hiệu lực (trang, Điều khoản, cảnh báo); không phụ thuộc tên file."""
    d = asdict(van_ban)
    d.pop("ten_file")
    return hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def _duong_dan(hash_pdf: str, thu_muc: Path, hash_nd: str | None = None) -> Path:
    ten = f"{hash_pdf}-{hash_nd[:16]}" if hash_nd else hash_pdf
    return Path(thu_muc) / THU_MUC_CON / f"{ten}.json"


def _duong_dan_goc(hash_pdf: str, thu_muc: Path) -> Path:
    return Path(thu_muc) / THU_MUC_CON / f"{hash_pdf}-goc.json"


def luu_van_ban(van_ban: VanBanHieuLuc, thu_muc: str | Path, ban_goc: bool = False) -> Path:
    """Lưu thành bản đang dùng; `ban_goc=True` (khi Số hóa) thì ghi cả bản gốc."""
    noi_dung = json.dumps(asdict(van_ban), ensure_ascii=False, indent=1)
    file = _duong_dan(van_ban.hash_pdf, Path(thu_muc))
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(noi_dung, encoding="utf-8")
    _duong_dan(van_ban.hash_pdf, Path(thu_muc), hash_noi_dung(van_ban)).write_text(noi_dung, encoding="utf-8")
    if ban_goc:
        _duong_dan_goc(van_ban.hash_pdf, Path(thu_muc)).write_text(noi_dung, encoding="utf-8")
    return file


def duong_dan_pdf(hash_pdf: str, thu_muc: str | Path) -> Path:
    return Path(thu_muc) / THU_MUC_PDF / f"{hash_pdf}.pdf"


def luu_pdf(pdf: str | Path, hash_pdf: str, thu_muc: str | Path) -> Path:
    """Chép file PDF vào thư mục dữ liệu (ảnh trang ở UI, báo cáo); chỉ nằm trên máy (ADR 0001)."""
    dich = duong_dan_pdf(hash_pdf, thu_muc)
    if not dich.exists():
        dich.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(pdf, dich)
    return dich


def nap_van_ban(hash_pdf: str, thu_muc: str | Path, hash_nd: str | None = None) -> VanBanHieuLuc | None:
    """Bản mới nhất; có `hash_nd` thì đúng bản có nội dung đó (Văn bản hiệu lực mà một Lượt đã dùng)."""
    return _doc(_duong_dan(hash_pdf, Path(thu_muc), hash_nd))


def nap_van_ban_goc(hash_pdf: str, thu_muc: str | Path) -> VanBanHieuLuc | None:
    """Bản do lần Số hóa gần nhất tạo ra, chưa sửa tay (None với văn bản số hóa trước khi có bản gốc)."""
    return _doc(_duong_dan_goc(hash_pdf, Path(thu_muc)))


def _doc(file: Path) -> VanBanHieuLuc | None:
    if not file.is_file():
        return None
    d = json.loads(file.read_text(encoding="utf-8"))
    return VanBanHieuLuc(
        hash_pdf=d["hash_pdf"],
        ten_file=d["ten_file"],
        trang=[TrangSoHoa(t["so"], t["nguon"], t["tin_cay_thap"], tuple(t["ly_do"])) for t in d["trang"]],
        dieu_khoan=[
            DieuKhoan(**{**dk, "vung": tuple(tuple(v) for v in dk["vung"])}) for dk in d["dieu_khoan"]
        ],
        canh_bao=d["canh_bao"],
    )


NHAN_REDLINE = ("xóa", "thêm", "sửa")
DANG_NHAN = re.compile(r"\[(\w+): ")


def sua_dieu_khoan(van_ban: VanBanHieuLuc, ma: int, noi_dung: str) -> VanBanHieuLuc:
    """Văn bản hiệu lực mới với nội dung Điều khoản `ma` đã sửa tay; nội dung sai định dạng nhãn thì báo ValueError."""
    if not any(dk.ma == ma for dk in van_ban.dieu_khoan):
        raise KeyError(f"Không có Điều khoản mã {ma}")
    noi_dung = noi_dung.strip()
    if not noi_dung:
        raise ValueError("Nội dung Điều khoản không được rỗng")
    _kiem_tra_nhan(noi_dung)
    return replace(
        van_ban, dieu_khoan=[replace(dk, noi_dung=noi_dung) if dk.ma == ma else dk for dk in van_ban.dieu_khoan]
    )


def _kiem_tra_nhan(noi_dung: str) -> None:
    """Ngoặc vuông phải đóng mở đủ, không lồng nhau; dạng `[tên: …]` thì tên phải là nhãn redline. Ngoặc thường của
    hợp đồng (như "[●]") vẫn hợp lệ."""
    mo = None
    for i, c in enumerate(noi_dung):
        if c == "[":
            if mo is not None:
                raise ValueError(f"Ngoặc vuông lồng nhau ở vị trí {i + 1}: …{noi_dung[max(0, i - 20) : i + 20]}…")
            mo = i
            if (nhan := DANG_NHAN.match(noi_dung, i)) and nhan.group(1) not in NHAN_REDLINE:
                raise ValueError(
                    f"Không có nhãn '{nhan.group(1)}', chỉ dùng [{': …], ['.join(NHAN_REDLINE)}: …]"
                )
        elif c == "]":
            if mo is None:
                raise ValueError(f"Văn bản có thừa dấu ] ở vị trí {i + 1}: …{noi_dung[max(0, i - 20) : i + 1]}")
            mo = None
    if mo is not None:
        raise ValueError(f"Nhãn mở ở vị trí {mo + 1} thiếu dấu ]: {noi_dung[mo : mo + 40]}…")


def dieu_khoan_tren_trang(van_ban: VanBanHieuLuc, so_trang: int) -> list[DieuKhoan]:
    return [dk for dk in van_ban.dieu_khoan if dk.trang_bat_dau <= so_trang <= dk.trang_ket_thuc]


def dieu_khoan_da_sua(van_ban: VanBanHieuLuc, goc: VanBanHieuLuc | None) -> set[int]:
    """Mã các Điều khoản có nội dung khác bản số hóa gốc."""
    if goc is None:
        return set()
    noi_dung_goc = {dk.ma: dk.noi_dung for dk in goc.dieu_khoan}
    return {dk.ma for dk in van_ban.dieu_khoan if noi_dung_goc.get(dk.ma) != dk.noi_dung}


@dataclass(frozen=True)
class TomTatVanBan:
    hash_pdf: str
    ten_file: str
    so_trang: int
    so_trang_tin_cay_thap: int
    so_dieu_khoan: int


def danh_sach_van_ban(thu_muc: str | Path) -> list[TomTatVanBan]:
    """Các Văn bản hiệu lực đã lưu (bản đang dùng), mới cập nhật trước."""
    thu_muc_con = Path(thu_muc) / THU_MUC_CON
    file = [f for f in thu_muc_con.glob("*.json") if "-" not in f.stem] if thu_muc_con.is_dir() else []
    ra = []
    for f in sorted(file, key=lambda f: (-f.stat().st_mtime_ns, f.stem)):
        vb = _doc(f)
        ra.append(TomTatVanBan(vb.hash_pdf, vb.ten_file, len(vb.trang), sum(t.tin_cay_thap for t in vb.trang),
                               len(vb.dieu_khoan)))
    return ra
