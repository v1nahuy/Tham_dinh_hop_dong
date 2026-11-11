"""Bước 2 trên giao diện: chạy Lượt thẩm định ở tiến trình nền, theo dõi tiến độ, chạy lại phần lỗi (issue 11).

Lượt chạy ở tiến trình riêng (`thamdinh.chay_nen`), nên đóng trình duyệt vẫn chạy tiếp; mỗi lúc chỉ một Lượt.
"""

from pathlib import Path

import streamlit as st

from thamdinh import chay_nen
from thamdinh.checklist import load_checklist, tim_checklist
from thamdinh.kho_luot import KhoLuot
from thamdinh.llm import LocalClient
from thamdinh.luot import DinhDangLuotError
from thamdinh.settings import load_settings
from thamdinh.so_hoa.van_ban import danh_sach_van_ban, duong_dan_pdf
from thamdinh.truy_xuat import LocalEmbeddingClient

THU_MUC_CHECKLIST = Path(__file__).resolve().parent.parent / "checklists"
TEN_CHE_DO = {"toan_van": "Toàn văn", "truy_xuat": "Truy xuất"}
LENH_MAY_CHU = (
    r"models\llama.cpp\cpu\llama-server.exe -m models\qwen\Qwen3.5-9B-Q4_K_M.gguf --alias qwen3.5 "
    "--host 127.0.0.1 --port 8080 -c 49152 -fa on -ctk q8_0 -ctv q8_0 --jinja -np 1"
)

settings = load_settings()
kho = KhoLuot(settings.data_dir)


@st.cache_data(show_spinner=False)
def ten_checklist(duong_dan: str) -> str:
    ck = load_checklist(duong_dan)
    return f"{ck.ten} V{ck.phien_ban}"


@st.cache_data(show_spinner=False)
def so_muc_checklist(ma_phien_ban: str) -> int:
    return len(load_checklist(tim_checklist(THU_MUC_CHECKLIST, ma_phien_ban)).muc)


def may_chu_san_sang(che_do: str) -> bool:
    """Q77: chưa có Qwen thì không chạy; chưa có bge-m3 (chế độ truy xuất) thì chỉ cảnh báo."""
    if not LocalClient(settings.local_url, settings.model).san_sang():
        st.error(
            f"Chưa chạy máy chủ model llama-server tại {settings.local_url} (hoặc đang nạp model). "
            "Mở một cửa sổ lệnh ở thư mục dự án, chạy lệnh dưới đây (xem docs/chay-model-local.md), chờ dòng "
            "\"listening on\" rồi bấm lại."
        )
        st.code(LENH_MAY_CHU, language=None)
        return False
    if che_do == "truy_xuat" and not LocalEmbeddingClient(settings.embedding_url, settings.embedding_model).san_sang():
        st.session_state["thong_bao_chay"] = (
            "Máy chủ embedding bge-m3 chưa chạy: lưới an toàn của chế độ truy xuất chỉ dùng BM25 (Lượt có ghi cảnh báo)."
        )
    return True


def khoi_chay(doi_so: list[str]) -> None:
    try:
        chay_nen.khoi_chay(doi_so, settings.data_dir)
    except chay_nen.DangChayError as e:
        st.error(str(e))
        return
    st.rerun()


st.title("Thẩm định")
st.caption("Đối chiếu Văn bản hiệu lực với từng Mục checklist để tạo Kết quả đề xuất.")

tt = chay_nen.trang_thai(settings.data_dir)
dang_chay = bool(tt and tt.dang_chay)
st.session_state["dang_chay_truoc"] = dang_chay
if thong_bao := st.session_state.pop("thong_bao_chay", None):
    st.warning(thong_bao)


@st.fragment(run_every=10 if dang_chay else None)
def tien_do() -> None:
    tt = chay_nen.trang_thai(settings.data_dir)
    if tt is None:
        return
    if tt.dang_chay:
        bat_dau = tt.bat_dau.replace("T", " ")
        try:
            luot = kho.nap(tt.ma_luot) if tt.ma_luot else None
        except KeyError:
            luot = None
        if luot:
            xong = sum(m.ket_qua is not None for m in luot.muc)
            st.info(f"Đang chạy Lượt {luot.ma} ({luot.ten_file}): {xong}/{so_muc_checklist(luot.checklist)} Mục đã có "
                    f"kết quả. Bắt đầu {bat_dau}; có thể đóng trình duyệt, Lượt vẫn chạy tiếp.",
                    icon=":material/hourglass_top:")
        else:
            st.info(f"Đang chuẩn bị Lượt (số hóa, xác định các bên, gắn Chủ đề…), bắt đầu {bat_dau}.",
                    icon=":material/hourglass_top:")
        st.code("\n".join(tt.dong_cuoi) or "…", language=None)
        st.button("Dừng", key="dung", icon=":material/stop:", on_click=chay_nen.dung, args=(settings.data_dir,),
                  help="Các Mục đã xong vẫn được giữ; chạy tiếp bằng \"Chạy lại phần lỗi\".")
    else:
        if st.session_state.get("dang_chay_truoc"):
            st.session_state["dang_chay_truoc"] = False
            st.rerun(scope="app")  # Lượt vừa xong: làm mới cả trang để bật lại các nút
        with st.expander(f"Nhật ký lần chạy gần nhất (bắt đầu {tt.bat_dau.replace('T', ' ')})"):
            st.code("\n".join(tt.dong_cuoi) or "(trống)", language=None)


tien_do()

# Chạy Lượt mới
st.subheader("Chạy Thẩm định")
van_ban = {v.hash_pdf: v for v in danh_sach_van_ban(settings.data_dir)}
if not van_ban:
    st.info("Chưa có Văn bản hiệu lực. Số hóa Dự thảo ở bước trước.")
else:
    mac_dinh = st.session_state.get("van_ban_dang_mo")
    hash_pdf = st.selectbox(
        "Văn bản hiệu lực", list(van_ban), index=list(van_ban).index(mac_dinh) if mac_dinh in van_ban else 0,
        format_func=lambda h: f"{van_ban[h].ten_file} · {van_ban[h].so_trang} trang", key="van_ban_chay",
    )
    cac_checklist = [str(p) for p in sorted(THU_MUC_CHECKLIST.glob("*.yaml"))]
    mac_dinh = st.session_state.get("phien_ban_checklist")
    checklist = st.selectbox(
        "Phiên bản checklist", cac_checklist,
        index=cac_checklist.index(mac_dinh) if mac_dinh in cac_checklist else 0,
        format_func=ten_checklist, key="checklist_chay",
    )
    che_do = st.segmented_control(
        "Chế độ", list(TEN_CHE_DO), format_func=TEN_CHE_DO.get, default="toan_van", key="che_do",
        required=True,
    )
    st.caption("Toàn văn: model đọc cả Hợp đồng cho mỗi Mục (TOSS trên máy này khoảng 6 giờ). Truy xuất: mỗi Mục "
               "chỉ đọc các Điều khoản liên quan (khoảng 8 giờ); lần đầu gắn Chủ đề mất khoảng 40 phút.")
    if st.button("Chạy Thẩm định", key="chay", type="primary", icon=":material/play_arrow:", disabled=dang_chay):
        pdf = duong_dan_pdf(hash_pdf, settings.data_dir)
        if not pdf.is_file():
            st.error("Không có file PDF gốc trong thư mục dữ liệu; số hóa lại Dự thảo ở bước trước.")
        elif may_chu_san_sang(che_do):
            khoi_chay([str(pdf), "--checklist", checklist, "--che-do", che_do])

# Chạy lại phần lỗi của một Lượt đã có
st.subheader("Chạy lại phần lỗi")
luot_ds = {t.ma: t for t in kho.danh_sach()}
if not luot_ds:
    st.caption("Chưa có Lượt thẩm định nào.")
else:
    mac_dinh = st.session_state.get("luot_dang_mo") or (tt.ma_luot if tt else None)
    ma = st.selectbox(
        "Lượt thẩm định", list(luot_ds), index=list(luot_ds).index(mac_dinh) if mac_dinh in luot_ds else 0,
        format_func=lambda m: (f"{luot_ds[m].ten_file} · {luot_ds[m].bat_dau[:16].replace('T', ' ')} · "
                               f"{luot_ds[m].so_muc_xong}/{luot_ds[m].so_muc} Mục"),
        key="luot_chay_lai",
    )
    st.session_state["luot_dang_mo"] = ma
    try:
        luot = kho.nap(ma)
    except DinhDangLuotError as e:  # Lượt lưu bằng code khác (thử nghiệm đã revert)
        st.error(f"Không mở được Lượt: {e}")
        st.stop()
    loi = [m for m in luot.muc if m.ket_qua is None]
    chua_chay = so_muc_checklist(luot.checklist) - len(luot.muc)
    if luot.cac_ben is None and luot.loi_cac_ben:
        st.error(f"Chưa xác định được các bên: {luot.loi_cac_ben}")
    for m in loi:
        st.error(f"Mục {m.so}: {m.loi}")
    if chua_chay > 0:
        st.warning(f"Còn {chua_chay} Mục chưa chạy (Lượt bị dừng giữa chừng).")
    if not (loi or chua_chay > 0 or luot.cac_ben is None):
        st.success("Mọi Mục của Lượt này đều đã có Kết quả đề xuất.")
    them = st.multiselect(
        "Chọn thêm Mục đã có kết quả để chạy lại", [m.so for m in luot.muc if m.ket_qua is not None],
        format_func=lambda s: f"Mục {s}", key="chay_lai_them",
    )
    if them:
        st.warning("Chạy lại Mục đã có kết quả sẽ tạo Lượt mới (ghi Lượt gốc); Lượt cũ và các Kết quả đã duyệt của "
                   "nó giữ nguyên.")
    co_viec = bool(loi or chua_chay > 0 or luot.cac_ben is None or them)
    if st.button("Chạy lại phần lỗi" + (" và các Mục đã chọn" if them else ""), key="chay_lai",
                 icon=":material/replay:", disabled=dang_chay or not co_viec):
        pdf = duong_dan_pdf(luot.hash_pdf, settings.data_dir)
        if not pdf.is_file():
            st.error("Không có file PDF gốc trong thư mục dữ liệu; số hóa lại Dự thảo ở bước trước.")
        elif may_chu_san_sang(luot.che_do):
            doi_so = [str(pdf), "--checklist", str(tim_checklist(THU_MUC_CHECKLIST, luot.checklist)), "--tiep-tuc", ma]
            if them:
                doi_so += ["--chi-muc", ",".join(map(str, sorted(them)))]
            khoi_chay(doi_so)
