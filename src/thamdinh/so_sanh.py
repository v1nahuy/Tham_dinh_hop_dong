"""So sánh ba nguồn đánh giá một Hợp đồng: chế độ toàn văn, chế độ truy xuất và Bộ chuẩn làm tay (issue 15).

So theo `danh_gia` cuối cùng (sau khi code so ngưỡng) của từng Tiêu chí; `khong_ro` khác `thoa`. Mục chưa đánh giá được
tính là không khớp và ghi riêng. Bộ chuẩn có thể chưa điền xong: chỉ so các Tiêu chí đã điền.
"""

from collections.abc import Collection, Sequence
from dataclasses import dataclass

from thamdinh.bo_chuan import BoChuan, DanhGiaChuan
from thamdinh.checklist import PhienBanChecklist, TieuChi
from thamdinh.so_hoa import VanBanHieuLuc
from thamdinh.tham_dinh import DanhGiaDeXuat, KetQuaLuot, TrichDanDaKiemTra
from thamdinh.tong_hop import TEN_DANH_GIA, TEN_KET_QUA
from thamdinh.trich_dan import KHONG_XAC_MINH_DUOC
from thamdinh.truy_xuat import DoPhu, NguCanhMuc, do_phu_ngu_canh

TEN_CHE_DO = {"toan_van": "toàn văn", "truy_xuat": "truy xuất"}


@dataclass(frozen=True)
class TyLe:
    khop: int
    tong: int


@dataclass(frozen=True)
class DongTieuChi:
    ma: str
    so_muc: int
    mo_ta: str
    toan_van: DanhGiaDeXuat | None  # None khi Mục chưa đánh giá được
    truy_xuat: DanhGiaDeXuat | None
    chuan: DanhGiaChuan | None  # None khi Bộ chuẩn chưa điền


@dataclass(frozen=True)
class DongMuc:
    so: int
    cau_hoi: str
    toan_van: str | None  # dat | luu_y | vi_pham; None khi chưa đánh giá được
    truy_xuat: str | None
    chuan: str | None
    tieu_chi_hai_che_do: TyLe
    tieu_chi_toan_van_chuan: TyLe
    tieu_chi_truy_xuat_chuan: TyLe


@dataclass(frozen=True)
class SoSanhNguon:
    dong: tuple[DongTieuChi, ...]
    muc: tuple[DongMuc, ...]
    so_tieu_chi_chuan: int  # số Tiêu chí Bộ chuẩn đã điền
    toan_van_truy_xuat: TyLe
    toan_van_chuan: TyLe
    truy_xuat_chuan: TyLe
    muc_toan_van_truy_xuat: TyLe
    muc_toan_van_chuan: TyLe
    muc_truy_xuat_chuan: TyLe
    gia_tri_toan_van_truy_xuat: TyLe
    gia_tri_toan_van_chuan: TyLe
    gia_tri_truy_xuat_chuan: TyLe
    bat_dong: tuple[DongTieuChi, ...]  # các nguồn đã có không thống nhất
    chua_danh_gia: dict[str, tuple[int, ...]]  # theo chế độ, chỉ chế độ có Mục chưa đánh giá được
    khong_xac_minh: dict[str, tuple[tuple[str, TrichDanDaKiemTra], ...]]  # theo chế độ: (mã Tiêu chí, Trích dẫn)
    canh_bao: tuple[str, ...]


def so_sanh_nguon(
    checklist: PhienBanChecklist, toan_van: KetQuaLuot, truy_xuat: KetQuaLuot, bo_chuan: BoChuan | None = None
) -> SoSanhNguon:
    if (toan_van.hash_pdf, toan_van.checklist) != (truy_xuat.hash_pdf, truy_xuat.checklist):
        raise ValueError(f"Hai Lượt thuộc Hợp đồng khác hoặc checklist khác ({toan_van.ma}, {truy_xuat.ma})")
    cua_tv, cua_tx = _theo_ma(toan_van), _theo_ma(truy_xuat)
    chuan = bo_chuan.danh_gia if bo_chuan else {}
    tieu_chi = [(muc.so, tc) for muc in checklist.muc for ds in muc.tieu_chi.values() for tc in ds]
    dong = tuple(
        DongTieuChi(tc.ma, so, tc.mo_ta, cua_tv.get(tc.ma), cua_tx.get(tc.ma), chuan.get(tc.ma)) for so, tc in tieu_chi
    )
    co_chuan = [d for d in dong if d.chuan]
    co_gia_tri = [(d, tc) for d, (_, tc) in zip(dong, tieu_chi) if tc.truong or tc.dieu_kien]

    def so_cap(chon: list[DongTieuChi], a: str, b: str) -> TyLe:
        return _ty_le([(_danh_gia(getattr(d, a)), _danh_gia(getattr(d, b))) for d in chon])

    def so_gia_tri(a: str, b: str) -> TyLe:
        cap = [(getattr(d, a), getattr(d, b), tc) for d, tc in co_gia_tri if b != "chuan" or d.chuan]
        return TyLe(sum(_cung_gia_tri(x, y, tc) for x, y, tc in cap), len(cap))

    ket_qua_tv, ket_qua_tx = _ket_qua_muc(toan_van), _ket_qua_muc(truy_xuat)
    ket_qua_chuan = bo_chuan.ket_qua_muc if bo_chuan else {}
    muc = []
    for m in checklist.muc:
        cua_muc = [d for d in dong if d.so_muc == m.so]
        co_chuan_muc = [d for d in cua_muc if d.chuan]
        muc.append(DongMuc(
            m.so, m.cau_hoi, ket_qua_tv.get(m.so), ket_qua_tx.get(m.so), ket_qua_chuan.get(m.so),
            so_cap(cua_muc, "toan_van", "truy_xuat"),
            so_cap(co_chuan_muc, "toan_van", "chuan"),
            so_cap(co_chuan_muc, "truy_xuat", "chuan"),
        ))
    co_ket_qua_chuan = [m for m in muc if m.chuan]

    canh_bao = [f"Lượt truy xuất: {c}" for c in truy_xuat.canh_bao] + [f"Lượt toàn văn: {c}" for c in toan_van.canh_bao]
    if toan_van.hash_van_ban != truy_xuat.hash_van_ban:
        canh_bao.append("Hai Lượt dùng Văn bản hiệu lực khác nhau (đã sửa tay giữa hai lần chạy?).")

    luot = {"toan_van": toan_van, "truy_xuat": truy_xuat}
    chua_danh_gia = {che_do: _muc_chua_danh_gia(checklist, l) for che_do, l in luot.items()}
    return SoSanhNguon(
        dong=dong,
        muc=tuple(muc),
        so_tieu_chi_chuan=len(co_chuan),
        toan_van_truy_xuat=so_cap(list(dong), "toan_van", "truy_xuat"),
        toan_van_chuan=so_cap(co_chuan, "toan_van", "chuan"),
        truy_xuat_chuan=so_cap(co_chuan, "truy_xuat", "chuan"),
        muc_toan_van_truy_xuat=_ty_le([(m.toan_van, m.truy_xuat) for m in muc]),
        muc_toan_van_chuan=_ty_le([(m.toan_van, m.chuan) for m in co_ket_qua_chuan]),
        muc_truy_xuat_chuan=_ty_le([(m.truy_xuat, m.chuan) for m in co_ket_qua_chuan]),
        gia_tri_toan_van_truy_xuat=so_gia_tri("toan_van", "truy_xuat"),
        gia_tri_toan_van_chuan=so_gia_tri("toan_van", "chuan"),
        gia_tri_truy_xuat_chuan=so_gia_tri("truy_xuat", "chuan"),
        bat_dong=tuple(d for d in dong if not _thong_nhat(d)),
        chua_danh_gia={che_do: so for che_do, so in chua_danh_gia.items() if so},
        khong_xac_minh={che_do: _khong_xac_minh(l) for che_do, l in luot.items()},
        canh_bao=tuple(canh_bao),
    )


@dataclass(frozen=True)
class DongLanChay:
    ma: str
    so_muc: int
    mo_ta: str
    truoc: DanhGiaDeXuat | None  # None khi Mục chưa đánh giá được
    sau: DanhGiaDeXuat | None
    chuan: DanhGiaChuan


@dataclass(frozen=True)
class SoSanhLanChay:
    """Hai lần chạy cùng chế độ trên cùng Hợp đồng (trước / sau khi đổi prompt), chấm theo Bộ chuẩn (issue 17)."""

    truoc: TyLe
    sau: TyLe
    sai_thanh_dung: tuple[DongLanChay, ...]
    dung_thanh_sai: tuple[DongLanChay, ...]
    canh_bao: tuple[str, ...]  # Mục đọc Điều khoản khác nhau giữa hai lần chạy: so sánh không công bằng


def so_sanh_lan_chay(
    checklist: PhienBanChecklist, truoc: KetQuaLuot, sau: KetQuaLuot, bo_chuan: BoChuan, muc: Collection[int]
) -> SoSanhLanChay:
    """Chỉ tính các Tiêu chí Bộ chuẩn đã điền của các Mục `muc`."""
    cua_truoc, cua_sau = _theo_ma(truoc), _theo_ma(sau)
    dong = [
        DongLanChay(tc.ma, m.so, tc.mo_ta, cua_truoc.get(tc.ma), cua_sau.get(tc.ma), bo_chuan.danh_gia[tc.ma])
        for m in checklist.muc if m.so in muc
        for ds in m.tieu_chi.values() for tc in ds if tc.ma in bo_chuan.danh_gia
    ]

    def dung(d: DanhGiaDeXuat | None, c: DanhGiaChuan) -> bool:
        return d is not None and d.danh_gia == c.danh_gia

    doc_truoc = {m.so: set(m.dieu_khoan_dua_vao) for m in truoc.muc}
    canh_bao = []
    for m in sau.muc:
        if m.so in muc and set(m.dieu_khoan_dua_vao) != doc_truoc.get(m.so, set()):
            them = set(m.dieu_khoan_dua_vao) - doc_truoc.get(m.so, set())
            bot = doc_truoc.get(m.so, set()) - set(m.dieu_khoan_dua_vao)
            canh_bao.append(f"Mục {m.so} đọc Điều khoản khác lần trước: thêm {', '.join(sorted(them)) or 'không'}; "
                            f"bớt {', '.join(sorted(bot)) or 'không'}.")

    return SoSanhLanChay(
        truoc=TyLe(sum(dung(d.truoc, d.chuan) for d in dong), len(dong)),
        sau=TyLe(sum(dung(d.sau, d.chuan) for d in dong), len(dong)),
        sai_thanh_dung=tuple(d for d in dong if not dung(d.truoc, d.chuan) and dung(d.sau, d.chuan)),
        dung_thanh_sai=tuple(d for d in dong if dung(d.truoc, d.chuan) and not dung(d.sau, d.chuan)),
        canh_bao=tuple(canh_bao),
    )


def do_phu_tu_luot(
    trich_dan_chuan: dict[str, tuple[str, ...]],
    checklist: PhienBanChecklist,
    van_ban: VanBanHieuLuc,
    truy_xuat: KetQuaLuot,
) -> list[DoPhu]:
    """Độ phủ ngữ cảnh theo đúng các Điều khoản Lượt truy xuất đã đọc (lưu trong Lượt), không chọn lại."""
    doc = {m.so: set(m.dieu_khoan_dua_vao) for m in truy_xuat.muc}

    def ngu_canh(muc) -> NguCanhMuc:
        chon = doc.get(muc.so, set())
        return NguCanhMuc(tuple(chon), "\n".join(d.noi_dung for d in van_ban.dieu_khoan if d.so_hieu in chon), 0, (), ())

    return do_phu_ngu_canh(trich_dan_chuan, checklist, van_ban, ngu_canh)


def bao_cao_so_sanh(
    kq: SoSanhNguon,
    toan_van: KetQuaLuot,
    truy_xuat: KetQuaLuot,
    do_phu: Sequence[DoPhu] = (),
    canh_bao: Sequence[str] = (),
) -> str:
    """Báo cáo Markdown: tỷ lệ khớp, từng Mục, Trích dẫn không xác minh được, độ phủ ngữ cảnh, các Tiêu chí bất đồng."""
    dong = [
        f"# So sánh các nguồn đánh giá: {toan_van.ten_file}",
        "",
        f"- **Lượt toàn văn:** {toan_van.ma} ({toan_van.bat_dau} → {toan_van.ket_thuc})",
        f"- **Lượt truy xuất:** {truy_xuat.ma} ({truy_xuat.bat_dau} → {truy_xuat.ket_thuc})",
        f"- **Model:** {toan_van.model}; **checklist:** {toan_van.checklist}",
        f"- **Bộ chuẩn:** đã điền {kq.so_tieu_chi_chuan}/{len(kq.dong)} Tiêu chí",
        "",
    ]
    if tat_ca := [*canh_bao, *kq.canh_bao]:
        dong += ["## Cảnh báo", "", *(f"- {c}" for c in tat_ca), ""]
    for che_do, so in kq.chua_danh_gia.items():
        dong += [f"**Mục chưa đánh giá được ({TEN_CHE_DO[che_do]}):** {', '.join(map(str, so))}", ""]

    dong += [
        "## Tỷ lệ khớp", "",
        "| Cặp so sánh | Tiêu chí | Kết quả Mục | Giá trị định lượng |", "|---|---|---|---|",
        f"| Toàn văn – truy xuất | {_pt(kq.toan_van_truy_xuat)} | {_pt(kq.muc_toan_van_truy_xuat)} "
        f"| {_pt(kq.gia_tri_toan_van_truy_xuat)} |",
        f"| Toàn văn – Bộ chuẩn | {_pt(kq.toan_van_chuan)} | {_pt(kq.muc_toan_van_chuan)} "
        f"| {_pt(kq.gia_tri_toan_van_chuan)} |",
        f"| Truy xuất – Bộ chuẩn | {_pt(kq.truy_xuat_chuan)} | {_pt(kq.muc_truy_xuat_chuan)} "
        f"| {_pt(kq.gia_tri_truy_xuat_chuan)} |",
        "",
        "## Từng Mục", "",
        "| Mục | Toàn văn | Truy xuất | Bộ chuẩn | Tiêu chí khớp giữa hai chế độ | Toàn văn – chuẩn | Truy xuất – chuẩn |",
        "|---|---|---|---|---|---|---|",
    ]
    dong += [
        f"| {m.so} | {_ten_kq(m.toan_van)} | {_ten_kq(m.truy_xuat)} | {TEN_KET_QUA.get(m.chuan, '–')} "
        f"| {_pt(m.tieu_chi_hai_che_do)} | {_pt(m.tieu_chi_toan_van_chuan)} | {_pt(m.tieu_chi_truy_xuat_chuan)} |"
        for m in kq.muc
    ]

    dong += ["", "## Trích dẫn không xác minh được", ""]
    for che_do, luot in (("toan_van", toan_van), ("truy_xuat", truy_xuat)):
        tong = sum(len(t.trich_dan) for m in luot.muc for t in m.tieu_chi)
        sai = kq.khong_xac_minh[che_do]
        dong.append(f"**{TEN_CHE_DO[che_do].capitalize()}:** {len(sai)}/{tong} Trích dẫn")
        dong += ["", *(f"- {ma} ({td.so_hieu}): “{td.nguyen_van}”" for ma, td in sai), ""]

    dong += ["## Ngữ cảnh chế độ truy xuất", "", "| Mục | Số Điều khoản đã đọc | Cảnh báo |", "|---|---|---|"]
    dong += [f"| {m.so} | {len(m.dieu_khoan_dua_vao)} | {'; '.join(m.canh_bao)} |" for m in truy_xuat.muc]
    dong += [""]
    if do_phu:
        tinh = [d for d in do_phu if d.trang_thai != "khong_co_trong_van_ban"]
        dong += [f"**Độ phủ Trích dẫn Bộ chuẩn:** {_pt(TyLe(sum(d.trang_thai == 'co' for d in tinh), len(tinh)))}", ""]
        dong += [f"- Ngoài ngữ cảnh, {d.ma}: “{d.nguyen_van}”" for d in tinh if d.trang_thai == "thieu"]
        dong += [f"- Không tìm thấy trong Văn bản hiệu lực (Bộ chuẩn chép sai hoặc số hóa lỗi), {d.ma}: “{d.nguyen_van}”"
                 for d in do_phu if d.trang_thai == "khong_co_trong_van_ban"]
        dong += [""]

    dong += [
        f"## Các Tiêu chí không thống nhất ({len(kq.bat_dong)}/{len(kq.dong)})", "",
        "| Mã | Tiêu chí | Toàn văn | Truy xuất | Bộ chuẩn |", "|---|---|---|---|---|",
    ]
    dong += [
        f"| {d.ma} | {d.mo_ta} | {_ten_dg(d.toan_van)} | {_ten_dg(d.truy_xuat)} "
        f"| {TEN_DANH_GIA[d.chuan.danh_gia] if d.chuan else '–'} |"
        for d in kq.bat_dong
    ]
    return "\n".join(dong) + "\n"


def _pt(t: TyLe) -> str:
    return f"{t.khop}/{t.tong} ({t.khop / t.tong:.1%})" if t.tong else "–"


def _ten_kq(ket_qua: str | None) -> str:
    return TEN_KET_QUA[ket_qua] if ket_qua else "Chưa đánh giá được"


def _ten_dg(d: DanhGiaDeXuat | None) -> str:
    return TEN_DANH_GIA[d.danh_gia] if d else "Chưa đánh giá được"


def _theo_ma(luot: KetQuaLuot) -> dict[str, DanhGiaDeXuat]:
    return {t.ma: t for m in luot.muc for t in m.tieu_chi}


def _ket_qua_muc(luot: KetQuaLuot) -> dict[int, str]:
    return {m.so: m.ket_qua.ket_qua for m in luot.muc if m.ket_qua}


def _muc_chua_danh_gia(checklist: PhienBanChecklist, luot: KetQuaLuot) -> tuple[int, ...]:
    co = _ket_qua_muc(luot)
    return tuple(m.so for m in checklist.muc if m.so not in co)


def _khong_xac_minh(luot: KetQuaLuot) -> tuple[tuple[str, TrichDanDaKiemTra], ...]:
    return tuple((t.ma, td) for m in luot.muc for t in m.tieu_chi for td in t.trich_dan
                 if td.trang_thai == KHONG_XAC_MINH_DUOC)


def _danh_gia(d: DanhGiaDeXuat | DanhGiaChuan | None) -> str | None:
    return d.danh_gia if d else None


def _ty_le(cap: list[tuple]) -> TyLe:
    """Bên nào chưa đánh giá được (None) thì tính là không khớp."""
    return TyLe(sum(a is not None and a == b for a, b in cap), len(cap))


def _gia_tri(d: DanhGiaDeXuat | DanhGiaChuan, tc: TieuChi) -> float | None:
    if isinstance(d, DanhGiaChuan):
        return d.gia_tri
    return d.gia_tri if tc.truong else d.gia_tri_dieu_kien


def _cung_gia_tri(a: DanhGiaDeXuat | DanhGiaChuan | None, b: DanhGiaDeXuat | DanhGiaChuan | None, tc: TieuChi) -> bool:
    """Hai bên cùng không đọc được con số cũng là khớp; Mục chưa đánh giá được thì không."""
    return a is not None and b is not None and _gia_tri(a, tc) == _gia_tri(b, tc)


def _thong_nhat(d: DongTieuChi) -> bool:
    nguon = [_danh_gia(d.toan_van), _danh_gia(d.truy_xuat)]
    if d.chuan:
        nguon.append(d.chuan.danh_gia)
    return nguon[0] is not None and len(set(nguon)) == 1
