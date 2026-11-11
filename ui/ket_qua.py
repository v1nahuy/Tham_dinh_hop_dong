"""Bước 3 trên giao diện: xem Kết quả đề xuất của một Lượt và duyệt thành Kết quả đã duyệt (issue 11)."""

import pandas as pd
import streamlit as st

from pathlib import Path

from thamdinh.anh_trang import anh_trang
from thamdinh.bang_ket_qua import bang_ket_qua
from thamdinh.bao_cao import so_hop_dong, tao_bao_cao, ten_file_bao_cao
from thamdinh.checklist import load_checklist, mo_ta_de_doc, tim_checklist
from thamdinh.kho_luot import KhoLuot
from thamdinh.luot import DinhDangLuotError
from thamdinh.settings import load_settings
from thamdinh.so_hoa.van_ban import duong_dan_pdf, nap_van_ban
from thamdinh.tong_hop import TEN_KET_QUA
from thamdinh.trich_dan import KHONG_XAC_MINH_DUOC, KHOP_SAI_SO_HIEU, TrichDan, vung_trich_dan

MAU = {"dat": "green", "luu_y": "orange", "vi_pham": "red"}
NEN = {"Đạt": "#c6efce", "Lưu ý": "#ffeb9c", "Vi phạm": "#ffc7ce"}  # màu ô Kết quả như checklist
TEN_DANH_GIA = {"thoa": "thỏa", "khong_thoa": "không thỏa", "khong_ro": "không rõ"}
TEN_CHE_DO = {"toan_van": "toàn văn", "truy_xuat": "truy xuất"}
THU_MUC_CHECKLIST = Path(__file__).resolve().parent.parent / "checklists"

settings = load_settings()
kho = KhoLuot(settings.data_dir)


def nhan_mau(ma: str | None) -> str:
    return f":{MAU[ma]}[{TEN_KET_QUA[ma]}]" if ma else ":gray[chưa đánh giá được]"


@st.cache_data(show_spinner=False, max_entries=32)
def anh(pdf: str, so: int, vung: tuple) -> object:
    return anh_trang(pdf, so, vung)


@st.cache_resource(show_spinner=False)
def checklist_cua(ma_phien_ban: str):
    return load_checklist(tim_checklist(THU_MUC_CHECKLIST, ma_phien_ban))


@st.cache_data(show_spinner="Đang tạo báo cáo…", max_entries=8)
def bao_cao(thu_muc: str, ma: str, phien_ban_duyet: tuple, so_hd: str, canh_bao: str | None) -> bytes:
    """Tạo lại chỉ khi Lượt, các phiên bản duyệt hoặc số hợp đồng đổi (tạo một báo cáo mất khoảng 0,5 giây)."""
    kho_ = KhoLuot(thu_muc)
    luot_ = kho_.nap(ma)
    van_ban_ = nap_van_ban(luot_.hash_pdf, thu_muc, luot_.hash_van_ban)
    checklist = load_checklist(tim_checklist(THU_MUC_CHECKLIST, luot_.checklist))
    return tao_bao_cao(luot_, kho_.nap_duyet(ma), van_ban_, checklist, so_hd, canh_bao)


@st.dialog("Vị trí Trích dẫn", width="large")
def xem_trang(pdf: str, vung: tuple, tieu_de: str) -> None:
    st.caption(f"{tieu_de} (tô vùng Điều khoản chứa câu trích)")
    for so in sorted({v[0] for v in vung}):
        st.image(anh(pdf, so, vung), caption=f"Trang {so}", width="stretch")


st.title("Kết quả")
st.caption("Duyệt Kết quả đề xuất thành Kết quả đã duyệt và xuất báo cáo.")

if thong_bao := st.session_state.pop("thong_bao_duyet", None):
    st.success(thong_bao)

ds = {t.ma: t for t in kho.danh_sach()}
if not ds:
    st.info("Chưa có Lượt thẩm định nào. Chạy Thẩm định ở bước trước.")
    st.stop()

mac_dinh = st.session_state.get("luot_dang_mo")
ma = st.selectbox(
    "Lượt thẩm định",
    list(ds),
    index=list(ds).index(mac_dinh) if mac_dinh in ds else 0,
    format_func=lambda m: (f"{ds[m].ten_file} · {ds[m].bat_dau[:16].replace('T', ' ')} · "
                           f"{ds[m].so_muc_xong}/{ds[m].so_muc} Mục · đã duyệt {ds[m].so_muc_da_duyet}"),
    key="luot",
)
st.session_state["luot_dang_mo"] = ma
try:
    luot = kho.nap(ma)
except DinhDangLuotError as e:  # Lượt lưu bằng code khác (thử nghiệm đã revert)
    st.error(f"Không mở được Lượt: {e}")
    st.stop()
duyet = kho.nap_duyet(ma)
van_ban = nap_van_ban(luot.hash_pdf, settings.data_dir, luot.hash_van_ban)
pdf = duong_dan_pdf(luot.hash_pdf, settings.data_dir)
ck = checklist_cua(luot.checklist)

thong_tin = [
    f"Phiên bản checklist {luot.checklist}", f"chế độ {TEN_CHE_DO.get(luot.che_do, luot.che_do)}", f"model {luot.model}",
    f"chạy {luot.bat_dau[:16].replace('T', ' ')} – {luot.ket_thuc[:16].replace('T', ' ')}",
]
if luot.luot_goc:
    thong_tin.append(f"tạo từ Lượt {luot.luot_goc}")
st.caption(" · ".join(thong_tin))
if luot.cac_ben:
    st.markdown(f"**Công ty:** {luot.cac_ben.ten_cong_ty} ({luot.cac_ben.cong_ty}) · "
                f"**Khách hàng:** {luot.cac_ben.ten_khach_hang}")
else:
    st.warning(f"Chưa xác định được các bên: {luot.loi_cac_ben}")
for c in luot.canh_bao:
    st.warning(c)
if van_ban is None:
    st.warning("Không tìm thấy Văn bản hiệu lực mà Lượt đã dùng, nên không kiểm tra Trích dẫn và không duyệt được.")

st.session_state.setdefault("ten_nguoi_duyet", settings.nguoi_duyet)
st.session_state["ten_nguoi_duyet"] = st.text_input(
    "Người thẩm định", value=st.session_state["ten_nguoi_duyet"], key="nguoi_duyet",
    help="Ghi vào Kết quả đã duyệt. Đặt sẵn bằng THAMDINH_NGUOI_DUYET trong .env.",
).strip()

# Bảng 17 Mục
bang = bang_ket_qua(luot, duyet)
df = pd.DataFrame(
    {
        "Mục": [d.so for d in bang],
        "Câu hỏi": [d.cau_hoi for d in bang],
        "Đề xuất": [TEN_KET_QUA[d.de_xuat] if d.de_xuat else "Chưa đánh giá được" for d in bang],
        "Đã duyệt": [TEN_KET_QUA[d.da_duyet] if d.da_duyet else "" for d in bang],
        "Trích dẫn không xác minh được": [d.khong_xac_minh for d in bang],
        "Lỗi": [d.loi or "" for d in bang],
    }
)
st.dataframe(
    df.style.map(lambda v: f"background-color: {NEN[v]}; color: #1f1f1f" if v in NEN else "",
                 subset=["Đề xuất", "Đã duyệt"]),
    hide_index=True,
    alt="Kết quả từng Mục checklist",
)

# Báo cáo .docx (issue 12): Mục chưa duyệt lấy Kết quả đề xuất, ghi rõ chưa duyệt
st.subheader("Báo cáo")
if van_ban is None:
    st.caption("Không tạo được báo cáo vì thiếu Văn bản hiệu lực mà Lượt đã dùng.")
else:
    so = so_hop_dong(van_ban)
    so_hd = st.text_input("Số hợp đồng", value=so.gia_tri, key=f"so_hop_dong_{ma}",
                          help="Tự dò trong Văn bản hiệu lực; sửa lại nếu cần trước khi tải báo cáo.").strip()
    canh_bao_so = so.canh_bao if so_hd == so.gia_tri else None
    if canh_bao_so:
        st.warning(canh_bao_so)
    if len(duyet) < len(luot.muc):
        st.caption(f"{len(duyet)}/{len(luot.muc)} Mục đã duyệt; Mục chưa duyệt ghi Kết quả đề xuất kèm \"(đề xuất, "
                   "chưa duyệt)\".")
    st.download_button(
        "Tải báo cáo (.docx)",
        data=bao_cao(str(settings.data_dir), ma, tuple(sorted((s, d.phien_ban) for s, d in duyet.items())), so_hd,
                     canh_bao_so),
        file_name=ten_file_bao_cao(luot, duyet),
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        key="tai_bao_cao", icon=":material/download:",
    )

# Chi tiết và duyệt từng Mục
for m in sorted(luot.muc, key=lambda m: m.so):
    da = duyet.get(m.so)
    nhan = f"Mục {m.so} · {nhan_mau(m.ket_qua.ket_qua if m.ket_qua else None)}"
    if da:
        nhan += f" → đã duyệt {nhan_mau(da.ket_qua)}"
    with st.expander(f"{nhan} · {m.cau_hoi}"):
        if m.loi:
            st.error(m.loi)
        if m.ket_qua:
            st.markdown(f"**Kết quả đề xuất:** {nhan_mau(m.ket_qua.ket_qua)}. {m.ket_qua.giai_thich}")
            for g in m.ket_qua.ghi_chu:
                st.caption(g)
        for i, tc in enumerate(m.tieu_chi):
            with st.container(border=True):
                danh_gia = TEN_DANH_GIA.get(tc.danh_gia, tc.danh_gia)
                if tc.danh_gia_llm != tc.danh_gia:
                    danh_gia += f" (model trả lời {TEN_DANH_GIA.get(tc.danh_gia_llm, tc.danh_gia_llm)})"
                st.markdown(f"**{tc.ma}** · tiêu chí {TEN_KET_QUA[tc.muc_ket_qua]}: {mo_ta_de_doc(tc.mo_ta, ck)}  \n"
                            f"Đánh giá tiêu chí: **{danh_gia}**")
                if tc.gia_tri is not None or tc.gia_tri_dieu_kien is not None:
                    st.markdown(f"Giá trị trích xuất: {tc.gia_tri}"
                                + (f" · giá trị điều kiện: {tc.gia_tri_dieu_kien:,.0f}"
                                   if tc.gia_tri_dieu_kien is not None else ""))
                st.caption(tc.ly_do)
                for j, td in enumerate(tc.trich_dan):
                    if td.trang_thai == KHONG_XAC_MINH_DUOC:
                        trang_thai = ":red[không xác minh được]"
                    elif td.trang_thai == KHOP_SAI_SO_HIEU:
                        trang_thai = f":orange[có trong văn bản nhưng ở {td.so_hieu_dung}]"
                    else:
                        trang_thai = ":green[đã xác minh]"
                    trai, phai = st.columns([5, 1], vertical_alignment="center")
                    trai.markdown(f"**{td.so_hieu}**: “{td.nguyen_van}” · {trang_thai}")
                    vung = tuple(vung_trich_dan(td, van_ban)) if van_ban else ()
                    if vung and pdf.is_file() and phai.button("Xem trang", key=f"xem_{m.so}_{i}_{j}",
                                                              icon=":material/description:"):
                        xem_trang(str(pdf), vung, f"{td.so_hieu}: “{td.nguyen_van}”")
        if m.dieu_khoan_dua_vao and luot.che_do == "truy_xuat":
            st.caption("Điều khoản model đã đọc: " + ", ".join(m.dieu_khoan_dua_vao))
        for c in m.canh_bao:
            st.caption(f":orange[{c}]")

        # Duyệt: mặc định theo bản duyệt gần nhất, chưa duyệt thì theo Kết quả đề xuất
        st.markdown("**Duyệt**")
        if da:
            trich_dan = [(t.so_hieu, t.nguyen_van) for t in da.trich_dan]
        else:
            trich_dan = list(dict.fromkeys((t.so_hieu, t.nguyen_van) for tc in m.tieu_chi for t in tc.trich_dan))
        with st.form(f"duyet_{ma}_{m.so}", border=False):
            ket_qua = st.segmented_control(
                "Kết quả", list(TEN_KET_QUA), format_func=TEN_KET_QUA.get, key=f"kq_{ma}_{m.so}",
                default=da.ket_qua if da else (m.ket_qua.ket_qua if m.ket_qua else None),
            )
            giai_thich = st.text_area(
                "Giải thích", key=f"giai_thich_{ma}_{m.so}",
                value=da.giai_thich if da else (m.ket_qua.giai_thich if m.ket_qua else ""),
            )
            bang_trich_dan = st.data_editor(
                pd.DataFrame(trich_dan, columns=["so_hieu", "nguyen_van"]),
                column_config={"so_hieu": st.column_config.TextColumn("Số hiệu", width="small"),
                               "nguyen_van": st.column_config.TextColumn("Nguyên văn", width="large")},
                num_rows="dynamic", hide_index=True, key=f"trich_dan_{ma}_{m.so}", width="stretch",
            )
            luu = st.form_submit_button("Lưu Kết quả đã duyệt", key=f"luu_duyet_{ma}_{m.so}", type="primary",
                                        disabled=van_ban is None)
        if luu:
            nguoi_duyet = st.session_state["ten_nguoi_duyet"]
            if not nguoi_duyet:
                st.error("Chưa nhập tên người thẩm định (ô phía trên bảng), chưa lưu.")
            elif ket_qua is None:
                st.error("Chọn Kết quả trước khi lưu.")
            else:
                cac_trich_dan = [
                    TrichDan(str(r.so_hieu or "").strip(), str(r.nguyen_van).strip())
                    for r in bang_trich_dan.itertuples() if str(r.nguyen_van or "").strip()
                ]
                try:
                    phien_ban = kho.luu_duyet(ma, m.so, ket_qua, giai_thich, cac_trich_dan, nguoi_duyet, van_ban)
                except ValueError as e:
                    st.error(f"Chưa lưu: {e}")
                else:
                    st.session_state["thong_bao_duyet"] = (
                        f"Đã lưu Kết quả đã duyệt Mục {m.so} (phiên bản {phien_ban.phien_ban})."
                    )
                    st.rerun()
        if lich_su := kho.lich_su_duyet(ma, m.so):
            st.markdown("**Lịch sử duyệt**  \n" + "  \n".join(
                f"Phiên bản {v.phien_ban} · {v.thoi_diem.replace('T', ' ')} · {v.nguoi_duyet}: "
                f"{nhan_mau(v.ket_qua)}. {v.giai_thich}"
                for v in reversed(lich_su)
            ))
