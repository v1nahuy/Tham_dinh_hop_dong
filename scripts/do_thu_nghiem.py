"""Chạy thử model: chạy tiếp một Lượt gốc với các Mục chọn, rồi so với Lượt gốc theo Bộ chuẩn (issue 25).

Cách làm cả lần thử (xác nhận, kiểm tra mỗi giờ, tắt máy chủ, giữ/bỏ): docs/agents/thu-nghiem-model.md.

Chạy (nền, cần llama-server):
  .venv/Scripts/python scripts/do_thu_nghiem.py --tiep-tuc <mã Lượt gốc> --chi-muc 3,4,13
      --tang-toi-thieu 3 --dung-thanh-sai-toi-da 1 [--env THAMDINH_X=gia_tri ...] [--toi-da-phut 180]
      [--pdf sample/...TOSS....pdf] [--bo-chuan eval/chuan/toss.yaml] [--checklist checklists/dau-ra-v1.1.yaml]
      > data/nhat-ky/thu-nghiem-<tên>.log 2>&1
In "Xong chuỗi" ở dòng cuối khi kết thúc (kể cả khi lỗi hoặc dừng vì quá giờ).
"""

import argparse
import os
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent


def ghi(x: str) -> None:
    print(f"[{datetime.now():%m-%d %H:%M}] {x}", flush=True)


def main(a) -> None:
    for cap in a.env:  # đặt trước khi nạp cấu hình: tiến trình Lượt kế thừa biến môi trường này
        k, _, v = cap.partition("=")
        os.environ[k] = v

    import httpx

    from thamdinh import chay_nen
    from thamdinh.llm import may_chu_san_sang
    from thamdinh.settings import load_settings

    s = load_settings()
    d = s.data_dir
    ghi(f"Cấu hình: {', '.join(a.env) or 'mặc định'}; suy luận {s.suy_luan}, ngân sách truy xuất {s.ngan_sach_truy_xuat}")
    if not may_chu_san_sang(s.local_url, httpx.Client()):
        ghi(f"LỖI: llama-server chưa sẵn sàng ở {s.local_url}")
        return
    so_muc = tuple(int(x) for x in a.chi_muc.split(","))
    pdf = a.pdf or next((GOC / "sample").glob("*TOSS*.pdf"), None)
    if pdf is None or not Path(pdf).is_file():
        ghi(f"LỖI: không thấy PDF {pdf or 'sample/*TOSS*.pdf'}")
        return
    pdf = str(pdf)

    t0 = time.time()
    tt = chay_nen.khoi_chay([pdf, "--tiep-tuc", a.tiep_tuc, "--chi-muc", a.chi_muc], d)
    ghi(f"Bắt đầu pid {tt.pid}, nhật ký Lượt {tt.nhat_ky}, Mục {a.chi_muc}")
    try:
        _cho_va_so_sanh(a, d, pdf, t0, so_muc)
    finally:  # kể cả khi lỗi hoặc bị ngắt: không để Lượt chạy nền mồ côi
        if (tt := chay_nen.trang_thai(d)) and tt.dang_chay:
            ghi("Dừng Lượt đang chạy nền")
            chay_nen.dung(d)


def _cho_va_so_sanh(a, d, pdf: str, t0: float, so_muc: tuple[int, ...]) -> None:
    from thamdinh import chay_nen
    from thamdinh.bo_chuan import nap_bo_chuan
    from thamdinh.checklist import load_checklist
    from thamdinh.kho_luot import KhoLuot

    while chay_nen.trang_thai(d).dang_chay:
        if (time.time() - t0) / 60 > a.toi_da_phut:
            ghi(f"Quá {a.toi_da_phut} phút: dừng")
            chay_nen.dung(d)
            break
        time.sleep(60)
    tt = chay_nen.trang_thai(d)
    ghi(f"Lượt sau {tt.ma_luot}, {(time.time() - t0) / 60:.0f} phút")
    if not tt.ma_luot or tt.ma_luot == a.tiep_tuc:
        ghi("LỖI: không có Lượt mới")
        return
    luot = KhoLuot(d).nap(tt.ma_luot)
    thieu = [m for m in luot.muc if m.so in so_muc and m.ket_qua is None]
    for m in thieu:
        ghi(f"Mục {m.so} chưa đánh giá được: {m.loi}")

    kq = subprocess.run(
        [sys.executable, str(GOC / "scripts" / "so_sanh_lan_chay.py"), pdf, "--truoc", a.tiep_tuc, "--sau", tt.ma_luot,
         "--muc", a.chi_muc, "--bo-chuan", str(a.bo_chuan), "--checklist", str(a.checklist),
         "--tang-toi-thieu", str(a.tang_toi_thieu), "--dung-thanh-sai-toi-da", str(a.dung_thanh_sai_toi_da)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    print(kq.stdout, kq.stderr, flush=True)
    if kq.returncode:
        ghi(f"LỖI: so_sanh_lan_chay.py thoát mã {kq.returncode}")
    bc = nap_bo_chuan(a.bo_chuan, load_checklist(a.checklist))
    for m in luot.muc:
        if m.so not in so_muc or m.ket_qua is None:
            continue
        for t in m.tieu_chi:
            chuan = bc.danh_gia.get(t.ma)
            ghi(f"  {t.ma}: {t.danh_gia} chuẩn={chuan.danh_gia if chuan else '-'} | {t.ly_do[:160]}")
        ghi(f"Kết quả Mục {m.so}: {m.ket_qua.ket_qua}, chuẩn {bc.ket_qua_muc.get(m.so)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--tiep-tuc", required=True, help="mã Lượt gốc")
    ap.add_argument("--chi-muc", required=True, help="các Mục chạy lại, ví dụ 3,4,13")
    ap.add_argument("--env", action="append", default=[], help="KEY=VAL, đặt thêm biến môi trường (lặp được)")
    ap.add_argument("--toi-da-phut", type=float, default=180)
    ap.add_argument("--tang-toi-thieu", type=int, required=True, help="theo quy tắc giữ đã ghi trong issue")
    ap.add_argument("--dung-thanh-sai-toi-da", type=int, required=True, help="theo quy tắc giữ đã ghi trong issue")
    ap.add_argument("--pdf", type=Path)
    ap.add_argument("--bo-chuan", type=Path, default=GOC / "eval" / "chuan" / "toss.yaml")
    ap.add_argument("--checklist", type=Path, default=GOC / "checklists" / "dau-ra-v1.1.yaml")
    ma_thoat = 0
    try:
        main(ap.parse_args())
    except SystemExit as e:  # argparse báo thiếu tham số (đã in ra stderr)
        ma_thoat = e.code
    except BaseException:  # ghi lỗi vào nhật ký trước "Xong chuỗi", để người kiểm tra mỗi giờ thấy
        ghi("LỖI: " + traceback.format_exc())
        ma_thoat = 1
    finally:
        ghi("Xong chuỗi")
    sys.exit(ma_thoat)
