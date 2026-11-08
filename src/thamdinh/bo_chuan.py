"""Bộ chuẩn: kết quả thẩm định làm tay, dùng để đo chất lượng hệ thống (issue 13, 15)."""

import json
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from thamdinh.checklist import PhienBanChecklist, load_checklist
from thamdinh.so_hoa import hash_pdf

TEN_MUC = {"dat": "Đạt", "luu_y": "Lưu ý", "vi_pham": "Vi phạm"}

HUONG_DAN = """\
# BỘ CHUẨN THẨM ĐỊNH (điền tay)
#
# Điền bằng cách đọc trực tiếp PDF Hợp đồng, TRƯỚC KHI xem bất kỳ Kết quả đề xuất nào của hệ thống.
#
# Với mỗi Tiêu chí:
#   danh_gia:  thoa | khong_thoa | khong_ro      (bắt buộc)
#              - "Nếu ..." thì coi là thoa khi điều kiện không xảy ra.
#              - khong_ro khi Hợp đồng không đủ thông tin để kết luận (ví dụ cần giấy ủy quyền, năng lực thực tế).
#              - Tiêu chí định lượng: vẫn điền danh_gia theo ý bạn, và điền gia_tri là con số đọc được trong Hợp đồng.
#   gia_tri:   chỉ với Tiêu chí có dòng "# gia_tri:"; ghi số (không ghi đơn vị), để trống nếu Hợp đồng không ghi.
#   trich_dan: câu trích NGUYÊN VĂN từ Hợp đồng làm căn cứ (chép đúng chữ, có thể nhiều câu bằng danh sách).
#   vi_tri:    số hiệu Điều khoản và trang, ví dụ "4.3.2, trang 3" hoặc "Phụ lục 01, Mục B, trang 14".
#   ghi_chu:   tùy chọn.
# Với mỗi Mục: ket_qua (dat | luu_y | vi_pham) là nhận định chung của bạn, điền SAU khi xong các Tiêu chí.
#
# Kiểm tra file đã điền đủ chưa: .venv/Scripts/python scripts/kiem_tra_bo_chuan.py <file này>
"""


def chuoi(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def tao_mau_bo_chuan(duong_dan_checklist: Path, duong_dan_pdf: Path) -> str:
    checklist = load_checklist(duong_dan_checklist)
    dong = [
        HUONG_DAN,
        f"hop_dong: {chuoi(duong_dan_pdf.name)}",
        f"hash_pdf: {hash_pdf(duong_dan_pdf)}",
        f"checklist: {chuoi(f'{checklist.ma} {checklist.phien_ban}')}",
        'nguoi_dien: ""',
        'ngay_dien: ""',
        "",
        "muc:",
    ]
    for muc in checklist.muc:
        dong += [
            f"  - so: {muc.so}",
            f"    cau_hoi: {chuoi(muc.cau_hoi)}",
            '    ket_qua: ""',
            "    tieu_chi:",
        ]
        for muc_kq, ds in muc.tieu_chi.items():
            for tc in ds:
                dong += [
                    f"      # [{TEN_MUC[muc_kq]}] {tc.mo_ta}",
                    f'      - ma: "{tc.ma}"',
                    '        danh_gia: ""',
                ]
                truong = tc.truong or (tc.dieu_kien.truong if tc.dieu_kien else None)
                if truong:
                    dong += [f"        # gia_tri: {truong}", "        gia_tri:"]
                dong += ['        trich_dan: ""', '        vi_tri: ""', '        ghi_chu: ""']
        dong.append("")
    return "\n".join(dong)


# --- Nạp và kiểm tra file đã điền -----------------------------------------------------------------

DANH_GIA_HOP_LE = ("thoa", "khong_thoa", "khong_ro")
KET_QUA_HOP_LE = ("dat", "luu_y", "vi_pham")


class BoChuanError(Exception):
    """File Bộ chuẩn chưa điền đủ hoặc sai; `loi` liệt kê mọi lỗi kèm vị trí."""

    def __init__(self, loi: list[str]):
        super().__init__(f"{len(loi)} lỗi:\n" + "\n".join(loi))
        self.loi = loi


@dataclass(frozen=True)
class DanhGiaChuan:
    ma: str
    danh_gia: str
    gia_tri: float | None
    trich_dan: tuple[str, ...]
    vi_tri: str
    ghi_chu: str


@dataclass(frozen=True)
class BoChuan:
    hop_dong: str
    hash_pdf: str
    checklist: str
    nguoi_dien: str
    ngay_dien: str
    danh_gia: dict[str, DanhGiaChuan]
    ket_qua_muc: dict[int, str | None]


def nap_bo_chuan(
    duong_dan: str | Path, checklist: PhienBanChecklist, pdf: str | Path | None = None, mot_phan: bool = False
) -> BoChuan:
    """`mot_phan`: nhận file chưa điền xong, chỉ lấy các Tiêu chí đã điền; ô đã điền mà sai vẫn báo lỗi."""
    d = _doc_yaml(duong_dan)
    loi: list[str] = []

    ten_checklist = f"{checklist.ma} {checklist.phien_ban}"
    if d.get("checklist") != ten_checklist:
        loi.append(f"File điền cho checklist '{d.get('checklist')}', nhưng đang kiểm tra với '{ten_checklist}'")
    if pdf is not None and d.get("hash_pdf") != hash_pdf(pdf):
        loi.append(f"hash_pdf không khớp với file {Path(pdf).name}: Bộ chuẩn này được điền cho một file PDF khác")

    da_dien = {m.get("so"): m for m in d.get("muc") or []}
    danh_gia: dict[str, DanhGiaChuan] = {}
    ket_qua_muc: dict[int, str | None] = {}
    for muc in checklist.muc:
        m = da_dien.pop(muc.so, None)
        if m is None:
            loi.append(f"Thiếu Mục {muc.so}")
            continue
        vi_tri = f"Mục {muc.so}"
        ket_qua = m.get("ket_qua") or None
        if ket_qua is not None and ket_qua not in KET_QUA_HOP_LE:
            loi.append(f"{vi_tri}: ket_qua '{ket_qua}' không hợp lệ, phải là {' | '.join(KET_QUA_HOP_LE)}")
        ket_qua_muc[muc.so] = ket_qua

        tieu_chi = {str(t.get("ma")): t for t in m.get("tieu_chi") or []}
        for ds in muc.tieu_chi.values():
            for tc in ds:
                t = tieu_chi.pop(tc.ma, None)
                if t is None:
                    loi.append(f"{vi_tri}: thiếu tiêu chí {tc.ma}")
                    continue
                if mot_phan and not t.get("danh_gia"):
                    continue
                if (dg := _danh_gia(t, f"{vi_tri}, tiêu chí {tc.ma}", loi)) is not None:
                    danh_gia[tc.ma] = dg
        loi += [f"{vi_tri}: tiêu chí {ma} không có trong checklist" for ma in tieu_chi]
    loi += [f"Mục {so} không có trong checklist" for so in da_dien]

    if loi:
        raise BoChuanError(loi)
    return BoChuan(
        hop_dong=d.get("hop_dong") or "",
        hash_pdf=d.get("hash_pdf") or "",
        checklist=ten_checklist,
        nguoi_dien=d.get("nguoi_dien") or "",
        ngay_dien=str(d.get("ngay_dien") or ""),
        danh_gia=danh_gia,
        ket_qua_muc=ket_qua_muc,
    )


def doc_trich_dan_chuan(duong_dan: str | Path) -> dict[str, tuple[str, ...]]:
    """Trích dẫn của các Tiêu chí đã điền, kể cả khi Bộ chuẩn chưa điền xong (đo độ phủ ngữ cảnh, issue 09/15)."""
    d = _doc_yaml(duong_dan)
    kq = {}
    for m in d.get("muc") or []:
        for t in m.get("tieu_chi") or []:
            td = t.get("trich_dan") or ()
            td = tuple(x for x in ((td,) if isinstance(td, str) else td) if str(x).strip())
            if td:
                kq[str(t["ma"])] = td
    return kq


def _doc_yaml(duong_dan: str | Path) -> dict:
    noi_dung = Path(duong_dan).read_text(encoding="utf-8")
    try:
        return yaml.safe_load(noi_dung) or {}
    except yaml.MarkedYAMLError as e:
        # File điền tay: báo dòng/cột thay vì traceback; Tab (hay gõ nhầm) không hợp lệ trong YAML
        mark = e.problem_mark or e.context_mark
        vi_tri = f"dòng {mark.line + 1}, cột {mark.column + 1}" if mark else "không rõ vị trí"
        dong = noi_dung.splitlines()[mark.line] if mark and mark.line < len(noi_dung.splitlines()) else ""
        goi_y = " Dòng này có ký tự Tab: hãy xóa Tab, chỉ dùng dấu cách." if "\t" in dong else ""
        raise BoChuanError([f"File không đúng cú pháp YAML ở {vi_tri}: {e.problem}.{goi_y}"]) from e


def _danh_gia(t: dict, vi_tri: str, loi: list[str]) -> DanhGiaChuan | None:
    so_loi = len(loi)
    danh_gia = t.get("danh_gia") or None
    if danh_gia is None:
        loi.append(f"{vi_tri}: chưa điền danh_gia")
    elif danh_gia not in DANH_GIA_HOP_LE:
        loi.append(f"{vi_tri}: danh_gia '{danh_gia}' không hợp lệ, phải là {' | '.join(DANH_GIA_HOP_LE)}")
    gia_tri = t.get("gia_tri")
    if gia_tri is not None and (isinstance(gia_tri, bool) or not isinstance(gia_tri, (int, float))):
        goi_y = ""
        if isinstance(gia_tri, str) and re.fullmatch(r"\d{1,3}(\.\d{3})+", gia_tri.strip()):
            goi_y = f" (ghi {gia_tri.strip().replace('.', '')}, không dùng dấu chấm phân cách hàng nghìn)"
        loi.append(f"{vi_tri}: gia_tri '{gia_tri}' phải là số{goi_y}")
    if len(loi) > so_loi:
        return None
    trich_dan = t.get("trich_dan") or ()
    return DanhGiaChuan(
        ma=str(t["ma"]),
        danh_gia=danh_gia,
        gia_tri=gia_tri,
        trich_dan=(trich_dan,) if isinstance(trich_dan, str) else tuple(trich_dan),
        vi_tri=t.get("vi_tri") or "",
        ghi_chu=t.get("ghi_chu") or "",
    )
