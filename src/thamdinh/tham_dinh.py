"""Bước 2: Thẩm định Văn bản hiệu lực theo Phiên bản checklist bằng LLM.

Mỗi Mục checklist là một lần gọi LLM. Chế độ toàn văn: prompt có phần đầu cố định (hướng dẫn chung + toàn văn
Hợp đồng) để máy chủ model dùng lại phần đã đọc giữa các Mục; phần riêng của từng Mục đặt ở cuối. Chế độ truy xuất
(`truy_xuat.py`): thay toàn văn bằng các Điều khoản được chọn cho từng Mục.
"""

from collections.abc import Callable, Collection
from dataclasses import replace
from datetime import datetime
from typing import Any, Protocol

import yaml

from thamdinh.checklist import MucChecklist, PhienBanChecklist, TieuChi
from thamdinh.llm import LLMBiCatError, LLMClient, LLMResponseError
from thamdinh.so_hoa import VanBanHieuLuc, hash_noi_dung
from thamdinh.luot import CacBen, KetQuaLuot
from thamdinh.ket_qua_de_xuat import TOI_DA_KY_TU_TRICH_DAN, KetQuaMucDeXuat, ket_qua_de_xuat_muc
from thamdinh.tong_hop import TEN_KET_QUA
from thamdinh.trich_dan import TrichDan


HUONG_DAN_CHUNG = """\
Bạn là chuyên viên pháp chế của Công ty (VTIT), thẩm định Dự thảo Hợp đồng đầu ra dưới đây để bảo vệ quyền lợi của Công ty.

Quy ước:
- "Công ty" là VTIT, "Khách hàng" là bên còn lại; trong Hợp đồng, Công ty có thể là Bên A hoặc Bên B.
- Hợp đồng có thể còn nhãn sửa đổi: [xóa: …] là chữ đã bị xóa, KHÔNG còn hiệu lực; [thêm: …] là chữ mới thêm; \
[sửa: …] là đoạn được tô màu, vẫn có hiệu lực. Đánh giá theo nội dung sau khi chấp nhận các thay đổi.
- Chỉ dựa vào nội dung Hợp đồng và Danh mục tham chiếu được cung cấp.
- Mỗi Tiêu chí được đánh giá là "thoa", "khong_thoa" hoặc "khong_ro". Dùng "khong_ro" khi Hợp đồng không đủ thông tin \
để kết luận, hoặc khi cần thông tin ngoài Hợp đồng (giấy ủy quyền, năng lực thực tế của Công ty…).
- Ý nghĩa của danh_gia: "thoa" nghĩa là ĐIỀU ĐƯỢC MÔ TẢ TRONG TIÊU CHÍ ĐÚNG VỚI HỢP ĐỒNG, "khong_thoa" nghĩa là điều đó KHÔNG đúng \
với Hợp đồng. Áp dụng như nhau cho mọi Tiêu chí, kể cả Tiêu chí [Vi phạm] và [Lưu ý]: chúng mô tả một vấn đề xấu, nên "thoa" nghĩa \
là vấn đề đó CÓ xảy ra. Ví dụ: Tiêu chí [Vi phạm] "Không có điều khoản bất khả kháng", Hợp đồng có Điều 11 về bất khả kháng thì là "khong_thoa".
- Xét chặt: Tiêu chí nêu nhiều yếu tố thì chỉ "thoa" khi Hợp đồng có ĐỦ từng yếu tố; thiếu một yếu tố, hoặc các điều khoản \
mâu thuẫn nhau, là "khong_thoa". Có điều khoản cùng chủ đề chưa đủ để kết luận "thoa": đối chiếu từng yếu tố và ghi trong \
ly_do yếu tố nào có, yếu tố nào thiếu. Ví dụ: Tiêu chí [Đạt] "Có điều khoản bảo hiểm, ghi rõ bên mua bảo hiểm và số tiền \
bảo hiểm", Hợp đồng chỉ ghi Bên B mua bảo hiểm mà không ghi số tiền thì là "khong_thoa".
- Tiêu chí bắt đầu bằng "Nếu …" được coi là "thoa" khi điều kiện không xảy ra. Ví dụ: "Nếu có thuê kho bãi, ghi rõ bên \
chịu chi phí lưu kho", Hợp đồng không có thuê kho bãi thì là "thoa".
- Trích dẫn: chép NGUYÊN VĂN câu trong Hợp đồng, không diễn đạt lại; "so_hieu" là số hiệu Điều khoản ghi sau dấu "###". \
Có thể lược bớt giữa câu bằng "…". Nếu Hợp đồng không có điều khoản liên quan, để "trich_dan" rỗng và ghi "ly_do" là \
"Không tìm thấy điều khoản về …".
- Viết "ly_do" bằng tiếng Việt, ngắn gọn.
"""

HUONG_DAN_CAC_BEN = """\
Đọc phần mở đầu của Hợp đồng dưới đây và xác định các bên.
"Công ty" là Công ty TNHH MTV Đầu tư Công nghệ Viettel (VTIT); "Khách hàng" là bên còn lại.
"""

# Model nhỏ bám theo phần cuối prompt, nên câu hỏi được nhắc lại sau văn bản.
CAU_HOI_CAC_BEN = """\
Câu hỏi: Công ty là Công ty TNHH MTV Đầu tư Công nghệ Viettel (VTIT). Trong phần trên, tên Công ty nằm ở \
dòng "BÊN A:" hay dòng "BÊN B:"?
- cong_ty: "Bên A" nếu tên Công ty nằm ở dòng BÊN A, "Bên B" nếu nằm ở dòng BÊN B, "không rõ" nếu không tìm thấy.
- ten_cong_ty: tên bên đó theo Hợp đồng; ten_khach_hang: tên bên còn lại.
- trich_dan: chép NGUYÊN VĂN dòng chứa tên Công ty; "so_hieu" là số hiệu ghi sau dấu "###".
"""

NHAC_LAI_QUY_UOC = """\
Nhắc lại quy ước:
- Ý nghĩa của danh_gia: "thoa" nghĩa là ĐIỀU ĐƯỢC MÔ TẢ TRONG TIÊU CHÍ ĐÚNG VỚI HỢP ĐỒNG, "khong_thoa" nghĩa là điều đó KHÔNG đúng \
với Hợp đồng. Áp dụng như nhau cho mọi Tiêu chí, kể cả Tiêu chí [Vi phạm] và [Lưu ý]: chúng mô tả một vấn đề xấu, nên "thoa" nghĩa \
là vấn đề đó CÓ xảy ra.
- danh_gia là "thoa", "khong_thoa" hoặc "khong_ro" (khong_ro khi Hợp đồng không đủ thông tin hoặc cần thông tin ngoài \
Hợp đồng). Tiêu chí bắt đầu bằng "Nếu …" là "thoa" khi điều kiện không xảy ra.
- Bỏ qua chữ trong [xóa: …]; chữ trong [thêm: …] và [sửa: …] có hiệu lực.
- trich_dan: chép NGUYÊN VĂN câu trong Hợp đồng; "so_hieu" là số hiệu ghi sau dấu "###". Không có điều khoản liên quan \
thì để trich_dan rỗng và ly_do là "Không tìm thấy điều khoản về …".
"""
# Không thêm vào đây yêu cầu "tối đa 3 trích dẫn, dưới 300 ký tự": thử với Qwen3.5-9B trên Mục 14 TOSS, model bỏ hẳn
# trích dẫn. Giới hạn đó nằm trong SCHEMA_TRICH_DAN, llama-server ép theo.
# Giữ phần đuôi prompt của Mục 1 (từ "MỤC CHECKLIST" trở đi) dưới 516 token: Qwen3.5 chỉ dùng lại được phần đầu từ điểm lưu
# trạng thái, cách cuối prompt 516 token. Đuôi dài hơn thì chế độ toàn văn đọc lại cả Hợp đồng ở mọi Mục (80 phút thay vì 15 phút).

DANH_GIA = ["thoa", "khong_thoa", "khong_ro"]
# Giới hạn số lượng và độ dài trích dẫn: llama-server ép theo schema, chặn model chép lặp không dừng
SCHEMA_TRICH_DAN = {
    "type": "array",
    "maxItems": 3,
    "items": {
        "type": "object",
        "properties": {"so_hieu": {"type": "string"}, "nguyen_van": {"type": "string", "maxLength": TOI_DA_KY_TU_TRICH_DAN}},
        "required": ["so_hieu", "nguyen_van"],
        "additionalProperties": False,
    },
}


def toan_van(van_ban: VanBanHieuLuc) -> str:
    return "\n\n".join(f"### {dk.so_hieu}\n{dk.noi_dung}" for dk in van_ban.dieu_khoan)


def xay_prompt_cac_ben(van_ban: VanBanHieuLuc) -> tuple[str, dict[str, Any]]:
    mo_dau = [dk for dk in van_ban.dieu_khoan if dk.loai == "mo_dau"]
    noi_dung = "\n\n".join(f"### {dk.so_hieu}\n{dk.noi_dung}" for dk in mo_dau) if mo_dau else toan_van(van_ban)
    prompt = f"{HUONG_DAN_CAC_BEN}\n=== HỢP ĐỒNG ===\n{noi_dung}\n=== HẾT ===\n\n{CAU_HOI_CAC_BEN}"
    schema = {
        "type": "object",
        "properties": {
            "cong_ty": {"enum": ["Bên A", "Bên B", "không rõ"]},
            "ten_cong_ty": {"type": "string"},
            "ten_khach_hang": {"type": "string"},
            "trich_dan": SCHEMA_TRICH_DAN,
        },
        "required": ["cong_ty", "ten_cong_ty", "ten_khach_hang", "trich_dan"],
        "additionalProperties": False,
    }
    return prompt, schema


def phan_dau_truy_xuat(van_ban: VanBanHieuLuc, dieu_khoan_chon: str) -> str:
    """Chế độ truy xuất: hướng dẫn chung và các Điều khoản được chọn cho Mục (khác nhau giữa các Mục)."""
    return (
        f"{HUONG_DAN_CHUNG}\n=== CÁC ĐIỀU KHOẢN LIÊN QUAN CỦA HỢP ĐỒNG ({van_ban.ten_file}) ===\n"
        "(Đây là các Điều khoản được chọn là liên quan đến Mục checklist này, không phải toàn văn Hợp đồng; "
        "Điều khoản chỉ có dòng tiêu đề là Điều khoản cha, được đưa vào để biết vị trí.)\n"
        f"{dieu_khoan_chon}\n=== HẾT VĂN BẢN HỢP ĐỒNG ===\n"
    )


def phan_dau_chung(van_ban: VanBanHieuLuc) -> str:
    """Phần đầu giống hệt nhau ở mọi Mục: hướng dẫn chung và toàn văn Hợp đồng."""
    return (
        f"{HUONG_DAN_CHUNG}\n=== VĂN BẢN HỢP ĐỒNG ({van_ban.ten_file}) ===\n"
        f"{toan_van(van_ban)}\n=== HẾT VĂN BẢN HỢP ĐỒNG ===\n"
    )


def xay_prompt_muc(
    muc: MucChecklist,
    checklist: PhienBanChecklist,
    van_ban: VanBanHieuLuc,
    cac_ben: CacBen | None,
    chi_tieu_chi: Collection[str] | None = None,
    dieu_khoan_chon: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Prompt và schema cho một Mục.

    `chi_tieu_chi` giới hạn ở một phần Tiêu chí (khi chia đôi Mục). `dieu_khoan_chon` (chế độ truy xuất) thay toàn văn
    bằng văn bản các Điều khoản được chọn.
    """
    tieu_chi = [tc for ds in muc.tieu_chi.values() for tc in ds if chi_tieu_chi is None or tc.ma in chi_tieu_chi]
    dau = phan_dau_chung(van_ban) if dieu_khoan_chon is None else phan_dau_truy_xuat(van_ban, dieu_khoan_chon)
    phan = [dau, _mo_ta_cac_ben(cac_ben), f"\nMỤC CHECKLIST {muc.so}: {muc.cau_hoi}"]
    if muc.can_cu_phap_ly:
        phan.append("Căn cứ pháp lý: " + "; ".join(muc.can_cu_phap_ly))
    for ma in muc.danh_muc:
        phan.append(f"\nDanh mục tham chiếu '{ma}':\n{_danh_muc(checklist, ma)}")
    phan.append("\nCác Tiêu chí cần đánh giá:")
    for muc_kq, ds in muc.tieu_chi.items():
        for tc in ds:
            if tc in tieu_chi:
                phan.append(f"- {tc.ma} [{TEN_KET_QUA[muc_kq]}]: {tc.mo_ta}{_huong_dan_gia_tri(tc)}")
    phan.append("\n" + NHAC_LAI_QUY_UOC.rstrip())
    phan.append(
        "\nTrả lời bằng JSON: với mỗi mã Tiêu chí ở trên, ghi danh_gia, ly_do, trich_dan "
        "(và gia_tri / gia_tri_dieu_kien khi được yêu cầu; ghi null nếu Hợp đồng không nêu)."
    )

    schema = {
        "type": "object",
        "properties": {tc.ma: _schema_tieu_chi(tc) for tc in tieu_chi},
        "required": [tc.ma for tc in tieu_chi],
        "additionalProperties": False,
    }
    return "\n".join(phan) + "\n", schema


def uoc_tinh_token(van_ban: str) -> int:
    """Ước tính thô, thiên về an toàn: tiếng Việt khoảng 2,5 ký tự mỗi token."""
    return int(len(van_ban) / 2.5) + 1


def _mo_ta_cac_ben(cac_ben: CacBen | None) -> str:
    if cac_ben is None or cac_ben.cong_ty == "không rõ":
        return "\nCác bên: chưa xác định được Công ty là Bên A hay Bên B; hãy tự xác định từ Hợp đồng."
    khach_hang = "Bên A" if cac_ben.cong_ty == "Bên B" else "Bên B"
    return (
        f"\nCác bên: Công ty là {cac_ben.cong_ty} ({cac_ben.ten_cong_ty}); "
        f"Khách hàng là {khach_hang} ({cac_ben.ten_khach_hang})."
    )


def _don_vi(truong: str) -> str:
    if "_phan_tram" in truong:
        return "%"
    if truong.endswith("_vnd"):
        return "đồng"
    if truong.endswith("_ngay"):
        return "ngày"
    if truong.endswith("_thang"):
        return "tháng"
    return ""


def _huong_dan_gia_tri(tc: TieuChi) -> str:
    ghi_chu = []
    if tc.loai == "dinh_luong":
        ghi_chu.append(
            f"ghi gia_tri = {tc.truong} (đơn vị {_don_vi(tc.truong)}, chỉ ghi số) đọc từ Hợp đồng; hệ thống tự so sánh với ngưỡng"
        )
    if tc.dieu_kien:
        truong = tc.dieu_kien.truong
        ghi_chu.append(f"ghi gia_tri_dieu_kien = {truong} (đơn vị {_don_vi(truong)}, chỉ ghi số) đọc từ Hợp đồng")
    return f" ({'; '.join(ghi_chu)})" if ghi_chu else ""


def _schema_tieu_chi(tc: TieuChi) -> dict[str, Any]:
    # Thứ tự thuộc tính là thứ tự model viết. Đặt ly_do trước danh_gia làm model hiểu ngược `thoa` (issue 17, Q127).
    properties: dict[str, Any] = {"danh_gia": {"enum": DANH_GIA}}
    if tc.loai == "dinh_luong":
        properties["gia_tri"] = {"type": ["number", "null"]}
    if tc.dieu_kien:
        properties["gia_tri_dieu_kien"] = {"type": ["number", "null"]}
    properties["ly_do"] = {"type": "string"}
    properties["trich_dan"] = SCHEMA_TRICH_DAN
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def _danh_muc(checklist: PhienBanChecklist, ma: str) -> str:
    d = yaml.safe_load(checklist.danh_muc_tham_chieu[ma].read_text(encoding="utf-8"))
    gon = {k: d[k] for k in ("ten", "nguon", "ghi_chu", "muc") if d.get(k)}
    return yaml.safe_dump(gon, allow_unicode=True, sort_keys=False, width=1000)


# --- Lượt thẩm định -------------------------------------------------------------------------------

DU_PHONG_DAU_RA = 4096  # token dành cho câu trả lời của model


class VanBanQuaDaiError(Exception):
    """Prompt chế độ toàn văn vượt ngữ cảnh của model."""


class NguCanh(Protocol):
    dieu_khoan: tuple[str, ...]
    van_ban: str
    canh_bao: tuple[str, ...]


class NguonNguCanh(Protocol):
    """Chế độ truy xuất (`truy_xuat.TruyXuat`): chọn Điều khoản cho từng Mục."""

    canh_bao: tuple[str, ...]

    def ngu_canh(self, muc: MucChecklist) -> NguCanh: ...


def tham_dinh(
    van_ban: VanBanHieuLuc,
    checklist: PhienBanChecklist,
    llm: LLMClient,
    ngu_canh: int = 65536,
    model: str = "",
    tien_trinh: Callable[[str], None] = lambda _: None,
    sau_moi_buoc: Callable[[KetQuaLuot], None] = lambda _: None,
    luot_truoc: KetQuaLuot | None = None,
    chay_lai: Collection[int] = (),
    truy_xuat: NguonNguCanh | None = None,
) -> KetQuaLuot:
    """Một Lượt thẩm định: xác định các bên, rồi đánh giá từng Mục checklist.

    Chế độ toàn văn khi `truy_xuat` là None; chế độ truy xuất thì mỗi Mục chỉ đọc các Điều khoản `truy_xuat` chọn.

    `sau_moi_buoc` nhận kết quả tạm sau bước xác định các bên và sau mỗi Mục, để người gọi lưu ngay.
    `luot_truoc`: chạy tiếp một Lượt đã lưu; chỉ gọi model cho Mục chưa chạy, chưa đánh giá được, hoặc có trong
    `chay_lai`.
    """
    if luot_truoc and (luot_truoc.hash_pdf, luot_truoc.checklist) != (van_ban.hash_pdf, f"{checklist.ma} {checklist.phien_ban}"):
        raise ValueError(
            f"Lượt đã lưu thuộc Hợp đồng khác hoặc checklist khác ({luot_truoc.ten_file}, {luot_truoc.checklist})"
        )
    che_do = "toan_van" if truy_xuat is None else "truy_xuat"
    if luot_truoc and luot_truoc.che_do != che_do:
        raise ValueError(f"Lượt đã lưu chạy ở chế độ {luot_truoc.che_do}, không chạy tiếp ở chế độ {che_do} được")
    dai_nhat = max(uoc_tinh_token(xay_prompt_muc(m, checklist, van_ban, None)[0]) for m in checklist.muc)
    if truy_xuat is None and dai_nhat + DU_PHONG_DAU_RA > ngu_canh:
        raise VanBanQuaDaiError(
            f"Prompt chế độ toàn văn ước tính {dai_nhat} token, cộng {DU_PHONG_DAU_RA} token trả lời là vượt ngữ cảnh "
            f"{ngu_canh} token của model. Tăng THAMDINH_NGU_CANH (và tham số -c của llama-server) "
            "hoặc dùng chế độ truy xuất."
        )
    da_co = {m.so: m for m in luot_truoc.muc if m.ket_qua is not None} if luot_truoc else {}
    # Chạy lại Mục đã có Kết quả đề xuất thì tạo Lượt mới: Kết quả đề xuất không bao giờ bị ghi đè (issue 10)
    tao_moi = luot_truoc is not None and any(so in da_co for so in chay_lai)
    if luot_truoc and not tao_moi and luot_truoc.ma:
        bat_dau, ma, luot_goc = luot_truoc.bat_dau, luot_truoc.ma, luot_truoc.luot_goc
    else:
        bay_gio = datetime.now()
        bat_dau = bay_gio.isoformat(timespec="seconds")
        ma = f"{van_ban.hash_pdf[:12]}-{bay_gio:%Y%m%dT%H%M%S%f}"
        luot_goc = luot_truoc.ma if tao_moi else None
    hash_vb = hash_noi_dung(van_ban)

    if luot_truoc and luot_truoc.cac_ben:
        cac_ben, loi_cac_ben = luot_truoc.cac_ben, None
    else:
        tien_trinh("Xác định các bên")
        cac_ben, loi_cac_ben = None, None
        try:
            d = _goi(llm, *xay_prompt_cac_ben(van_ban))
            cac_ben = CacBen(
                d["cong_ty"], d["ten_cong_ty"], d["ten_khach_hang"],
                tuple(TrichDan(t["so_hieu"], t["nguyen_van"]) for t in d["trich_dan"]),
            )
        except LLMResponseError as e:
            loi_cac_ben = f"chưa xác định được các bên: {e}"

    def luot(muc: list[KetQuaMucDeXuat]) -> KetQuaLuot:
        return KetQuaLuot(
            hash_pdf=van_ban.hash_pdf,
            ten_file=van_ban.ten_file,
            checklist=f"{checklist.ma} {checklist.phien_ban}",
            model=model,
            che_do=che_do,
            bat_dau=bat_dau,
            ma=ma,
            luot_goc=luot_goc,
            hash_van_ban=hash_vb,
            ket_thuc=datetime.now().isoformat(timespec="seconds"),
            cac_ben=cac_ben,
            loi_cac_ben=loi_cac_ben,
            muc=tuple(muc),
            canh_bao=tuple(truy_xuat.canh_bao) if truy_xuat else (),
        )

    ket_qua: list[KetQuaMucDeXuat] = []
    sau_moi_buoc(luot(ket_qua))
    for m in checklist.muc:
        if m.so in da_co and m.so not in chay_lai:
            ket_qua.append(da_co[m.so])
            sau_moi_buoc(luot(ket_qua))  # Lượt mới (chay_lai) phải có cả các Mục chép từ Lượt gốc
            continue
        tien_trinh(f"Mục {m.so}/{len(checklist.muc)}")
        if truy_xuat is None:
            kq = _danh_gia_muc(m, checklist, van_ban, cac_ben, llm)
            ket_qua.append(replace(kq, dieu_khoan_dua_vao=tuple(d.so_hieu for d in van_ban.dieu_khoan)))
        else:
            nc = truy_xuat.ngu_canh(m)
            kq = _danh_gia_muc(m, checklist, van_ban, cac_ben, llm, nc.van_ban)
            ket_qua.append(replace(kq, dieu_khoan_dua_vao=tuple(nc.dieu_khoan), canh_bao=tuple(nc.canh_bao)))
        sau_moi_buoc(luot(ket_qua))
    return luot(ket_qua)


def _goi(llm: LLMClient, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
    """Gọi model; JSON sai thì gọi lại một lần, kèm lỗi ở cuối prompt (giữ nguyên phần đầu để dùng lại cache).

    Câu trả lời bị cắt thì không gọi lại: người gọi phải đổi cách hỏi (chia nhỏ Tiêu chí).
    """
    try:
        return llm.complete_json(prompt, schema)
    except LLMBiCatError:
        raise
    except LLMResponseError as e:
        return llm.complete_json(
            f"{prompt}\nLần trả lời trước bị lỗi: {e}\nHãy trả lời lại, đúng JSON theo yêu cầu.\n", schema
        )


def _danh_gia_muc(
    muc: MucChecklist,
    checklist: PhienBanChecklist,
    van_ban: VanBanHieuLuc,
    cac_ben: CacBen | None,
    llm: LLMClient,
    dieu_khoan_chon: str | None = None,
) -> KetQuaMucDeXuat:
    try:
        tra_loi = _goi(llm, *xay_prompt_muc(muc, checklist, van_ban, cac_ben, dieu_khoan_chon=dieu_khoan_chon))
    except LLMBiCatError:
        # Gọi lại y nguyên thì model (nhiệt độ 0) lặp y như cũ: chia đôi Tiêu chí để mỗi câu trả lời ngắn lại
        ma = [tc.ma for ds in muc.tieu_chi.values() for tc in ds]
        nua = (len(ma) + 1) // 2
        try:
            tra_loi = {}
            for phan in (ma[:nua], ma[nua:]):
                tra_loi |= _goi(llm, *xay_prompt_muc(muc, checklist, van_ban, cac_ben, phan, dieu_khoan_chon))
        except LLMResponseError as e:
            return KetQuaMucDeXuat(muc.so, muc.cau_hoi, None, (), f"chưa đánh giá được (đã chia đôi Tiêu chí): {e}")
    except LLMResponseError as e:
        return KetQuaMucDeXuat(muc.so, muc.cau_hoi, None, (), f"chưa đánh giá được: {e}")

    return ket_qua_de_xuat_muc(muc, tra_loi, van_ban)
