"""Chấm lại mọi Lượt trong kho bằng code hiện tại, không gọi model (issue 25, docs/agents/thu-nghiem-model.md).

Chạy: .venv/Scripts/python scripts/cham_lai_kho.py [--so-voi <commit>] [--luot ma1,ma2]
                 [--bo-chuan eval/chuan/toss.yaml] [--checklist checklists/dau-ra-v1.1.yaml]

- Không có `--so-voi`: in số Tiêu chí và Kết quả Mục khớp Bộ chuẩn của từng Lượt, và trạng thái Trích dẫn.
- `--so-voi <commit>`: chấm thêm bằng code ở commit đó (git worktree tạm) rồi in chuyển trạng thái cũ → mới.
So với Bộ chuẩn chỉ tính các Lượt của đúng Hợp đồng trong Bộ chuẩn (cùng hash PDF).
`--so-voi` chấm bằng các module `thamdinh` ở commit đó nhưng `cham_lai.py` của bản này, nên không đo thay đổi trong
chính `cham_lai.py`.
"""

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent


def _nap_cham_lai():
    """Nạp `cham_lai.py` của bản code này theo đường dẫn: trong worktree cũ, các module `thamdinh` khác là bản cũ."""
    spec = importlib.util.spec_from_file_location("cham_lai_ban_nay", GOC / "src" / "thamdinh" / "cham_lai.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # dataclass cần tìm được module khi chú thích kiểu là chuỗi
    spec.loader.exec_module(mod)
    return mod


def _cham(checklist: Path, data: Path):
    from thamdinh.checklist import load_checklist
    from thamdinh.kho_luot import KhoLuot

    cl = _nap_cham_lai()
    return cl, cl.cham_lai(KhoLuot(data), load_checklist(checklist), data)


def _cham_o_commit(commit: str, checklist: Path, data: Path):
    if subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"{commit}^{{commit}}"], cwd=GOC,
                      capture_output=True).returncode:
        sys.exit(f"Không có commit {commit}")
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tam:
        wt, ra = Path(tam) / "wt", Path(tam) / "cham.json"
        subprocess.run(["git", "worktree", "add", "--detach", str(wt), commit], cwd=GOC, check=True,
                       capture_output=True)
        try:
            env = {**os.environ, "PYTHONPATH": str(wt / "src")}
            subprocess.run([sys.executable, __file__, "--chi-ghi-json", str(ra), "--checklist", str(checklist),
                            "--data", str(data)], cwd=GOC, env=env, check=True)
            return json.loads(ra.read_text(encoding="utf-8"))
        finally:  # không check: lỗi dọn worktree không được che lỗi chấm
            subprocess.run(["git", "worktree", "remove", "--force", str(wt)], cwd=GOC, capture_output=True)
            subprocess.run(["git", "worktree", "prune"], cwd=GOC, capture_output=True)


def _loc(cl, kq, chi: set[str] | None):
    return cl.ChamKho({ma: l for ma, l in kq.luot.items() if chi is None or ma in chi},
                      {ma: e for ma, e in kq.loi.items() if chi is None or ma in chi})


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--so-voi", help="commit để so (ví dụ HEAD)")
    ap.add_argument("--luot", help="chỉ chấm các Lượt này, cách nhau bằng dấu phẩy")
    ap.add_argument("--bo-chuan", type=Path, default=GOC / "eval" / "chuan" / "toss.yaml")
    ap.add_argument("--checklist", type=Path, default=GOC / "checklists" / "dau-ra-v1.1.yaml")
    ap.add_argument("--data", type=Path)
    ap.add_argument("--chi-ghi-json", type=Path, help=argparse.SUPPRESS)  # dùng nội bộ, trong worktree
    a = ap.parse_args()
    checklist = a.checklist.resolve()

    if a.data is None:
        from thamdinh.settings import load_settings

        a.data = Path(load_settings().data_dir)
    data = a.data.resolve()

    if a.chi_ghi_json:
        cl, kq = _cham(checklist, data)
        a.chi_ghi_json.write_text(json.dumps(cl.den_json(kq), ensure_ascii=False), encoding="utf-8")
        sys.exit(0)

    from thamdinh.bo_chuan import nap_bo_chuan
    from thamdinh.checklist import load_checklist

    bc = nap_bo_chuan(a.bo_chuan, load_checklist(checklist))
    chi = set(a.luot.split(",")) if a.luot else None
    cl, moi = _cham(checklist, data)
    moi = _loc(cl, moi, chi)
    cu = _loc(cl, cl.tu_json(_cham_o_commit(a.so_voi, checklist, data)), chi) if a.so_voi else moi
    for ten, kq in (("code cũ", cu), ("code hiện tại", moi)) if a.so_voi else (("", moi),):
        for ma, loi in kq.loi.items():
            print(f"Không chấm được {ma}" + (f" bằng {ten}" if ten else "") + f": {loi}")
    for ma, l in moi.luot.items():
        if l.trich_dan is None:
            print(f"{ma}: thiếu Văn bản hiệu lực, không kiểm lại Trích dẫn")

    sc = cl.so_cham(cu, moi, bc)
    so_tc, so_muc = len(bc.danh_gia), sum(1 for k in bc.ket_qua_muc.values() if k)
    print(f"Bộ chuẩn: {a.bo_chuan.name}, {so_tc} Tiêu chí, {so_muc} Kết quả Mục")
    for ma in sorted(sc.luot):
        l = sc.luot[ma]
        if moi.luot[ma].hash_pdf != bc.hash_pdf:
            print(f"- {ma}: Lượt của Hợp đồng khác, không so Bộ chuẩn")
            continue
        if not a.so_voi:
            print(f"- {ma}: Tiêu chí {l.dung_sau}/{so_tc}, Kết quả Mục {l.muc_dung_sau}/{so_muc}")
            continue
        print(f"- {ma}: Tiêu chí {l.dung_truoc}→{l.dung_sau}/{so_tc}, Kết quả Mục {l.muc_dung_truoc}→{l.muc_dung_sau}/{so_muc}")
        if l.sai_thanh_dung:
            print(f"  - sai→đúng: {', '.join(l.sai_thanh_dung)}")
        if l.dung_thanh_sai:
            print(f"  - đúng→sai: {', '.join(l.dung_thanh_sai)}")
        if l.muc_doi:
            print("  - Kết quả Mục đổi: " + ", ".join(f"{so}: {t} → {s}" for so, t, s in l.muc_doi))
    print("Trích dẫn" + (" (cũ → mới):" if a.so_voi else ":"))
    if a.so_voi:
        for (t, s), n in sorted(sc.trich_dan.items()):
            print(f"  {t} → {s}: {n}")
    else:
        dem = Counter(tt for l in moi.luot.values() for td in (l.trich_dan or {}).values() for tt in td)
        for tt, n in sorted(dem.items()):
            print(f"  {tt}: {n}")
