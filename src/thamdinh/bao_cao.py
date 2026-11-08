"""Báo cáo thẩm định dạng .docx (python-docx), theo bố cục của checklist (issue 12).

Mỗi Mục: Kết quả đã duyệt nếu có, chưa duyệt thì Kết quả đề xuất kèm ghi chú "(đề xuất, chưa duyệt)". Phụ lục cuối liệt
kê các Mục có mức Kết quả đã duyệt khác Kết quả đề xuất.
"""

import io
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from thamdinh.bang_ket_qua import TEN_KET_QUA
from thamdinh.checklist import PhienBanChecklist, mo_ta_de_doc
from thamdinh.kho_luot import KetQuaDuyet
from thamdinh.so_hoa import VanBanHieuLuc
from thamdinh.tham_dinh import KetQuaLuot, KetQuaMucDeXuat
from thamdinh.trich_dan import KHONG_XAC_MINH_DUOC, dieu_khoan_chua_trich_dan

FONT = "Times New Roman"
NEN_KET_QUA = {"dat": "C6EFCE", "luu_y": "FFEB9C", "vi_pham": "FFC7CE"}  # như ô Kết quả trên trang Kết quả
NEN_CAU_HOI = "DCE6F1"  # hàng câu hỏi của checklist gốc
NEN_CHUA_DANH_GIA = "EDEDED"
TEN_CHE_DO = {"toan_van": "toàn văn", "truy_xuat": "truy xuất"}

SO_HOP_DONG = [
    re.compile(r"^\s*Số\s*:\s*(\S.*?)\s*$", re.MULTILINE),  # dòng "Số: …" ở phần mở đầu
    re.compile(r"Hợp đồng số\s*:?\s*(\S.*?)(?:\s+ký ngày|\)|$)", re.MULTILINE | re.IGNORECASE),
]
CHO_TRONG = re.compile(r"…|\.\.")


@dataclass(frozen=True)
class SoHopDong:
    gia_tri: str
    canh_bao: str | None


def so_hop_dong(van_ban: VanBanHieuLuc) -> SoHopDong:
    """Số hợp đồng ghi trong Văn bản hiệu lực: ưu tiên phần mở đầu, rồi đến câu "Kèm theo Hợp đồng số …".

    Dự thảo thường để trống số ("……./2026/VNA-VTIT"): giữ nguyên văn và kèm cảnh báo.
    """
    thu_tu = sorted(van_ban.dieu_khoan, key=lambda dk: dk.loai != "mo_dau")
    for mau in SO_HOP_DONG:
        for dk in thu_tu:
            if tim := mau.search(dk.noi_dung):
                gia_tri = tim.group(1).strip()
                if CHO_TRONG.search(gia_tri):
                    return SoHopDong(gia_tri, f"Không tìm thấy số hợp đồng: Văn bản hiệu lực còn để trống ({gia_tri}).")
                return SoHopDong(gia_tri, None)
    return SoHopDong("", "Không tìm thấy số hợp đồng trong Văn bản hiệu lực.")


def tao_bao_cao(
    luot: KetQuaLuot,
    duyet: dict[int, KetQuaDuyet],
    van_ban: VanBanHieuLuc,
    checklist: PhienBanChecklist,
    so_hop_dong: str,
    canh_bao_so_hop_dong: str | None = None,
) -> bytes:
    doc = Document()
    _dinh_dang(doc)
    tieu_de = doc.add_paragraph()
    tieu_de.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _chu(tieu_de, "BÁO CÁO THẨM ĐỊNH HỢP ĐỒNG ĐẦU RA", dam=True, co=14)

    ngay = _ngay_tham_dinh(luot, duyet)
    nguoi = sorted({d.nguoi_duyet for d in duyet.values()})
    khach_hang = luot.cac_ben.ten_khach_hang if luot.cac_ben else "(chưa xác định được)"
    thong_tin = [
        ("Số hợp đồng", so_hop_dong or "(trống)", canh_bao_so_hop_dong),
        ("Tên file", luot.ten_file, None),
        ("Khách hàng", khach_hang, None),
        ("Phiên bản checklist", f"{checklist.ten} V{checklist.phien_ban}", None),
        ("Ngày thẩm định", f"{ngay:%d/%m/%Y}", None),
        ("Người thẩm định", ", ".join(nguoi) or "(chưa duyệt)", None),
        ("Tình trạng duyệt", f"{len(duyet)}/{len(luot.muc)} Mục đã duyệt", None),
        ("Lượt thẩm định", f"{luot.ma} (chế độ {TEN_CHE_DO.get(luot.che_do, luot.che_do)}, model {luot.model})", None),
    ]
    bang = doc.add_table(rows=0, cols=2, style="Table Grid")
    for nhan, gia_tri, canh_bao in thong_tin:
        o = bang.add_row().cells
        _chu(o[0].paragraphs[0], nhan, dam=True)
        _chu(o[1].paragraphs[0], gia_tri)
        if canh_bao:
            _chu(o[1].add_paragraph(), canh_bao, nghieng=True, mau=RGBColor(0xC0, 0x00, 0x00))
    _do_rong(bang, [Cm(4.5), Cm(12.5)])

    # Tổng hợp
    doc.add_paragraph()
    _chu(doc.add_paragraph(), "TỔNG HỢP KẾT QUẢ", dam=True)
    tong_hop = doc.add_table(rows=1, cols=3, style="Table Grid")
    for o, nhan in zip(tong_hop.rows[0].cells, ("Mục", "Câu hỏi", "Kết quả")):
        _chu(o.paragraphs[0], nhan, dam=True)
    muc = sorted(luot.muc, key=lambda m: m.so)
    for m in muc:
        o = tong_hop.add_row().cells
        ket_qua, chu_ket_qua = _ket_qua(m, duyet.get(m.so))
        _chu(o[0].paragraphs[0], str(m.so))
        _chu(o[1].paragraphs[0], m.cau_hoi)
        _chu(o[2].paragraphs[0], chu_ket_qua)
        _nen(o[2], NEN_KET_QUA.get(ket_qua, NEN_CHUA_DANH_GIA))
    _do_rong(tong_hop, [Cm(1.3), Cm(11.2), Cm(4.5)])

    # Từng Mục theo bố cục checklist
    muc_checklist = {mc.so: mc for mc in checklist.muc}
    for m in muc:
        doc.add_paragraph()
        _bang_muc(doc, m, muc_checklist.get(m.so), duyet.get(m.so), van_ban, checklist)

    _phu_luc(doc, muc, duyet)
    ra = io.BytesIO()
    doc.save(ra)
    return ra.getvalue()


def ten_file_bao_cao(luot: KetQuaLuot, duyet: dict[int, KetQuaDuyet]) -> str:
    """Ví dụ "Bao-cao-tham-dinh_HD-TOSS_20261031.docx": chữ không dấu, tránh lỗi tên file trên trình duyệt."""
    ten = unicodedata.normalize("NFD", Path(luot.ten_file).stem.replace("Đ", "D").replace("đ", "d"))
    ten = re.sub(r"[^A-Za-z0-9.]+", "-", "".join(c for c in ten if not unicodedata.combining(c))).strip("-")
    return f"Bao-cao-tham-dinh_{ten}_{_ngay_tham_dinh(luot, duyet):%Y%m%d}.docx"


def _ngay_tham_dinh(luot: KetQuaLuot, duyet: dict[int, KetQuaDuyet]) -> datetime:
    """Ngày duyệt gần nhất; chưa duyệt thì ngày Lượt chạy xong."""
    return datetime.fromisoformat(max((d.thoi_diem for d in duyet.values()), default=luot.ket_thuc))


def _ket_qua(m: KetQuaMucDeXuat, da: KetQuaDuyet | None) -> tuple[str | None, str]:
    if da:
        return da.ket_qua, TEN_KET_QUA[da.ket_qua]
    if m.ket_qua:
        return m.ket_qua.ket_qua, f"{TEN_KET_QUA[m.ket_qua.ket_qua]} (đề xuất, chưa duyệt)"
    return None, "Chưa đánh giá được"


def _bang_muc(
    doc, m: KetQuaMucDeXuat, mc, da: KetQuaDuyet | None, van_ban: VanBanHieuLuc, checklist: PhienBanChecklist
) -> None:
    bang = doc.add_table(rows=1, cols=2, style="Table Grid")
    dau = bang.cell(0, 0).merge(bang.cell(0, 1))
    _chu(dau.paragraphs[0], f"{m.so}. {m.cau_hoi}", dam=True)
    _nen(dau, NEN_CAU_HOI)

    for ma, nhan in (("dat", "Đạt"), ("luu_y", "Lưu ý"), ("vi_pham", "Vi phạm")):
        o = bang.add_row().cells
        _chu(o[0].paragraphs[0], nhan, dam=True)
        _nen(o[0], NEN_KET_QUA[ma])
        tieu_chi = mc.tieu_chi.get(ma, []) if mc else []
        _doan(o[1], [f"- {mo_ta_de_doc(tc.mo_ta, checklist)}" for tc in tieu_chi] or ["—"])

    ket_qua, chu_ket_qua = _ket_qua(m, da)
    o = bang.add_row().cells
    _chu(o[0].paragraphs[0], "Kết quả", dam=True)
    _chu(o[1].paragraphs[0], chu_ket_qua if ket_qua or not m.loi else f"{chu_ket_qua}: {m.loi}", dam=True)
    _nen(o[1], NEN_KET_QUA.get(ket_qua, NEN_CHUA_DANH_GIA))

    o = bang.add_row().cells
    _chu(o[0].paragraphs[0], "Giải thích", dam=True)
    if da:
        _doan(o[1], [da.giai_thich or "—"])
    else:
        _doan(o[1], [m.ket_qua.giai_thich, *m.ket_qua.ghi_chu] if m.ket_qua else ["—"])

    o = bang.add_row().cells
    _chu(o[0].paragraphs[0], "Trích dẫn", dam=True)
    if da:
        trich_dan = list(da.trich_dan)
    else:
        trich_dan = list({(t.so_hieu, t.nguyen_van): t for tc in m.tieu_chi for t in tc.trich_dan}.values())
    _doan(o[1], [_trich_dan(t, van_ban) for t in trich_dan] or ["Không có"])
    _do_rong(bang, [Cm(2.8), Cm(14.2)])


def _trich_dan(td, van_ban: VanBanHieuLuc) -> str:
    if td.trang_thai == KHONG_XAC_MINH_DUOC:
        return f"“{td.nguyen_van}”, ghi là {td.so_hieu} (không xác minh được trong Văn bản hiệu lực)"
    return f"“{td.nguyen_van}” ({_vi_tri(td, van_ban)})"


def _vi_tri(td, van_ban: VanBanHieuLuc) -> str:
    """Ví dụ "khoản 4.3.2, trang 3": số hiệu của Điều khoản chứa câu trích (nhiều Điều khoản thì số hiệu được trích)."""
    chua = dieu_khoan_chua_trich_dan(td, van_ban)
    so_hieu = chua[0].so_hieu if len(chua) == 1 else (td.so_hieu_dung or td.so_hieu)
    if so_hieu[:1].isdigit():
        so_hieu = f"khoản {so_hieu}"
    trang = sorted({v[0] for dk in chua for v in dk.vung}
                   or {t for dk in chua for t in range(dk.trang_bat_dau, dk.trang_ket_thuc + 1)})
    if not trang:
        return so_hieu
    if len(trang) == 1:
        return f"{so_hieu}, trang {trang[0]}"
    if trang == list(range(trang[0], trang[-1] + 1)):
        return f"{so_hieu}, trang {trang[0]}–{trang[-1]}"
    return f"{so_hieu}, trang {', '.join(map(str, trang))}"


def _phu_luc(doc, muc: list[KetQuaMucDeXuat], duyet: dict[int, KetQuaDuyet]) -> None:
    khac = [m for m in muc if m.so in duyet and duyet[m.so].ket_qua != (m.ket_qua.ket_qua if m.ket_qua else None)]
    doc.add_page_break()
    _chu(doc.add_paragraph(), "PHỤ LỤC: CÁC MỤC CÓ KẾT QUẢ ĐÃ DUYỆT KHÁC KẾT QUẢ ĐỀ XUẤT", dam=True)
    if not khac:
        _chu(doc.add_paragraph(), "Không có Mục nào.")
        return
    tieu_de = ("Mục", "Kết quả đề xuất", "Kết quả đã duyệt", "Giải thích của hệ thống",
               "Giải thích của Người thẩm định", "Người duyệt")
    bang = doc.add_table(rows=1, cols=len(tieu_de), style="Table Grid")
    for o, nhan in zip(bang.rows[0].cells, tieu_de):
        _chu(o.paragraphs[0], nhan, dam=True, co=10)
    for m in khac:
        da = duyet[m.so]
        o = bang.add_row().cells
        de_xuat = m.ket_qua.ket_qua if m.ket_qua else None
        gia_tri = (str(m.so), TEN_KET_QUA[de_xuat] if de_xuat else "Chưa đánh giá được", TEN_KET_QUA[da.ket_qua],
                   m.ket_qua.giai_thich if m.ket_qua else (m.loi or ""), da.giai_thich,
                   f"{da.nguoi_duyet}, {datetime.fromisoformat(da.thoi_diem):%d/%m/%Y %H:%M}")
        for i, (o_i, v) in enumerate(zip(o, gia_tri)):
            _chu(o_i.paragraphs[0], v, co=10)
            if i in (1, 2):
                _nen(o_i, NEN_KET_QUA.get(de_xuat if i == 1 else da.ket_qua, NEN_CHUA_DANH_GIA))
    _do_rong(bang, [Cm(1.1), Cm(2.2), Cm(2.2), Cm(4.4), Cm(4.4), Cm(2.7)])


# ---- định dạng ----


def _dinh_dang(doc) -> None:
    phan = doc.sections[0]
    phan.orientation = WD_ORIENT.PORTRAIT
    phan.page_width, phan.page_height = Cm(21), Cm(29.7)
    phan.left_margin = phan.right_margin = Cm(2)
    phan.top_margin = phan.bottom_margin = Cm(2)
    kieu = doc.styles["Normal"]
    kieu.font.name = FONT
    kieu.font.size = Pt(12)
    rfonts = kieu.element.get_or_add_rPr().get_or_add_rFonts()
    for thuoc_tinh in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(thuoc_tinh), FONT)
    kieu.paragraph_format.space_after = Pt(2)


def _chu(doan, van_ban: str, dam=False, nghieng=False, co: int | None = None, mau: RGBColor | None = None):
    chu = doan.add_run(van_ban)
    chu.bold, chu.italic = dam, nghieng
    if co:
        chu.font.size = Pt(co)
    if mau:
        chu.font.color.rgb = mau
    return chu


def _doan(o, dong: list[str]) -> None:
    _chu(o.paragraphs[0], dong[0])
    for d in dong[1:]:
        _chu(o.add_paragraph(), d)


def _nen(o, mau: str) -> None:
    tc_pr = o._tc.get_or_add_tcPr()
    for cu in tc_pr.findall(qn("w:shd")):
        tc_pr.remove(cu)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), mau)
    tc_pr.append(shd)


def _do_rong(bang, rong: list) -> None:
    bang.autofit = False
    for hang in bang.rows:
        for o, r in zip(hang.cells, rong):
            o.width = r
