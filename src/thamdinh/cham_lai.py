"""Chấm lại các Lượt đã lưu bằng code hiện tại, không gọi model (issue 25).

Dùng khi thay đổi nằm ở code sau model (tổng hợp, kiểm tra Trích dẫn): so kết quả của hai bản code trên cùng câu trả lời
model đã lưu. Xem `docs/agents/thu-nghiem-model.md`.
"""

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from thamdinh.bo_chuan import BoChuan
from thamdinh.checklist import PhienBanChecklist
from thamdinh.kho_luot import KhoLuot
from thamdinh.so_hoa.van_ban import nap_van_ban
from thamdinh.tong_hop import DanhGiaTieuChi, tong_hop_muc
from thamdinh.trich_dan import TrichDan, kiem_tra_trich_dan


@dataclass(frozen=True)
class ChamLuot:
    danh_gia: dict[str, str]  # mã Tiêu chí → Đánh giá tiêu chí sau khi tổng hợp lại
    ket_qua_muc: dict[int, str | None]  # None: Mục chưa đánh giá được
    trich_dan: dict[str, tuple[str, ...]]  # mã Tiêu chí → trạng thái từng Trích dẫn; rỗng khi thiếu Văn bản hiệu lực


@dataclass(frozen=True)
class ChamKho:
    luot: dict[str, ChamLuot]  # theo mã Lượt
    loi: dict[str, str]  # mã Lượt không nạp được → lỗi


def cham_lai(kho: KhoLuot, checklist: PhienBanChecklist, thu_muc: str | Path) -> ChamKho:
    theo_so = {m.so: m for m in checklist.muc}
    luot, loi = {}, {}
    for tom_tat in kho.danh_sach():
        try:
            l = kho.nap(tom_tat.ma)
        except Exception as e:  # Lượt lưu bằng code khác (đã revert): ghi lại, chấm tiếp các Lượt khác
            loi[tom_tat.ma] = f"{type(e).__name__}: {e}"
            continue
        danh_gia: dict[str, str] = {}
        ket_qua_muc: dict[int, str | None] = {}
        van_ban = nap_van_ban(l.hash_pdf, thu_muc, l.hash_van_ban)
        trich_dan = {} if van_ban is None else {
            t.ma: tuple(kiem_tra_trich_dan(TrichDan(td.so_hieu, td.nguyen_van), van_ban).trang_thai for td in t.trich_dan)
            for m in l.muc for t in m.tieu_chi
        }
        for m in l.muc:
            if m.ket_qua is None:
                ket_qua_muc[m.so] = None
                continue
            kq = tong_hop_muc(theo_so[m.so], [
                DanhGiaTieuChi(t.ma, t.danh_gia_llm, t.gia_tri, t.gia_tri_dieu_kien, t.ly_do) for t in m.tieu_chi
            ])
            danh_gia |= kq.danh_gia
            ket_qua_muc[m.so] = kq.ket_qua
        luot[tom_tat.ma] = ChamLuot(danh_gia, ket_qua_muc, trich_dan)
    return ChamKho(luot, loi)


def den_json(kq: ChamKho) -> dict:
    return {
        "luot": {ma: {"danh_gia": l.danh_gia, "ket_qua_muc": {str(so): k for so, k in l.ket_qua_muc.items()},
                      "trich_dan": {tc: list(td) for tc, td in l.trich_dan.items()}} for ma, l in kq.luot.items()},
        "loi": kq.loi,
    }


def tu_json(d: dict) -> ChamKho:
    return ChamKho(
        {ma: ChamLuot(l["danh_gia"], {int(so): k for so, k in l["ket_qua_muc"].items()},
                      {tc: tuple(td) for tc, td in l["trich_dan"].items()}) for ma, l in d["luot"].items()},
        d["loi"],
    )


@dataclass(frozen=True)
class SoChamLuot:
    dung_truoc: int  # số Tiêu chí khớp Bộ chuẩn
    dung_sau: int
    sai_thanh_dung: tuple[str, ...]
    dung_thanh_sai: tuple[str, ...]
    muc_doi: tuple[tuple[int, str | None, str | None], ...]  # (số Mục, Kết quả trước, Kết quả sau)
    muc_dung_truoc: int  # số Kết quả Mục khớp Bộ chuẩn
    muc_dung_sau: int


@dataclass(frozen=True)
class SoCham:
    luot: dict[str, SoChamLuot]  # Lượt có ở cả hai lần chấm
    trich_dan: dict[tuple[str, str], int]  # (trạng thái trước, trạng thái sau) → số Trích dẫn, mọi Lượt cộng lại


def so_cham(truoc: ChamKho, sau: ChamKho, bo_chuan: BoChuan) -> SoCham:
    chuan = {ma: d.danh_gia for ma, d in bo_chuan.danh_gia.items()}
    chuan_muc = {so: kq for so, kq in bo_chuan.ket_qua_muc.items() if kq}
    ket_qua, trich_dan = {}, Counter()
    for ma in truoc.luot.keys() & sau.luot.keys():
        a, b = truoc.luot[ma], sau.luot[ma]
        dung_a = {tc for tc, dg in chuan.items() if a.danh_gia.get(tc) == dg}
        dung_b = {tc for tc, dg in chuan.items() if b.danh_gia.get(tc) == dg}
        cac_muc = sorted(a.ket_qua_muc.keys() | b.ket_qua_muc.keys())
        ket_qua[ma] = SoChamLuot(
            len(dung_a), len(dung_b), tuple(sorted(dung_b - dung_a)), tuple(sorted(dung_a - dung_b)),
            tuple((so, a.ket_qua_muc.get(so), b.ket_qua_muc.get(so)) for so in cac_muc
                  if a.ket_qua_muc.get(so) != b.ket_qua_muc.get(so)),
            sum(a.ket_qua_muc.get(so) == kq for so, kq in chuan_muc.items()),
            sum(b.ket_qua_muc.get(so) == kq for so, kq in chuan_muc.items()),
        )
        for tc in a.trich_dan.keys() & b.trich_dan.keys():
            trich_dan.update(zip(a.trich_dan[tc], b.trich_dan[tc]))
    return SoCham(ket_qua, dict(trich_dan))
