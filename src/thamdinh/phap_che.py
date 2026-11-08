"""Danh sách Tiêu chí mà ba nguồn không thống nhất, dạng .docx gửi pháp chế xem (issue 15)."""

import io
from datetime import date

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm

from thamdinh.bao_cao import NEN_CAU_HOI, _chu, _dinh_dang, _do_rong, _nen, _trich_dan
from thamdinh.bo_chuan import DanhGiaChuan
from thamdinh.checklist import PhienBanChecklist, mo_ta_de_doc
from thamdinh.so_hoa import VanBanHieuLuc
from thamdinh.so_sanh import SoSanhNguon
from thamdinh.tham_dinh import DanhGiaDeXuat
from thamdinh.tong_hop import TEN_DANH_GIA

CO_CHU = 10
TIEU_DE = ("Mã", "Tiêu chí", "Hệ thống, chế độ toàn văn", "Hệ thống, chế độ truy xuất", "Bản điền tay",
           "Kết luận pháp chế")
DO_RONG = [Cm(1.3), Cm(5.5), Cm(5.8), Cm(5.8), Cm(5.0), Cm(3.2)]


class ChuaDuBoChuanError(Exception):
    """Bộ chuẩn chưa điền đủ: chưa đủ ba nguồn để lập danh sách."""


def tao_danh_sach_phap_che(kq: SoSanhNguon, checklist: PhienBanChecklist, van_ban: VanBanHieuLuc) -> bytes:
    if kq.so_tieu_chi_chuan < len(kq.dong):
        raise ChuaDuBoChuanError(f"Bộ chuẩn mới điền {kq.so_tieu_chi_chuan}/{len(kq.dong)} Tiêu chí")
    doc = Document()
    _dinh_dang(doc)
    phan = doc.sections[0]
    phan.orientation = WD_ORIENT.LANDSCAPE
    phan.page_width, phan.page_height = Cm(29.7), Cm(21)
    phan.left_margin = phan.right_margin = Cm(1.5)

    tieu_de = doc.add_paragraph()
    tieu_de.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _chu(tieu_de, "DANH SÁCH TIÊU CHÍ CÁC NGUỒN ĐÁNH GIÁ KHÔNG THỐNG NHẤT", dam=True, co=14)
    _chu(doc.add_paragraph(), f"Hợp đồng: {van_ban.ten_file}")
    _chu(doc.add_paragraph(), f"{len(kq.bat_dong)}/{len(kq.dong)} Tiêu chí không thống nhất, lập ngày {date.today():%d/%m/%Y}.")
    _chu(doc.add_paragraph(), "Đề nghị pháp chế ghi kết luận đúng vào cột cuối.", nghieng=True)

    bang = doc.add_table(rows=1, cols=len(TIEU_DE), style="Table Grid")
    for o, nhan in zip(bang.rows[0].cells, TIEU_DE):
        _chu(o.paragraphs[0], nhan, dam=True, co=CO_CHU)

    cau_hoi = {m.so: m.cau_hoi for m in kq.muc}
    muc_dang = None
    for d in kq.bat_dong:
        if d.so_muc != muc_dang:
            muc_dang = d.so_muc
            o = bang.add_row().cells
            gop = o[0].merge(o[-1])
            _chu(gop.paragraphs[0], f"Mục {d.so_muc}. {cau_hoi[d.so_muc]}", dam=True, co=CO_CHU)
            _nen(gop, NEN_CAU_HOI)
        o = bang.add_row().cells
        _chu(o[0].paragraphs[0], d.ma, co=CO_CHU)
        _chu(o[1].paragraphs[0], mo_ta_de_doc(d.mo_ta, checklist), co=CO_CHU)
        _dong(o[2], _he_thong(d.toan_van, van_ban))
        _dong(o[3], _he_thong(d.truy_xuat, van_ban))
        _dong(o[4], _chuan(d.chuan))
    _do_rong(bang, DO_RONG)

    ra = io.BytesIO()
    doc.save(ra)
    return ra.getvalue()


def _dong(o, dong: list[str]) -> None:
    _chu(o.paragraphs[0], dong[0], dam=True, co=CO_CHU)
    for d in dong[1:]:
        _chu(o.add_paragraph(), d, co=CO_CHU)


def _so(gia_tri: float) -> str:
    return f"{gia_tri:g}" if abs(gia_tri) < 1e6 else f"{gia_tri:.0f}"


def _he_thong(d: DanhGiaDeXuat | None, van_ban: VanBanHieuLuc) -> list[str]:
    if d is None:
        return ["Chưa đánh giá được"]
    dong = [TEN_DANH_GIA[d.danh_gia].capitalize()]
    gia_tri = d.gia_tri if d.gia_tri is not None else d.gia_tri_dieu_kien
    if gia_tri is not None:
        dong.append(f"Giá trị: {_so(gia_tri)}")
    if d.ly_do:
        dong.append(d.ly_do)
    return dong + [_trich_dan(td, van_ban) for td in d.trich_dan]


def _chuan(d: DanhGiaChuan) -> list[str]:
    dong = [TEN_DANH_GIA[d.danh_gia].capitalize()]
    if d.gia_tri is not None:
        dong.append(f"Giá trị: {_so(d.gia_tri)}")
    dong += [f"“{t}”" for t in d.trich_dan]
    if d.vi_tri:
        dong.append(f"Vị trí: {d.vi_tri}")
    if d.ghi_chu:
        dong.append(f"Ghi chú: {d.ghi_chu}")
    return dong
