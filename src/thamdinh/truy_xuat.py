"""Chế độ truy xuất theo cấu trúc (ADR 0002): gắn Chủ đề cho Điều khoản, rồi chọn Điều khoản cho từng Mục checklist.

Gắn Chủ đề làm một lần cho mỗi Văn bản hiệu lực, lưu lại theo nội dung Văn bản hiệu lực + Phiên bản checklist + model.
"""

import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Protocol

import httpx

from thamdinh.checklist import MucChecklist, PhienBanChecklist
from thamdinh.llm import LLMClient, LLMKetNoiError, LLMResponseError, may_chu_san_sang
from thamdinh.so_hoa import VanBanHieuLuc
from thamdinh.so_hoa.cau_truc import DieuKhoan, ban_sach
from thamdinh.tham_dinh import _goi, uoc_tinh_token
from thamdinh.trich_dan import KHONG_XAC_MINH_DUOC, KHOP, TrichDan, kiem_tra_trich_dan

TOI_DA_TOKEN_NHOM = 4000  # văn bản mỗi lần gọi gắn Chủ đề
TOI_DA_CHU_DE = 5  # mỗi Điều khoản; chặn model liệt kê lặp

HUONG_DAN_GAN_CHU_DE = """\
Bạn là chuyên viên pháp chế. Dưới đây là một phần của Dự thảo Hợp đồng, chia theo Điều khoản; mỗi Điều khoản bắt đầu bằng \
dòng "### [mã] số hiệu". Hãy gắn cho mỗi Điều khoản các Chủ đề mà nội dung CỦA CHÍNH Điều khoản đó đề cập, chọn trong danh sách:
{danh_sach}

Quy ước:
- Một Điều khoản có thể có nhiều Chủ đề, hoặc không có Chủ đề nào (ghi []).
- Chỉ gắn khi Điều khoản thực sự quy định về Chủ đề đó, không gắn vì nhắc qua.
- Bỏ qua chữ trong [xóa: …]; chữ trong [thêm: …] và [sửa: …] có hiệu lực.
"""

CAU_HOI_GAN_CHU_DE = """\
Với mỗi mã Điều khoản ở trên ([dk…]), trả lời bằng JSON: mã Điều khoản → danh sách mã Chủ đề trong danh sách đã cho \
(tối đa {toi_da}; [] nếu không thuộc Chủ đề nào)."""


@dataclass(frozen=True)
class ChuDeVanBan:
    khoa: str  # theo nội dung Văn bản hiệu lực + Phiên bản checklist + model
    chu_de: dict[int, tuple[str, ...]]  # mã Điều khoản (DieuKhoan.ma) → mã Chủ đề
    canh_bao: tuple[str, ...]


def gan_chu_de(
    van_ban: VanBanHieuLuc,
    checklist: PhienBanChecklist,
    llm: LLMClient,
    model: str = "",
    thu_muc_luu: str | Path | None = None,
    toi_da_token_nhom: int = TOI_DA_TOKEN_NHOM,
    tien_trinh: Callable[[str], None] = lambda _: None,
) -> ChuDeVanBan:
    """Gắn Chủ đề cho mọi Điều khoản; nhóm nào model trả lời sai hai lần thì các Điều khoản đó không có Chủ đề."""
    khoa = _khoa(van_ban, checklist, model)
    file = Path(thu_muc_luu) / "chu-de" / f"{van_ban.hash_pdf[:12]}-{khoa[:16]}.json" if thu_muc_luu else None
    if file and file.exists():
        d = json.loads(file.read_text(encoding="utf-8"))
        return ChuDeVanBan(khoa, {int(ma): tuple(cd) for ma, cd in d["chu_de"].items()}, ())

    chu_de: dict[int, tuple[str, ...]] = {}
    canh_bao = []
    nhom = _chia_nhom(van_ban.dieu_khoan, toi_da_token_nhom)
    for i, ds in enumerate(nhom, 1):
        tien_trinh(f"Gắn Chủ đề: nhóm {i}/{len(nhom)}")
        try:
            tra_loi = _goi(llm, *_xay_prompt(ds, checklist))
        except LLMResponseError as e:
            canh_bao.append(f"Chưa gắn được Chủ đề cho {', '.join(d.so_hieu for d in ds)}: {e}")
            tra_loi = {}
        for d in ds:
            chu_de[d.ma] = tuple(dict.fromkeys(tra_loi.get(f"dk{d.ma}", [])))

    if file and not canh_bao:
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps({"khoa": khoa, "model": model, "chu_de": chu_de}, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    return ChuDeVanBan(khoa, chu_de, tuple(canh_bao))


def _khoa(van_ban: VanBanHieuLuc, checklist: PhienBanChecklist, model: str) -> str:
    noi_dung = {
        "dieu_khoan": [[d.so_hieu, d.noi_dung] for d in van_ban.dieu_khoan],
        "checklist": f"{checklist.ma} {checklist.phien_ban}",
        "chu_de": checklist.chu_de,
        "model": model,
    }
    return hashlib.sha256(json.dumps(noi_dung, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def _chia_nhom(dieu_khoan: list[DieuKhoan], toi_da: int) -> list[list[DieuKhoan]]:
    """Các Điều khoản liền nhau, mỗi nhóm không quá `toi_da` token; Điều khoản lớn hơn thì đứng một mình."""
    nhom: list[list[DieuKhoan]] = []
    dang, so_token = [], 0
    for d in dieu_khoan:
        n = uoc_tinh_token(d.noi_dung)
        if dang and so_token + n > toi_da:
            nhom.append(dang)
            dang, so_token = [], 0
        dang.append(d)
        so_token += n
    if dang:
        nhom.append(dang)
    return nhom


def _xay_prompt(ds: list[DieuKhoan], checklist: PhienBanChecklist) -> tuple[str, dict[str, Any]]:
    danh_sach = "\n".join(f"- {ma}: {ten}" for ma, ten in checklist.chu_de.items())
    van_ban = "\n\n".join(f"### [dk{d.ma}] {d.so_hieu}\n{d.noi_dung}" for d in ds)
    prompt = (
        f"{HUONG_DAN_GAN_CHU_DE.format(danh_sach=danh_sach)}\n=== ĐIỀU KHOẢN ===\n{van_ban}\n=== HẾT ===\n\n"
        f"{CAU_HOI_GAN_CHU_DE.format(toi_da=TOI_DA_CHU_DE)}\n"
    )
    item = {"type": "array", "items": {"enum": list(checklist.chu_de)}, "maxItems": TOI_DA_CHU_DE}
    schema = {
        "type": "object",
        "properties": {f"dk{d.ma}": item for d in ds},
        "required": [f"dk{d.ma}" for d in ds],
        "additionalProperties": False,
    }
    return prompt, schema


# --- Chọn Điều khoản cho một Mục checklist ---------------------------------------------------------

TOP_K_LUOI_AN_TOAN = 5  # mỗi bộ tìm kiếm


class BoTimKiem(Protocol):
    def tim(self, cau_truy_van: str) -> list[int]:
        """Mã mọi Điều khoản (DieuKhoan.ma), liên quan nhất trước."""
        ...


@dataclass(frozen=True)
class NguCanhMuc:
    dieu_khoan: tuple[str, ...]  # số hiệu các Điều khoản đưa nguyên văn, theo thứ tự trong Hợp đồng
    van_ban: str  # văn bản đưa vào prompt (Điều khoản cha chỉ có dòng tiêu đề)
    so_token: int
    bo_qua: tuple[str, ...]  # gốc các nhóm Điều khoản bị bỏ vì vượt ngân sách, theo thứ tự ưu tiên
    canh_bao: tuple[str, ...]


def cau_truy_van(muc: MucChecklist) -> str:
    return "\n".join([muc.cau_hoi, *(tc.mo_ta for ds in muc.tieu_chi.values() for tc in ds)])


def chon_dieu_khoan(
    muc: MucChecklist,
    van_ban: VanBanHieuLuc,
    chu_de: ChuDeVanBan,
    tim_kiem: list[BoTimKiem],
    ngan_sach: int,
    dem: Callable[[str], int] = uoc_tinh_token,
) -> NguCanhMuc:
    """Điều khoản mang Chủ đề của Mục (kèm con cháu), cộng top-k mỗi bộ tìm kiếm, trong ngân sách `ngan_sach` token.

    Ưu tiên: theo Chủ đề trước lưới an toàn; trong nhóm Chủ đề, Điều khoản lớn hơn nửa ngân sách xếp sau cùng.
    Một cây không vừa thì thử từng Điều khoản con; Điều khoản không con không vừa thì bỏ nguyên (không cắt giữa chừng).
    `dem` đếm token (chính xác: `/tokenize` của llama-server; mặc định ước tính).
    """
    da_dem: dict[str, int] = {}

    def so_token(van_ban_chon: str) -> int:
        if van_ban_chon not in da_dem:
            da_dem[van_ban_chon] = dem(van_ban_chon)
        return da_dem[van_ban_chon]

    con = _con_chau(van_ban.dieu_khoan)
    con_truc_tiep: dict[int, list[int]] = {d.ma: [] for d in van_ban.dieu_khoan}
    for d in van_ban.dieu_khoan:
        if d.cha is not None:
            con_truc_tiep[d.cha].append(d.ma)
    so_hieu = {d.ma: d.so_hieu for d in van_ban.dieu_khoan}
    ket_qua_tim = [bo.tim(cau_truy_van(muc)) for bo in tim_kiem]
    hang: dict[int, int] = {}
    for ds in ket_qua_tim:
        for i, ma in enumerate(ds):
            hang[ma] = min(hang.get(ma, i), i)

    goc_chu_de = [d.ma for d in van_ban.dieu_khoan if set(chu_de.chu_de.get(d.ma, ())) & set(muc.chu_de)]
    da_phu = set().union(*(con[ma] for ma in goc_chu_de)) if goc_chu_de else set()
    goc_luoi: list[int] = []
    for ds in ket_qua_tim:
        moi = [ma for ma in ds if ma not in da_phu][:TOP_K_LUOI_AN_TOAN]
        goc_luoi += [ma for ma in moi if ma not in goc_luoi]

    def hang_cua(g: int) -> int:
        return min((hang.get(m, len(hang)) for m in con[g]), default=0)

    def lon(g: int) -> bool:
        return so_token(_trinh_bay(van_ban.dieu_khoan, con[g])) > ngan_sach / 2

    def thu_tu(goc: list[int], lon_xep_sau: bool) -> list[int]:
        goc = [g for g in goc if not any(g in con[k] and g != k for k in goc)]  # bỏ gốc nằm trong gốc khác
        return sorted(goc, key=lambda g: (lon_xep_sau and lon(g), hang_cua(g)))

    chon: set[int] = set()
    da_bo: set[int] = set()
    bo_qua = []
    goc_theo_thu_tu = thu_tu(goc_chu_de, True) + [g for g in thu_tu(goc_luoi, False) if not con[g] <= da_phu]
    hang_doi = [(g, con[g]) for g in goc_theo_thu_tu]  # (gốc, nhóm Điều khoản)
    while hang_doi:
        goc, nhom = hang_doi.pop(0)
        moi = nhom - chon - da_bo
        if not moi:
            continue
        if so_token(_trinh_bay(van_ban.dieu_khoan, chon | moi)) <= ngan_sach:
            chon |= moi
        elif len(nhom) > 1:
            # Cả cây không vừa: thử phần của riêng Điều khoản gốc, rồi từng Điều khoản con (liên quan nhất trước)
            hang_doi[:0] = [(goc, {goc})] + [(c, con[c]) for c in sorted(con_truc_tiep[goc], key=hang_cua)]
        else:
            bo_qua.append(so_hieu[goc])
            da_bo |= moi

    canh_bao = []
    if not goc_chu_de:
        canh_bao.append(
            f"Không Điều khoản nào mang Chủ đề của Mục {muc.so} ({', '.join(muc.chu_de)}); chỉ dựa vào lưới an toàn."
        )
    if bo_qua:
        canh_bao.append(f"Vượt ngân sách {ngan_sach} token: đã bỏ {', '.join(bo_qua)}.")
    van_ban_chon = _trinh_bay(van_ban.dieu_khoan, chon)
    return NguCanhMuc(
        dieu_khoan=tuple(d.so_hieu for d in van_ban.dieu_khoan if d.ma in chon),
        van_ban=van_ban_chon,
        so_token=so_token(van_ban_chon),
        bo_qua=tuple(bo_qua),
        canh_bao=tuple(canh_bao),
    )


def _con_chau(dieu_khoan: list[DieuKhoan]) -> dict[int, set[int]]:
    """Mã Điều khoản → chính nó và mọi Điều khoản con cháu."""
    con = {d.ma: {d.ma} for d in dieu_khoan}
    for d in reversed(dieu_khoan):  # con luôn đứng sau cha
        if d.cha is not None:
            con[d.cha] |= con[d.ma]
    return con


def _trinh_bay(dieu_khoan: list[DieuKhoan], chon: set[int]) -> str:
    cha = {d.ma: d.cha for d in dieu_khoan}
    to_tien = set()
    for ma in chon:
        while cha[ma] is not None:
            ma = cha[ma]
            to_tien.add(ma)
    phan = []
    for d in dieu_khoan:
        if d.ma in chon:
            phan.append(f"### {d.so_hieu}\n{d.noi_dung}")
        elif d.ma in to_tien:
            phan.append(f"### {d.so_hieu}\n{d.noi_dung.splitlines()[0] if d.noi_dung else ''}")
    return "\n\n".join(phan)


# --- Lưới an toàn: BM25 và embedding --------------------------------------------------------------

_TU = re.compile(r"\w+")


def tach_tu(van_ban: str) -> list[str]:
    """Âm tiết (chữ thường, giữ dấu) cộng cặp âm tiết liền nhau, để "hợp đồng" khác "hợp" + "đồng" rời nhau."""
    am_tiet = _TU.findall(unicodedata.normalize("NFC", van_ban).lower())
    return am_tiet + [f"{a} {b}" for a, b in zip(am_tiet, am_tiet[1:])]


def _ban_sach(dk: DieuKhoan) -> str:
    return "\n".join(ban_sach(dong) for dong in dk.noi_dung.splitlines())


class BoTimBM25:
    """BM25 trên bản đã chấp nhận redline của từng Điều khoản."""

    K1, B = 1.5, 0.75

    def __init__(self, van_ban: VanBanHieuLuc):
        self._ma = [d.ma for d in van_ban.dieu_khoan]
        self._tan_suat = [Counter(tach_tu(_ban_sach(d))) for d in van_ban.dieu_khoan]
        self._do_dai = [sum(ts.values()) for ts in self._tan_suat]
        self._tb = sum(self._do_dai) / max(len(self._do_dai), 1) or 1
        so_van_ban = Counter(t for ts in self._tan_suat for t in ts)
        n = len(self._ma)
        self._idf = {t: math.log((n - df + 0.5) / (df + 0.5) + 1) for t, df in so_van_ban.items()}

    def tim(self, cau_truy_van: str) -> list[int]:
        tu = set(tach_tu(cau_truy_van))
        diem = []
        for ts, dai in zip(self._tan_suat, self._do_dai):
            chuan = self.K1 * (1 - self.B + self.B * dai / self._tb)
            diem.append(sum(self._idf[t] * ts[t] * (self.K1 + 1) / (ts[t] + chuan) for t in tu if t in ts))
        thu_tu = sorted(range(len(self._ma)), key=lambda i: -diem[i])  # bằng điểm thì giữ thứ tự Hợp đồng
        return [self._ma[i] for i in thu_tu]


class BoNhung(Protocol):
    def nhung(self, van_ban: list[str]) -> list[list[float]]: ...


class LocalEmbeddingClient:
    """Gọi bge-m3 chạy bằng `llama-server --embedding` qua API chuẩn OpenAI (`/v1/embeddings`)."""

    def __init__(self, base_url: str, model: str, http: httpx.Client | None = None, timeout: float = 600):
        self._url = base_url.rstrip("/")
        self._model = model
        self._http = http or httpx.Client(timeout=httpx.Timeout(timeout, connect=10.0))

    def san_sang(self) -> bool:
        return may_chu_san_sang(self._url, self._http)

    def nhung(self, van_ban: list[str]) -> list[list[float]]:
        try:
            response = self._http.post(f"{self._url}/embeddings", json={"model": self._model, "input": van_ban})
        except httpx.ConnectError as e:
            raise LLMKetNoiError(f"Chưa chạy máy chủ embedding tại {self._url} (xem docs/chay-model-local.md).") from e
        response.raise_for_status()
        return [d["embedding"] for d in sorted(response.json()["data"], key=lambda d: d["index"])]


class BoTimNhung:
    """Độ tương đồng cosine giữa câu truy vấn và từng Điều khoản; Điều khoản dài được chia đoạn, lấy đoạn giống nhất."""

    def __init__(self, van_ban: VanBanHieuLuc, nhung: BoNhung, toi_da_token_doan: int = 2000, lo: int = 32):
        self._nhung = nhung
        self._ma = [d.ma for d in van_ban.dieu_khoan]
        doan, cua = [], []
        for i, d in enumerate(van_ban.dieu_khoan):
            for p in _chia_doan(f"{d.so_hieu}\n{_ban_sach(d)}", int(toi_da_token_doan * 2.5)):
                doan.append(p)
                cua.append(i)
        vec = [v for k in range(0, len(doan), lo) for v in nhung.nhung(doan[k : k + lo])]
        self._doan = list(zip(cua, (_chuan_hoa(v) for v in vec)))

    def tim(self, cau_truy_van: str) -> list[int]:
        q = _chuan_hoa(self._nhung.nhung([cau_truy_van])[0])
        diem = [-1.0] * len(self._ma)
        for i, v in self._doan:
            diem[i] = max(diem[i], sum(a * b for a, b in zip(q, v)))
        return [self._ma[i] for i in sorted(range(len(self._ma)), key=lambda i: -diem[i])]


def _chia_doan(van_ban: str, toi_da_ky_tu: int) -> list[str]:
    doan, dang = [], ""
    for tu in van_ban.split(" "):
        if dang and len(dang) + 1 + len(tu) > toi_da_ky_tu:
            doan.append(dang)
            dang = tu
        else:
            dang = f"{dang} {tu}" if dang else tu
    return doan + [dang] if dang else doan or [""]


def _chuan_hoa(v: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def tao_bo_tim_kiem(van_ban: VanBanHieuLuc, nhung: BoNhung | None) -> tuple[list[BoTimKiem], list[str]]:
    """BM25, cộng embedding nếu máy chủ embedding đang chạy (không thì chỉ BM25, kèm cảnh báo)."""
    bo: list[BoTimKiem] = [BoTimBM25(van_ban)]
    if nhung is None:
        return bo, ["Chưa cấu hình embedding; lưới an toàn chỉ dùng BM25."]
    try:
        bo.append(BoTimNhung(van_ban, nhung))
    except LLMKetNoiError as e:
        return bo, [f"{e} Lưới an toàn chỉ dùng BM25."]
    return bo, []


# --- Ghép lại cho một Lượt thẩm định ---------------------------------------------------------------


@dataclass(frozen=True)
class TruyXuat:
    """Nguồn ngữ cảnh cho `tham_dinh(..., truy_xuat=…)`: chọn Điều khoản cho từng Mục."""

    van_ban: VanBanHieuLuc
    chu_de: ChuDeVanBan
    tim_kiem: list[BoTimKiem]
    ngan_sach: int
    canh_bao: tuple[str, ...]
    dem_token: Callable[[str], int] = uoc_tinh_token

    def ngu_canh(self, muc: MucChecklist) -> NguCanhMuc:
        return chon_dieu_khoan(muc, self.van_ban, self.chu_de, self.tim_kiem, self.ngan_sach, self.dem_token)


def chuan_bi_truy_xuat(
    van_ban: VanBanHieuLuc,
    checklist: PhienBanChecklist,
    llm: LLMClient,
    nhung: BoNhung | None,
    ngan_sach: int,
    model: str = "",
    thu_muc_luu: str | Path | None = None,
    tien_trinh: Callable[[str], None] = lambda _: None,
    dem_token: Callable[[str], int] | None = None,
) -> TruyXuat:
    """Gắn Chủ đề (dùng lại kết quả đã lưu nếu có) và dựng các bộ tìm kiếm của lưới an toàn.

    `dem_token` (thường là `LocalClient.dem_token`): đếm token chính xác cho ngân sách; không có hoặc không gọi được
    thì ước tính (đếm dư) và ghi cảnh báo.
    """
    chu_de = gan_chu_de(van_ban, checklist, llm, model=model, thu_muc_luu=thu_muc_luu, tien_trinh=tien_trinh)
    tien_trinh("Dựng chỉ mục tìm kiếm")
    tim_kiem, canh_bao = tao_bo_tim_kiem(van_ban, nhung)
    dem = uoc_tinh_token
    try:
        if dem_token is None:
            raise LLMKetNoiError("Chưa có bộ đếm token của model.")
        dem_token("Điều 1")
        dem = lru_cache(maxsize=4096)(dem_token)  # các Mục dùng chung nhiều đoạn văn bản
    except LLMKetNoiError as e:
        canh_bao.append(f"{e} Ngân sách token theo ước tính (đếm dư khoảng 20%).")
    return TruyXuat(van_ban, chu_de, tim_kiem, ngan_sach, (*chu_de.canh_bao, *canh_bao), dem)


# --- Độ phủ ngữ cảnh: Trích dẫn của Bộ chuẩn có nằm trong ngữ cảnh truy xuất không ------------------


@dataclass(frozen=True)
class DoPhu:
    ma: str  # mã Tiêu chí
    so_muc: int
    nguyen_van: str  # Trích dẫn trong Bộ chuẩn
    trang_thai: str  # co | thieu | khong_co_trong_van_ban (Bộ chuẩn chép sai hoặc số hóa lỗi, không tính vào độ phủ)


def do_phu_ngu_canh(
    trich_dan_chuan: dict[str, tuple[str, ...]],
    checklist: PhienBanChecklist,
    van_ban: VanBanHieuLuc,
    ngu_canh: Callable[[MucChecklist], NguCanhMuc],
) -> list[DoPhu]:
    """Với mỗi Trích dẫn trong Bộ chuẩn: model có được đọc câu đó ở Mục tương ứng không (so khớp như kiểm tra Trích dẫn)."""
    kq = []
    for muc in checklist.muc:
        ma_muc = [tc.ma for ds in muc.tieu_chi.values() for tc in ds if tc.ma in trich_dan_chuan]
        if not ma_muc:
            continue
        nc = ngu_canh(muc)
        chi_ngu_canh = VanBanHieuLuc("", "", [], [DieuKhoan(0, "ngữ cảnh", "khoan", None, None, 1, 1, nc.van_ban)], [])
        for ma in ma_muc:
            for cau in trich_dan_chuan[ma]:
                if kiem_tra_trich_dan(TrichDan("", cau), van_ban).trang_thai == KHONG_XAC_MINH_DUOC:
                    trang_thai = "khong_co_trong_van_ban"
                elif kiem_tra_trich_dan(TrichDan("ngữ cảnh", cau), chi_ngu_canh).trang_thai == KHOP:
                    trang_thai = "co"
                else:
                    trang_thai = "thieu"
                kq.append(DoPhu(ma, muc.so, cau, trang_thai))
    return kq
