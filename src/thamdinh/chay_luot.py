"""Chạy một Lượt thẩm định từ file PDF: dùng cho `scripts/chay_tham_dinh.py` (và tiến trình nền của giao diện)."""

import time
from collections.abc import Callable, Collection
from pathlib import Path

from thamdinh.checklist import load_checklist
from thamdinh.kho_luot import KhoLuot
from thamdinh.llm import LLMClient, LocalClient
from thamdinh.settings import Settings
from thamdinh.so_hoa import so_hoa
from thamdinh.so_hoa.ocr import BoOCRMacDinh
from thamdinh.tham_dinh import KetQuaLuot, tham_dinh
from thamdinh.truy_xuat import BoNhung, LocalEmbeddingClient, chuan_bi_truy_xuat


def chay_luot(
    pdf: str | Path,
    checklist: str | Path,
    settings: Settings,
    che_do: str | None = None,
    tiep_tuc: str | None = None,
    chi_muc: Collection[int] = (),
    llm: LLMClient | None = None,
    nhung: BoNhung | None = None,
    in_ra: Callable[[str], None] = print,
) -> KetQuaLuot:
    """Chạy (hoặc chạy tiếp Lượt `tiep_tuc`) và lưu vào kho sau mỗi Mục.

    - `tiep_tuc`: chỉ chạy Mục chưa chạy hoặc "chưa đánh giá được", vẫn là Lượt đó.
    - `chi_muc`: cùng `tiep_tuc`, chạy lại các Mục này dù đã có kết quả; tạo Lượt mới, Lượt cũ giữ nguyên.
    - In "Mã Lượt: …" ngay khi Lượt được lưu lần đầu, để giao diện theo dõi tiến độ trong kho.
    """
    if chi_muc and not tiep_tuc:
        raise ValueError("chi_muc cần đi cùng tiep_tuc")
    kho = KhoLuot(settings.data_dir)
    luot_truoc = kho.nap(tiep_tuc) if tiep_tuc else None
    che_do = che_do or (luot_truoc.che_do if luot_truoc else "toan_van")
    bat_dau = time.monotonic()

    def tien_trinh(viec: str) -> None:
        in_ra(f"[{(time.monotonic() - bat_dau) / 60:5.1f} phút] {viec}")

    van_ban = so_hoa(
        pdf, thu_muc_luu=settings.data_dir, bo_ocr=BoOCRMacDinh(settings.thu_muc_model_ocr, settings.ocr_model),
        tien_trinh=tien_trinh,
    )
    llm = llm or LocalClient(settings.local_url, settings.model, suy_luan=settings.suy_luan)
    truy_xuat = None
    if che_do == "truy_xuat":
        truy_xuat = chuan_bi_truy_xuat(
            van_ban, load_checklist(checklist), llm,
            nhung or LocalEmbeddingClient(settings.embedding_url, settings.embedding_model),
            settings.ngan_sach_truy_xuat, model=settings.model, thu_muc_luu=settings.data_dir, tien_trinh=tien_trinh,
            dem_token=getattr(llm, "dem_token", None),
        )
        for c in truy_xuat.canh_bao:
            in_ra(f"Cảnh báo: {c}")

    da_in: set[str] = set()

    def luu(kq: KetQuaLuot) -> None:
        kho.luu(kq)
        if kq.ma not in da_in:
            da_in.add(kq.ma)
            in_ra(f"Mã Lượt: {kq.ma}")

    kq = tham_dinh(
        van_ban, load_checklist(checklist), llm, ngu_canh=settings.ngu_canh, model=settings.model,
        tien_trinh=tien_trinh, sau_moi_buoc=luu, luot_truoc=luot_truoc, chay_lai=chi_muc, truy_xuat=truy_xuat,
    )
    luu(kq)
    return kq
