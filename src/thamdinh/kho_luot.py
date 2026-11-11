"""Lưu trữ Lượt thẩm định trong SQLite (`data/tham-dinh.sqlite3`), chỉ nằm trên máy (ADR 0001).

- `luot`: thông tin chung của Lượt.
- `muc_de_xuat`: Kết quả đề xuất, mỗi Mục một dòng JSON. Mục đã có Kết quả thì không sửa, không xóa được (trigger);
  chạy lại Mục đó tạo Lượt mới (`tham_dinh(..., chay_lai=…)`).
- `duyet`: Kết quả đã duyệt theo Mục, chỉ thêm (mỗi lần lưu là một phiên bản), bản mới nhất là hiện tại.
"""

import json
import sqlite3
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from thamdinh.so_hoa import VanBanHieuLuc, hash_noi_dung
from thamdinh.luot import KetQuaLuot, luot_den_dict, luot_tu_dict
from thamdinh.trich_dan import TrichDan, TrichDanDaKiemTra, kiem_tra_va_ghi

TEN_FILE = "tham-dinh.sqlite3"
KET_QUA = ("dat", "luu_y", "vi_pham")
# Cột chỉ mục của bảng `luot`, đúng thứ tự trong SCHEMA; các trường khác của Lượt lưu trong cột `chung` (JSON)
COT_LUOT = ("ma", "hash_pdf", "ten_file", "checklist", "model", "che_do", "bat_dau", "ket_thuc", "hash_van_ban", "luot_goc")

SCHEMA = """
CREATE TABLE IF NOT EXISTS luot (
    ma TEXT PRIMARY KEY,
    hash_pdf TEXT NOT NULL,
    ten_file TEXT NOT NULL,
    checklist TEXT NOT NULL,
    model TEXT NOT NULL,
    che_do TEXT NOT NULL,
    bat_dau TEXT NOT NULL,
    ket_thuc TEXT NOT NULL,
    hash_van_ban TEXT NOT NULL,
    luot_goc TEXT REFERENCES luot(ma),
    chung TEXT NOT NULL  -- JSON: cac_ben, loi_cac_ben, canh_bao
);
CREATE TABLE IF NOT EXISTS muc_de_xuat (
    luot TEXT NOT NULL REFERENCES luot(ma),
    so INTEGER NOT NULL,
    co_ket_qua INTEGER NOT NULL,
    du_lieu TEXT NOT NULL,  -- JSON của KetQuaMucDeXuat
    PRIMARY KEY (luot, so)
);
CREATE TRIGGER IF NOT EXISTS khong_sua_de_xuat BEFORE UPDATE ON muc_de_xuat WHEN OLD.co_ket_qua = 1
BEGIN SELECT RAISE(ABORT, 'Kết quả đề xuất đã có, không được ghi đè'); END;
CREATE TRIGGER IF NOT EXISTS khong_xoa_de_xuat BEFORE DELETE ON muc_de_xuat WHEN OLD.co_ket_qua = 1
BEGIN SELECT RAISE(ABORT, 'Kết quả đề xuất đã có, không được xóa'); END;
CREATE TABLE IF NOT EXISTS duyet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    luot TEXT NOT NULL REFERENCES luot(ma),
    so_muc INTEGER NOT NULL,
    du_lieu TEXT NOT NULL  -- JSON của KetQuaDuyet
);
CREATE TRIGGER IF NOT EXISTS duyet_khong_sua BEFORE UPDATE ON duyet
BEGIN SELECT RAISE(ABORT, 'Kết quả đã duyệt chỉ được thêm phiên bản mới'); END;
CREATE TRIGGER IF NOT EXISTS duyet_khong_xoa BEFORE DELETE ON duyet
BEGIN SELECT RAISE(ABORT, 'Kết quả đã duyệt chỉ được thêm phiên bản mới'); END;
"""


class GhiDeError(ValueError):
    """Cố lưu một Lượt làm thay đổi Kết quả đề xuất đã có."""


@dataclass(frozen=True)
class KetQuaDuyet:
    so_muc: int
    ket_qua: str  # dat | luu_y | vi_pham
    giai_thich: str
    trich_dan: tuple[TrichDanDaKiemTra, ...]
    nguoi_duyet: str
    thoi_diem: str
    phien_ban: int  # 1, 2, … theo thứ tự lưu


@dataclass(frozen=True)
class TomTatLuot:
    ma: str
    ten_file: str
    hash_pdf: str
    checklist: str
    che_do: str
    model: str
    bat_dau: str
    ket_thuc: str
    luot_goc: str | None
    so_muc: int
    so_muc_xong: int  # Mục đã có Kết quả đề xuất
    so_muc_da_duyet: int


class KhoLuot:
    def __init__(self, thu_muc: str | Path):
        self.duong_dan = Path(thu_muc) / TEN_FILE
        self.duong_dan.parent.mkdir(parents=True, exist_ok=True)
        with self._ket_noi() as db:
            db.executescript(SCHEMA)

    def _ket_noi(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.duong_dan)
        db.execute("PRAGMA foreign_keys = ON")
        return db

    def luu(self, kq: KetQuaLuot) -> None:
        """Lưu (hoặc cập nhật khi đang chạy / chạy lại phần lỗi) một Lượt; không bao giờ ghi đè Mục đã có Kết quả."""
        d = luot_den_dict(kq)
        # Mọi trường không phải cột chỉ mục nằm trong `chung`: thêm trường cấp Lượt không cần sửa ở đây
        chung = json.dumps({k: v for k, v in d.items() if k not in COT_LUOT and k != "muc"}, ensure_ascii=False)
        with self._ket_noi() as db:
            cu = db.execute("SELECT chung FROM luot WHERE ma = ?", (kq.ma,)).fetchone()
            if cu and json.loads(cu[0])["cac_ben"] not in (None, json.loads(chung)["cac_ben"]):
                raise GhiDeError(f"Lượt {kq.ma}: kết quả xác định các bên đã có, không được ghi đè")
            db.execute(
                """INSERT INTO luot VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(ma) DO UPDATE SET ket_thuc = excluded.ket_thuc, chung = excluded.chung""",
                (*(d[c] for c in COT_LUOT), chung),
            )
            for m, dm in zip(kq.muc, d["muc"]):
                du_lieu = json.dumps(dm, ensure_ascii=False)
                try:
                    db.execute(
                        """INSERT INTO muc_de_xuat VALUES (?, ?, ?, ?)
                           ON CONFLICT(luot, so) DO UPDATE SET co_ket_qua = excluded.co_ket_qua,
                               du_lieu = excluded.du_lieu
                           WHERE muc_de_xuat.du_lieu != excluded.du_lieu""",
                        (kq.ma, m.so, int(m.ket_qua is not None), du_lieu),
                    )
                except sqlite3.IntegrityError as e:
                    raise GhiDeError(
                        f"Lượt {kq.ma}, Mục {m.so}: Kết quả đề xuất đã có, không được ghi đè "
                        "(chạy lại Mục này thì tạo Lượt mới)"
                    ) from e

    def nap(self, ma: str) -> KetQuaLuot:
        with self._ket_noi() as db:
            dong = db.execute(f"SELECT {', '.join(COT_LUOT)}, chung FROM luot WHERE ma = ?", (ma,)).fetchone()
            if dong is None:
                raise KeyError(f"Không có Lượt {ma}")
            muc = [json.loads(r[0]) for r in db.execute("SELECT du_lieu FROM muc_de_xuat WHERE luot = ? ORDER BY so", (ma,))]
        return luot_tu_dict({**dict(zip(COT_LUOT, dong)), **json.loads(dong[-1]), "muc": muc})

    def danh_sach(self) -> list[TomTatLuot]:
        """Các Lượt đã lưu, mới nhất trước."""
        with self._ket_noi() as db:
            dong = db.execute(
                """SELECT l.ma, l.ten_file, l.hash_pdf, l.checklist, l.che_do, l.model, l.bat_dau, l.ket_thuc, l.luot_goc,
                          (SELECT COUNT(*) FROM muc_de_xuat m WHERE m.luot = l.ma),
                          (SELECT COUNT(*) FROM muc_de_xuat m WHERE m.luot = l.ma AND m.co_ket_qua = 1),
                          (SELECT COUNT(DISTINCT so_muc) FROM duyet d WHERE d.luot = l.ma)
                   FROM luot l ORDER BY l.bat_dau DESC, l.ma DESC"""
            ).fetchall()
        return [TomTatLuot(*r) for r in dong]

    def luu_duyet(
        self,
        ma_luot: str,
        so_muc: int,
        ket_qua: str,
        giai_thich: str,
        trich_dan: Sequence[TrichDan],
        nguoi_duyet: str,
        van_ban: VanBanHieuLuc,
    ) -> KetQuaDuyet:
        """Thêm một phiên bản Kết quả đã duyệt cho Mục; Trích dẫn được kiểm tra lại với Văn bản hiệu lực Lượt đã dùng."""
        luot = self.nap(ma_luot)
        if ket_qua not in KET_QUA:
            raise ValueError(f"ket_qua '{ket_qua}' không hợp lệ, phải là {' | '.join(KET_QUA)}")
        if so_muc not in {m.so for m in luot.muc}:
            raise ValueError(f"Lượt {ma_luot} không có Mục {so_muc}")
        if not nguoi_duyet.strip():
            raise ValueError("Chưa ghi người duyệt")
        if (van_ban.hash_pdf, hash_noi_dung(van_ban)) != (luot.hash_pdf, luot.hash_van_ban):
            raise ValueError("Văn bản hiệu lực khác bản mà Lượt đã dùng (đã sửa tay sau khi chạy?)")
        da_kiem_tra = [kiem_tra_va_ghi(td, van_ban) for td in trich_dan]
        with self._ket_noi() as db:
            (phien_ban,) = db.execute(
                "SELECT COUNT(*) + 1 FROM duyet WHERE luot = ? AND so_muc = ?", (ma_luot, so_muc)
            ).fetchone()
            duyet = KetQuaDuyet(so_muc, ket_qua, giai_thich, tuple(da_kiem_tra), nguoi_duyet.strip(),
                                datetime.now().isoformat(timespec="seconds"), phien_ban)
            db.execute("INSERT INTO duyet (luot, so_muc, du_lieu) VALUES (?, ?, ?)",
                       (ma_luot, so_muc, json.dumps(asdict(duyet), ensure_ascii=False)))
        return duyet

    def lich_su_duyet(self, ma_luot: str, so_muc: int) -> list[KetQuaDuyet]:
        with self._ket_noi() as db:
            dong = db.execute(
                "SELECT du_lieu FROM duyet WHERE luot = ? AND so_muc = ? ORDER BY id", (ma_luot, so_muc)
            ).fetchall()
        return [_duyet_tu_json(r[0]) for r in dong]

    def nap_duyet(self, ma_luot: str) -> dict[int, KetQuaDuyet]:
        """Kết quả đã duyệt hiện tại (phiên bản mới nhất) của từng Mục đã duyệt."""
        with self._ket_noi() as db:
            dong = db.execute("SELECT so_muc, du_lieu FROM duyet WHERE luot = ? ORDER BY id", (ma_luot,)).fetchall()
        return {so: _duyet_tu_json(du_lieu) for so, du_lieu in dong}


def _duyet_tu_json(du_lieu: str) -> KetQuaDuyet:
    d = json.loads(du_lieu)
    return KetQuaDuyet(**{**d, "trich_dan": tuple(TrichDanDaKiemTra(**t) for t in d["trich_dan"])})
