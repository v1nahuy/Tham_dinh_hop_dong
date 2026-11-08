"""Nạp và kiểm tra Phiên bản checklist từ file YAML."""

import re
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

MUC_KET_QUA = ("dat", "luu_y", "vi_pham")
LOAI_TIEU_CHI = ("dinh_tinh", "dinh_luong")
PHEP_SO_SANH = ("<", "<=", ">", ">=", "==")
TRA_LOI_SU_KIEN = ("co", "khong")
THU_MUC_CAU_HOI_SU_KIEN = "cau-hoi-su-kien"
GHI_CHU_CAN_THONG_TIN_NGOAI = "các tiêu chí này cần thông tin ngoài Hợp đồng"


class ChecklistError(Exception):
    """File checklist không hợp lệ; thông báo chỉ rõ vị trí lỗi."""


@dataclass(frozen=True)
class DieuKien:
    """Tiêu chí chỉ áp dụng khi giá trị `truong` trích từ Hợp đồng thỏa phép so sánh với `nguong`."""

    truong: str
    phep_so_sanh: str
    nguong: float


@dataclass(frozen=True)
class TieuChi:
    ma: str
    mo_ta: str
    loai: str
    truong: str | None = None
    phep_so_sanh: str | None = None
    nguong: float | None = None
    dieu_kien: DieuKien | None = None
    # Khi Kết quả là Vi phạm do tiêu chí này, kèm GHI_CHU_CAN_THONG_TIN_NGOAI.
    can_thong_tin_ngoai: bool = False
    # Câu hỏi sự kiện (issue 19): model trả lời co/khong về Hợp đồng; trả lời bằng `thoa_khi` thì Tiêu chí thỏa.
    # Chỉ Tiêu chí định tính có; nạp từ file cùng tên trong thư mục cau-hoi-su-kien cạnh file checklist.
    cau_hoi: str | None = None
    thoa_khi: str | None = None


@dataclass(frozen=True)
class MucChecklist:
    so: int
    cau_hoi: str
    chu_de: list[str]
    danh_muc: list[str]
    tieu_chi: dict[str, list[TieuChi]]
    can_cu_phap_ly: list[str]
    ghi_chu_khong_ro: str | None


@dataclass(frozen=True)
class PhienBanChecklist:
    ma: str
    phien_ban: str
    ten: str
    dua_tren: str | None
    chu_de: dict[str, str]
    danh_muc_tham_chieu: dict[str, Path]
    muc: list[MucChecklist]


def load_checklist(path: str | Path) -> PhienBanChecklist:
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    for truong in ("ma", "phien_ban", "ten", "muc"):
        _bat_buoc(data, truong, "Checklist")

    chu_de = {c["ma"]: c["ten"] for c in data.get("chu_de") or []}

    danh_muc = {}
    for ma, rel in (data.get("danh_muc_tham_chieu") or {}).items():
        file = path.parent / rel
        if not file.is_file():
            raise ChecklistError(f"Danh mục tham chiếu '{ma}': không tìm thấy file {file}")
        danh_muc[ma] = file

    muc = []
    so_da_gap: set[int] = set()
    ma_da_gap: set[str] = set()
    for m in data["muc"]:
        item = _muc(m, chu_de, danh_muc, ma_da_gap)
        if item.so in so_da_gap:
            raise ChecklistError(f"Mục {item.so}: số mục bị trùng")
        so_da_gap.add(item.so)
        muc.append(item)
    muc = _gan_cau_hoi_su_kien(path, f"{data['ma']} {data['phien_ban']}", muc)

    return PhienBanChecklist(
        ma=data["ma"],
        phien_ban=str(data["phien_ban"]),
        ten=data["ten"],
        dua_tren=data.get("dua_tren"),
        chu_de=chu_de,
        danh_muc_tham_chieu=danh_muc,
        muc=muc,
    )


def _muc(m: dict[str, Any], chu_de: dict[str, str], danh_muc: dict[str, Path], ma_da_gap: set[str]) -> MucChecklist:
    vi_tri = f"Mục {m.get('so', '?')}"
    for truong in ("so", "cau_hoi", "tieu_chi"):
        _bat_buoc(m, truong, vi_tri)

    for cd in m.get("chu_de") or []:
        if cd not in chu_de:
            raise ChecklistError(f"{vi_tri}: Chủ đề '{cd}' chưa được khai báo")
    for dm in m.get("danh_muc") or []:
        if dm not in danh_muc:
            raise ChecklistError(f"{vi_tri}: Danh mục tham chiếu '{dm}' chưa được khai báo")

    tieu_chi = {}
    for muc_kq in MUC_KET_QUA:
        danh_sach = []
        for t in m["tieu_chi"].get(muc_kq) or []:
            tc = _tieu_chi(t, vi_tri)
            if tc.ma in ma_da_gap:
                raise ChecklistError(f"{vi_tri}, tiêu chí {tc.ma}: mã bị trùng")
            ma_da_gap.add(tc.ma)
            danh_sach.append(tc)
        tieu_chi[muc_kq] = danh_sach
    if not tieu_chi["dat"]:
        raise ChecklistError(f"{vi_tri}: thiếu tiêu chí Đạt")

    return MucChecklist(
        so=m["so"],
        cau_hoi=m["cau_hoi"],
        chu_de=list(m.get("chu_de") or []),
        danh_muc=list(m.get("danh_muc") or []),
        tieu_chi=tieu_chi,
        can_cu_phap_ly=list(m.get("can_cu_phap_ly") or []),
        ghi_chu_khong_ro=m.get("ghi_chu_khong_ro"),
    )


def _tieu_chi(t: dict[str, Any], vi_tri_muc: str) -> TieuChi:
    vi_tri = f"{vi_tri_muc}, tiêu chí {t.get('ma', '?')}"
    for truong in ("ma", "mo_ta", "loai"):
        _bat_buoc(t, truong, vi_tri)
    if t["loai"] not in LOAI_TIEU_CHI:
        raise ChecklistError(f"{vi_tri}: loai '{t['loai']}' không hợp lệ, phải là một trong {LOAI_TIEU_CHI}")
    if t["loai"] == "dinh_luong":
        for truong in ("truong", "phep_so_sanh", "nguong"):
            if t.get(truong) is None:
                raise ChecklistError(f"{vi_tri}: tiêu chí định lượng thiếu {truong}")
        if t["phep_so_sanh"] not in PHEP_SO_SANH:
            raise ChecklistError(
                f"{vi_tri}: phep_so_sanh '{t['phep_so_sanh']}' không hợp lệ, phải là một trong {PHEP_SO_SANH}"
            )
    return TieuChi(
        ma=str(t["ma"]),
        mo_ta=t["mo_ta"],
        loai=t["loai"],
        truong=t.get("truong"),
        phep_so_sanh=t.get("phep_so_sanh"),
        nguong=t.get("nguong"),
        dieu_kien=_dieu_kien(t.get("dieu_kien"), vi_tri),
        can_thong_tin_ngoai=bool(t.get("can_thong_tin_ngoai", False)),
    )


def _dieu_kien(d: dict[str, Any] | None, vi_tri: str) -> DieuKien | None:
    if d is None:
        return None
    for truong in ("truong", "phep_so_sanh", "nguong"):
        if d.get(truong) is None:
            raise ChecklistError(f"{vi_tri}: dieu_kien thiếu {truong}")
    if d["phep_so_sanh"] not in PHEP_SO_SANH:
        raise ChecklistError(
            f"{vi_tri}: dieu_kien có phep_so_sanh '{d['phep_so_sanh']}' không hợp lệ, phải là một trong {PHEP_SO_SANH}"
        )
    return DieuKien(truong=d["truong"], phep_so_sanh=d["phep_so_sanh"], nguong=d["nguong"])


def _gan_cau_hoi_su_kien(path: Path, ten_checklist: str, muc: list[MucChecklist]) -> list[MucChecklist]:
    """Gắn câu hỏi sự kiện vào từng Tiêu chí định tính; file phải phủ đúng các Tiêu chí định tính, không thừa không thiếu."""
    file = path.parent / THU_MUC_CAU_HOI_SU_KIEN / path.name
    if not file.is_file():
        raise ChecklistError(f"Câu hỏi sự kiện: không tìm thấy file {file}")
    data = yaml.safe_load(file.read_text(encoding="utf-8")) or {}
    if data.get("checklist") != ten_checklist:
        raise ChecklistError(f"Câu hỏi sự kiện: file {file} soạn cho checklist '{data.get('checklist')}', không phải '{ten_checklist}'")
    cau_hoi: dict[str, Any] = data.get("cau_hoi") or {}
    loai = {tc.ma: (muc_kq, tc.loai) for m in muc for muc_kq, ds in m.tieu_chi.items() for tc in ds}
    for ma in cau_hoi:
        if ma not in loai:
            raise ChecklistError(f"Câu hỏi sự kiện: {ma} không có trong checklist")
    for ma, (muc_kq, loai_tc) in loai.items():
        vi_tri = f"Câu hỏi sự kiện, tiêu chí {ma}"
        if loai_tc == "dinh_luong":
            if ma in cau_hoi:
                raise ChecklistError(f"{vi_tri}: tiêu chí định lượng không có câu hỏi sự kiện (code so ngưỡng)")
            continue
        if ma not in cau_hoi:
            raise ChecklistError(f"Câu hỏi sự kiện: thiếu câu hỏi cho tiêu chí {ma}")
        c = cau_hoi[ma]
        _bat_buoc(c, "cau_hoi", vi_tri)
        if c.get("thoa_khi") not in TRA_LOI_SU_KIEN:
            raise ChecklistError(f"{vi_tri}: thoa_khi '{c.get('thoa_khi')}' không hợp lệ, phải là một trong {TRA_LOI_SU_KIEN}")
        # "Nếu …" được trả lời "co" khi điều kiện không xảy ra, lúc đó Tiêu chí Đạt thỏa, Tiêu chí rủi ro không thỏa
        if c["cau_hoi"].startswith("Nếu") and c["thoa_khi"] != ("co" if muc_kq == "dat" else "khong"):
            yeu_cau = "Đạt phải có thoa_khi: co" if muc_kq == "dat" else "Lưu ý/Vi phạm phải có thoa_khi: khong"
            raise ChecklistError(f'{vi_tri}: câu hỏi "Nếu …" của tiêu chí {yeu_cau}')

    def gan(tc: TieuChi) -> TieuChi:
        c = cau_hoi.get(tc.ma)
        return replace(tc, cau_hoi=c["cau_hoi"], thoa_khi=c["thoa_khi"]) if c else tc

    return [replace(m, tieu_chi={k: [gan(tc) for tc in ds] for k, ds in m.tieu_chi.items()}) for m in muc]


def _bat_buoc(data: dict[str, Any], truong: str, vi_tri: str) -> None:
    if data.get(truong) in (None, ""):
        raise ChecklistError(f"{vi_tri}: thiếu trường '{truong}'")


def tim_checklist(thu_muc: str | Path, ma_phien_ban: str) -> Path:
    """File YAML của Phiên bản checklist mà Lượt ghi là "<mã> <phiên bản>" (ví dụ "dau-ra 1.1")."""
    for file in sorted(Path(thu_muc).glob("*.yaml")):
        data = yaml.safe_load(file.read_text(encoding="utf-8")) or {}
        if f"{data.get('ma')} {data.get('phien_ban')}" == ma_phien_ban:
            return file
    raise FileNotFoundError(f"Không có Phiên bản checklist '{ma_phien_ban}' trong {thu_muc}")


DANH_MUC_TRONG_MO_TA = re.compile(r"Danh mục ([a-z0-9]+(?:-[a-z0-9]+)+)")


def mo_ta_de_doc(mo_ta: str, checklist: PhienBanChecklist) -> str:
    """Mô tả Tiêu chí cho người đọc (báo cáo, giao diện): mã Danh mục tham chiếu thay bằng tên của danh mục đó.

    Ví dụ "(Danh mục nganh-nghe-dang-ky)" thành "(danh mục “Ngành nghề kinh doanh đã đăng ký của Công ty”)". File
    checklist giữ nguyên vì Phiên bản checklist là bất biến.
    """

    def thay(tim: re.Match) -> str:
        file = checklist.danh_muc_tham_chieu.get(tim.group(1))
        if file is None:
            return tim.group(0)
        return f"danh mục “{_ten_danh_muc(str(file))}”"

    return DANH_MUC_TRONG_MO_TA.sub(thay, mo_ta)


@lru_cache
def _ten_danh_muc(file: str) -> str:
    return (yaml.safe_load(Path(file).read_text(encoding="utf-8")) or {}).get("ten") or Path(file).stem
