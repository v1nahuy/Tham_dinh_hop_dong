"""Chạy Lượt thẩm định ở tiến trình nền (`scripts/chay_tham_dinh.py`): đóng giao diện thì Lượt vẫn chạy tiếp.

Mỗi lúc chỉ một Lượt, vì llama-server chạy `-np 1`. Trạng thái nằm trong `<data>/dang-chay.json`, nhật ký trong
`<data>/nhat-ky/`; script in dòng "Mã Lượt: …" ngay khi Lượt được lưu lần đầu để giao diện theo dõi tiến độ trong kho.
"""

import ctypes
import json
import os
import re
import signal
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

GOC = Path(__file__).resolve().parents[2]
SCRIPT = GOC / "scripts" / "chay_tham_dinh.py"
FILE_TRANG_THAI = "dang-chay.json"
THU_MUC_NHAT_KY = "nhat-ky"
SO_DONG_CUOI = 8
MA_LUOT = re.compile(r"^Mã Lượt: (\S+)", re.MULTILINE)


class DangChayError(RuntimeError):
    """Đã có một Lượt đang chạy."""


@dataclass(frozen=True)
class TrangThaiChay:
    dang_chay: bool
    pid: int
    doi_so: tuple[str, ...]
    bat_dau: str
    nhat_ky: Path
    ma_luot: str | None  # None khi script chưa lưu Lượt lần đầu
    dong_cuoi: tuple[str, ...]


def _con_song(pid: int) -> bool:
    if sys.platform != "win32":
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True
    # Windows: os.kill(pid, 0) sẽ diệt tiến trình, nên hỏi mã thoát qua WinAPI (259 = STILL_ACTIVE).
    kernel32 = ctypes.windll.kernel32
    xu_ly = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not xu_ly:
        return False
    try:
        ma = ctypes.c_ulong()
        return bool(kernel32.GetExitCodeProcess(xu_ly, ctypes.byref(ma))) and ma.value == 259
    finally:
        kernel32.CloseHandle(xu_ly)


def _ket_thuc(pid: int) -> None:
    os.kill(pid, signal.SIGTERM)  # Windows: TerminateProcess


def khoi_chay(
    doi_so: list[str],
    thu_muc: str | Path,
    popen: Callable = subprocess.Popen,
    con_song: Callable[[int], bool] = _con_song,
) -> TrangThaiChay:
    """Khởi chạy `chay_tham_dinh.py <doi_so>` ở tiến trình nền; đã có Lượt đang chạy thì báo DangChayError."""
    thu_muc = Path(thu_muc)
    if (tt := trang_thai(thu_muc, con_song)) and tt.dang_chay:
        raise DangChayError(f"Đang chạy một Lượt (bắt đầu {tt.bat_dau}); chờ xong hoặc dừng trước.")
    bat_dau = datetime.now()
    nhat_ky = thu_muc / THU_MUC_NHAT_KY / f"{bat_dau:%Y%m%dT%H%M%S}.log"
    nhat_ky.parent.mkdir(parents=True, exist_ok=True)
    co = 0
    if sys.platform == "win32":  # nhóm tiến trình riêng: Ctrl+C ở cửa sổ Streamlit không dừng Lượt
        co = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
    with open(nhat_ky, "wb") as ra:
        p = popen(
            [sys.executable, "-u", str(SCRIPT), *doi_so], stdout=ra, stderr=subprocess.STDOUT, cwd=GOC,
            env={**os.environ, "PYTHONIOENCODING": "utf-8", "THAMDINH_DATA_DIR": str(thu_muc)}, creationflags=co,
        )
    (thu_muc / FILE_TRANG_THAI).write_text(
        json.dumps({"pid": p.pid, "doi_so": doi_so, "bat_dau": bat_dau.isoformat(timespec="seconds"),
                    "nhat_ky": str(nhat_ky)}, ensure_ascii=False),
        encoding="utf-8",
    )
    return trang_thai(thu_muc, con_song)


def trang_thai(thu_muc: str | Path, con_song: Callable[[int], bool] = _con_song) -> TrangThaiChay | None:
    """Lần chạy gần nhất (đang chạy hay đã thoát); None nếu chưa chạy lần nào."""
    file = Path(thu_muc) / FILE_TRANG_THAI
    if not file.is_file():
        return None
    d = json.loads(file.read_text(encoding="utf-8"))
    nhat_ky = Path(d["nhat_ky"])
    noi_dung = nhat_ky.read_text(encoding="utf-8", errors="replace") if nhat_ky.is_file() else ""
    ma = MA_LUOT.search(noi_dung)
    return TrangThaiChay(
        dang_chay=con_song(d["pid"]),
        pid=d["pid"],
        doi_so=tuple(d["doi_so"]),
        bat_dau=d["bat_dau"],
        nhat_ky=nhat_ky,
        ma_luot=ma.group(1) if ma else None,
        dong_cuoi=tuple(noi_dung.splitlines()[-SO_DONG_CUOI:]),
    )


def dung(
    thu_muc: str | Path,
    con_song: Callable[[int], bool] = _con_song,
    ket_thuc: Callable[[int], None] = _ket_thuc,
) -> None:
    """Dừng Lượt đang chạy. Các Mục đã xong vẫn còn trong kho; chạy tiếp bằng "Chạy lại phần lỗi"."""
    if (tt := trang_thai(thu_muc, con_song)) and tt.dang_chay:
        ket_thuc(tt.pid)
