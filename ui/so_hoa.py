"""Bước 1 trên giao diện: tải Dự thảo, Số hóa, xem song song ảnh trang và Điều khoản, sửa tay Điều khoản (issue 06)."""

import shutil
import tempfile
from pathlib import Path

import streamlit as st

from thamdinh.anh_trang import anh_trang
from thamdinh.checklist import load_checklist
from thamdinh.settings import load_settings
from thamdinh.so_hoa import VanBanHieuLuc, so_hoa
from thamdinh.so_hoa.ocr import BoOCRMacDinh
from thamdinh.so_hoa.van_ban import (
    danh_sach_van_ban,
    dieu_khoan_da_sua,
    dieu_khoan_tren_trang,
    duong_dan_pdf,
    luu_van_ban,
    nap_van_ban,
    nap_van_ban_goc,
    sua_dieu_khoan,
)

THU_MUC_CHECKLIST = Path(__file__).resolve().parent.parent / "checklists"

settings = load_settings()


@st.cache_data(show_spinner=False)
def ten_checklist(duong_dan: str) -> str:
    ck = load_checklist(duong_dan)
    return f"{ck.ten} V{ck.phien_ban}"


@st.cache_data(show_spinner=False, max_entries=64)
def anh(duong_dan: str, so: int):
    return anh_trang(duong_dan, so)


def chay_so_hoa(duong_dan: Path, lam_lai: bool = False) -> VanBanHieuLuc | None:
    with st.status(f"Đang số hóa {duong_dan.name}…", expanded=True) as trang_thai:
        try:
            van_ban = so_hoa(
                duong_dan, thu_muc_luu=settings.data_dir, lam_lai=lam_lai, tien_trinh=trang_thai.write,
                bo_ocr=BoOCRMacDinh(settings.thu_muc_model_ocr, settings.ocr_model),
            )
        except FileNotFoundError as e:  # thiếu model OCR
            trang_thai.update(label="Số hóa không thành công", state="error")
            st.error(str(e))
            return None
        trang_thai.update(
            label=f"Đã số hóa {duong_dan.name}: {len(van_ban.trang)} trang, {len(van_ban.dieu_khoan)} Điều khoản",
            state="complete", expanded=False,
        )
    return van_ban


def luu_dieu_khoan(hash_pdf: str, ma: int) -> None:
    """Callback nút Lưu: chạy trước khi trang vẽ lại, nên trang thấy ngay bản đã sửa."""
    try:
        van_ban = sua_dieu_khoan(
            nap_van_ban(hash_pdf, settings.data_dir), ma, st.session_state[f"noi_dung_{hash_pdf}_{ma}"]
        )
    except ValueError as e:
        st.session_state[f"thong_bao_{hash_pdf}_{ma}"] = ("error", f"Chưa lưu: {e}")
        return
    luu_van_ban(van_ban, settings.data_dir)
    st.session_state[f"thong_bao_{hash_pdf}_{ma}"] = ("success", "Đã lưu vào Văn bản hiệu lực.")


def bo_noi_dung_dang_sua(hash_pdf: str) -> None:
    for khoa in [k for k in st.session_state if str(k).startswith(f"noi_dung_{hash_pdf}_")]:
        del st.session_state[khoa]


st.title("Số hóa")
st.caption("Tải Dự thảo (PDF), chọn Phiên bản checklist và tạo Văn bản hiệu lực.")

# Phiên bản checklist: lưu sang khóa riêng vì Streamlit xóa trạng thái widget khi chuyển trang (trang Thẩm định dùng).
cac_checklist = [str(p) for p in sorted(THU_MUC_CHECKLIST.glob("*.yaml"))]
st.session_state["phien_ban_checklist"] = st.selectbox(
    "Phiên bản checklist", cac_checklist, format_func=ten_checklist, key="checklist"
)

tep = st.file_uploader("Dự thảo (PDF)", type=["pdf"], key="tai_len")
if tep is not None and st.button("Số hóa", key="so_hoa", type="primary"):
    with tempfile.TemporaryDirectory() as tam:
        duong_dan = Path(tam) / tep.name
        duong_dan.write_bytes(tep.getvalue())
        if van_ban := chay_so_hoa(duong_dan):
            st.session_state["van_ban"] = van_ban.hash_pdf

ds = {v.hash_pdf: v for v in danh_sach_van_ban(settings.data_dir)}
if not ds:
    st.info("Chưa có Văn bản hiệu lực nào. Tải Dự thảo (PDF) lên rồi bấm Số hóa.")
    st.stop()

hash_pdf = st.selectbox(
    "Văn bản đã số hóa",
    list(ds),
    format_func=lambda h: f"{ds[h].ten_file} · {ds[h].so_trang} trang, {ds[h].so_trang_tin_cay_thap} trang tin cậy thấp",
    key="van_ban",
)
st.session_state["van_ban_dang_mo"] = hash_pdf  # trang Thẩm định chọn sẵn văn bản này
van_ban = nap_van_ban(hash_pdf, settings.data_dir)
da_sua = dieu_khoan_da_sua(van_ban, nap_van_ban_goc(hash_pdf, settings.data_dir))
pdf = duong_dan_pdf(hash_pdf, settings.data_dir)

if van_ban.canh_bao:
    with st.expander(f"Cảnh báo cấu trúc ({len(van_ban.canh_bao)})"):
        for c in van_ban.canh_bao:
            st.markdown(f"- {c}")

if pdf.is_file():
    if st.button("Số hóa lại từ đầu", key="lam_lai"):
        st.session_state["xac_nhan_lam_lai"] = hash_pdf
    if st.session_state.get("xac_nhan_lam_lai") == hash_pdf:
        st.warning(
            "Số hóa lại sẽ bỏ các Điều khoản đã sửa tay trong bản đang dùng (các bản cũ vẫn lưu, Lượt thẩm định cũ "
            "vẫn mở được). Với PDF cần OCR, việc này mất khoảng 1 phút mỗi trang."
        )
        if st.button("Xác nhận số hóa lại", key="xac_nhan", type="primary"):
            del st.session_state["xac_nhan_lam_lai"]
            with tempfile.TemporaryDirectory() as tam:
                ban_chep = Path(tam) / van_ban.ten_file
                shutil.copyfile(pdf, ban_chep)
                if chay_so_hoa(ban_chep, lam_lai=True):
                    bo_noi_dung_dang_sua(hash_pdf)
                    st.rerun()

# Chọn trang, có lọc trang tin cậy thấp
chi_tin_cay_thap = st.checkbox("Chỉ trang tin cậy thấp", key="chi_tin_cay_thap")
trang = {t.so: t for t in van_ban.trang}
cac_trang = [so for so, t in trang.items() if t.tin_cay_thap or not chi_tin_cay_thap]
if not cac_trang:
    st.info("Không có trang tin cậy thấp.")
    st.stop()
so = st.selectbox(
    "Trang",
    cac_trang,
    format_func=lambda s: f"Trang {s}" + (" (tin cậy thấp)" if trang[s].tin_cay_thap else ""),
    key="trang",
)
nguon = "OCR" if trang[so].nguon == "ocr" else "lớp text"
if trang[so].tin_cay_thap:
    st.warning(f"Trang {so} tin cậy thấp (đọc bằng {nguon}): " + "; ".join(trang[so].ly_do))
else:
    st.caption(f"Trang {so} đọc bằng {nguon}.")

trai, phai = st.columns(2)
with trai:
    if pdf.is_file():
        st.image(anh(str(pdf), so), width="stretch")
    else:
        st.info("Không có file PDF gốc trong thư mục dữ liệu, chỉ xem được text.")
with phai:
    for dk in dieu_khoan_tren_trang(van_ban, so):
        nhan = " · ".join(x for x in (dk.so_hieu, dk.tieu_de, "đã sửa tay" if dk.ma in da_sua else None) if x)
        with st.expander(nhan, expanded=True):
            khoa = f"{hash_pdf}_{dk.ma}"
            if dk.trang_bat_dau != dk.trang_ket_thuc:
                st.caption(f"Trang {dk.trang_bat_dau}–{dk.trang_ket_thuc}")
            st.text_area(
                "Nội dung", value=dk.noi_dung, key=f"noi_dung_{khoa}", label_visibility="collapsed",
                height=min(600, 70 + 24 * (len(dk.noi_dung) // 70 + dk.noi_dung.count("\n"))),
            )
            st.button("Lưu", key=f"luu_{khoa}", on_click=luu_dieu_khoan, args=(hash_pdf, dk.ma))
            if thong_bao := st.session_state.pop(f"thong_bao_{khoa}", None):
                (st.error if thong_bao[0] == "error" else st.success)(thong_bao[1])
