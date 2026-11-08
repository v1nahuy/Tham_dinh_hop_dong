"""So hai lần chạy cùng chế độ (trước / sau khi đổi prompt) theo Bộ chuẩn, trên các Mục đã chạy lại (issue 17).

Chạy: .venv/Scripts/python scripts/so_sanh_lan_chay.py <hop_dong.pdf> --truoc <mã Lượt> --sau <mã Lượt> --muc 3,4,8
                 [--bo-chuan eval/chuan/toss.yaml] [--checklist checklist.yaml] [--ra eval/so-sanh]
Lượt sau thường tạo bằng `chay_tham_dinh.py <pdf> --tiep-tuc <Lượt trước> --chi-muc …`.
Giữ thay đổi khi số Tiêu chí đúng tăng ít nhất TANG_TOI_THIEU và không quá DUNG_THANH_SAI_TOI_DA Tiêu chí đúng thành sai (Q122).
"""

import argparse
import sys
from pathlib import Path

from thamdinh.bo_chuan import nap_bo_chuan
from thamdinh.checklist import load_checklist
from thamdinh.kho_luot import KhoLuot
from thamdinh.settings import load_settings
from thamdinh.so_sanh import DongLanChay, so_sanh_lan_chay
from thamdinh.tong_hop import TEN_DANH_GIA

TANG_TOI_THIEU = 5
DUNG_THANH_SAI_TOI_DA = 3


def _dong(d: DongLanChay) -> list[str]:
    def ten(x):
        return TEN_DANH_GIA[x.danh_gia] if x else "Chưa đánh giá được"

    return [
        f"- **{d.ma}** {d.mo_ta}",
        f"  - Bộ chuẩn: {TEN_DANH_GIA[d.chuan.danh_gia]}" + (f" ({d.chuan.ghi_chu})" if d.chuan.ghi_chu else ""),
        f"  - Trước: {ten(d.truoc)}" + (f": {d.truoc.ly_do}" if d.truoc else ""),
        f"  - Sau: {ten(d.sau)}" + (f": {d.sau.ly_do}" if d.sau else ""),
    ]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--truoc", required=True)
    ap.add_argument("--sau", required=True)
    ap.add_argument("--muc", required=True)
    ap.add_argument("--bo-chuan", type=Path, default=Path("eval/chuan/toss.yaml"))
    ap.add_argument("--checklist", default="checklists/dau-ra-v1.1.yaml")
    ap.add_argument("--ra", type=Path, default=Path("eval/so-sanh"))
    ap.add_argument("--tang-toi-thieu", type=int, default=TANG_TOI_THIEU)
    ap.add_argument("--dung-thanh-sai-toi-da", type=int, default=DUNG_THANH_SAI_TOI_DA)
    args = ap.parse_args()
    kho = KhoLuot(load_settings().data_dir)
    checklist = load_checklist(args.checklist)
    truoc, sau = kho.nap(args.truoc), kho.nap(args.sau)
    muc = sorted({int(x) for x in args.muc.split(",") if x.strip()})
    kq = so_sanh_lan_chay(checklist, truoc, sau, nap_bo_chuan(args.bo_chuan, checklist, pdf=args.pdf), muc)

    tang = kq.sau.khop - kq.truoc.khop
    giu = tang >= args.tang_toi_thieu and len(kq.dung_thanh_sai) <= args.dung_thanh_sai_toi_da
    dong = [
        f"# So hai lần chạy: {sau.ten_file}", "",
        f"- **Trước:** {truoc.ma} ({truoc.che_do})",
        f"- **Sau:** {sau.ma} ({sau.che_do})",
        f"- **Mục:** {', '.join(map(str, muc))}", "",
        f"**Đúng theo Bộ chuẩn:** trước {kq.truoc.khop}/{kq.truoc.tong}, sau {kq.sau.khop}/{kq.sau.tong} "
        f"(thay đổi {tang:+d}); đúng thành sai {len(kq.dung_thanh_sai)}.", "",
        f"**Theo quy tắc giữ thay đổi** (tăng ít nhất {args.tang_toi_thieu}, "
        f"đúng thành sai không quá {args.dung_thanh_sai_toi_da}): "
        + ("GIỮ thay đổi." if giu else "KHÔNG giữ thay đổi."), "",
    ]
    if truoc.che_do != sau.che_do:
        dong += [f"**Cảnh báo:** hai Lượt khác chế độ ({truoc.che_do}, {sau.che_do}).", ""]
    if kq.canh_bao:
        dong += ["## Cảnh báo ngữ cảnh (so sánh không công bằng ở các Mục này)", "", *(f"- {c}" for c in kq.canh_bao), ""]
    dong += [f"## Sai thành đúng ({len(kq.sai_thanh_dung)})", ""]
    dong += [x for d in kq.sai_thanh_dung for x in _dong(d)]
    dong += ["", f"## Đúng thành sai ({len(kq.dung_thanh_sai)})", ""]
    dong += [x for d in kq.dung_thanh_sai for x in _dong(d)]

    args.ra.mkdir(parents=True, exist_ok=True)
    file = args.ra / f"lan-chay-{sau.ma}.md"
    file.write_text("\n".join(dong) + "\n", encoding="utf-8")
    print("\n".join(dong[5:9]))
    print(f"Báo cáo: {file}")
