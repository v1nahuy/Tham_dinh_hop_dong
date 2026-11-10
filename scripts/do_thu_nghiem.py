"""Chạy thử model: chạy tiếp một Lượt gốc với các Mục chọn, rồi so với Lượt gốc theo Bộ chuẩn (issue 25).

Cách làm cả lần thử (xác nhận, kiểm tra mỗi giờ, tắt máy chủ, giữ/bỏ): docs/agents/thu-nghiem-model.md.

Chạy (nền, cần llama-server):
  .venv/Scripts/python scripts/do_thu_nghiem.py --tiep-tuc <mã Lượt gốc> --chi-muc 3,4,13
      [--env THAMDINH_X=gia_tri ...] [--toi-da-phut 180] [--tang-toi-thieu 3] [--dung-thanh-sai-toi-da 1]
      [--pdf sample/...TOSS....pdf] [--bo-chuan eval/chuan/toss.yaml] [--checklist checklists/dau-ra-v1.1.yaml]
      > data/nhat-ky/thu-nghiem-<tên>.log
In "Xong chuỗi" ở dòng cuối khi kết thúc (kể cả khi lỗi hoặc dừng vì quá giờ).
"""

import argparse
import os
import subprocess
import sys
import time
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
    from thamdinh.bo_chuan import nap_bo_chuan
    from thamdinh.checklist import load_checklist
    from thamdinh.kho_luot import KhoLuot
    from thamdinh.llm import may_chu_san_sang
    from thamdinh.settings import load_settings

    s = load_settings()
    d = s.data_dir
    ghi(f"Cấu hình: {', '.join(a.env) or 'mặc định'}; suy luận {s.suy_luan}, ngân sách truy xuất {s.ngan_sach_truy_xuat}")
    if not may_chu_san_sang(s.local_url, httpx.Client()):
        ghi(f"LỖI: llama-server chưa sẵn sàng ở {s.local_url}")
        return
    so_muc = tuple(int(x) for x in a.chi_muc.split(","))
    pdf = str(a.pdf or next((GOC / "sample").glob("*TOSS*.pdf")))

    t0 = time.time()
    tt = chay_nen.khoi_chay([pdf, "--tiep-tuc", a.tiep_tuc, "--chi-muc", a.chi_muc], d)
    ghi(f"Bắt đầu pid {tt.pid}, nhật ký Lượt {tt.nhat_ky}, Mục {a.chi_muc}")
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
    print(kq.stdout[-4000:], kq.stderr[-2000:], flush=True)
    bc = nap_bo_chuan(a.bo_chuan, load_checklist(a.checklist))
    for m in luot.muc:
        if m.so not in so_muc or m.ket_qua is None:
            continue
        for t in m.tieu_chi:
            ghi(f"  {t.ma}: {t.danh_gia} chuẩn={bc.danh_gia[t.ma].danh_gia} | {t.ly_do[:160]}")
        ghi(f"Kết quả Mục {m.so}: {m.ket_qua.ket_qua}, chuẩn {bc.ket_qua_muc.get(m.so)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--tiep-tuc", required=True, help="mã Lượt gốc")
    ap.add_argument("--chi-muc", required=True, help="các Mục chạy lại, ví dụ 3,4,13")
    ap.add_argument("--env", action="append", default=[], help="KEY=VAL, đặt thêm biến môi trường (lặp được)")
    ap.add_argument("--toi-da-phut", type=float, default=180)
    ap.add_argument("--tang-toi-thieu", type=int, default=3)
    ap.add_argument("--dung-thanh-sai-toi-da", type=int, default=1)
    ap.add_argument("--pdf", type=Path)
    ap.add_argument("--bo-chuan", type=Path, default=GOC / "eval" / "chuan" / "toss.yaml")
    ap.add_argument("--checklist", type=Path, default=GOC / "checklists" / "dau-ra-v1.1.yaml")
    try:
        main(ap.parse_args())
    finally:
        ghi("Xong chuỗi")
