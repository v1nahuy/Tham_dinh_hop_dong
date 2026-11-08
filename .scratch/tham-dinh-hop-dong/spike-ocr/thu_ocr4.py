"""So sánh bộ phát hiện chữ (RapidOCR PP-OCRv4, PaddleOCR PP-OCRv5 mobile/server) x VietOCR (vgg_seq2seq, vgg_transformer).

Chạy từ thư mục gốc repo: .venv/Scripts/python .scratch/tham-dinh-hop-dong/spike-ocr/thu_ocr4.py 2 3 8
Đo CER so với lớp text, và tỉ lệ đọc đúng số hiệu khoản (có / không đọc lại vùng số ở đầu dòng bằng PP-OCRv5 rec, Q39 b).
"""

import difflib
import glob
import re
import sys
import time
import unicodedata

import numpy as np
import pypdfium2 as pdfium
import yaml
from PIL import Image

Image.ANTIALIAS = Image.LANCZOS  # VietOCR 0.3.12 dùng tên cũ của Pillow
from paddleocr import TextDetection, TextRecognition  # noqa: E402
from rapidocr_onnxruntime import RapidOCR  # noqa: E402
from vietocr.tool.config import Cfg  # noqa: E402
from vietocr.tool.predictor import Predictor  # noqa: E402

sys.path.insert(0, "src")
from thamdinh.so_hoa.lop_text import doc_trang  # noqa: E402


def vietocr(ten):
    cfg = yaml.safe_load(open("models/vietocr/base.yml", encoding="utf-8"))
    cfg.update(yaml.safe_load(open(f"models/vietocr/{ten.replace('_', '-')}.yml", encoding="utf-8")))
    cfg = Cfg(cfg)
    cfg["weights"] = f"models/vietocr/{ten}.pth"
    cfg["device"] = "cpu"
    cfg["cnn"]["pretrained"] = False
    return Predictor(cfg)


NHAN_DANG = {ten: vietocr(ten) for ten in ("vgg_seq2seq", "vgg_transformer")}
PADDLE_REC = TextRecognition(model_name="PP-OCRv5_server_rec", enable_mkldnn=False)
RAPID = RapidOCR()
PADDLE_DET = {m: TextDetection(model_name=m, enable_mkldnn=False) for m in ("PP-OCRv5_mobile_det", "PP-OCRv5_server_det")}
SO_HIEU = re.compile(r"(?<![\d.])(\d{1,2}(?:\.\d{1,2})+)\.")
CHI_SO = re.compile(r"^[\d.]+$")


def phat_hien(ten, anh_nho):
    bgr = np.array(anh_nho)[:, :, ::-1]
    if ten == "rapid_v4":
        hop, _ = RAPID(bgr, use_det=True, use_cls=False, use_rec=False)
        return hop or []
    return PADDLE_DET[ten].predict(bgr)[0]["dt_polys"]


def cer(a, b):
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return 1 - sum(m.size for m in sm.get_matching_blocks()) / max(len(a), 1)


def chuan(s):
    s = unicodedata.normalize("NFC", s)
    s = re.sub(r"\[(xóa|thêm|sửa): ", "", s).replace("]", "")
    s = re.sub(r"[“”\"'‘’?]", "", s)
    return re.sub(r"\s+", "", s)


f = next(p for p in glob.glob("Sample/*.pdf") if "TOSS" in p)
pdf = pdfium.PdfDocument(f)
print(f"{'trang':>5} {'phát hiện':<20} {'nhận dạng':<16} {'CER':>6} {'số hiệu':>8} {'+PP rec':>8} {'giây':>5}")
for so in map(int, sys.argv[1:]):
    trang = pdf[so - 1]
    anh = trang.render(scale=300 / 72).to_pil().convert("RGB")
    goc = "\n".join(d.noi_dung for d in doc_trang(trang, so).dong)
    so_hieu_goc = set(SO_HIEU.findall(goc))
    k = 2  # phát hiện ở 150 dpi, nhận dạng trên ảnh 300 dpi
    nho = anh.resize((anh.width // k, anh.height // k))
    for det in ("rapid_v4",):
        t0 = time.time()
        hop = phat_hien(det, nho)
        t_det = time.time() - t0
        vung = []
        for h in hop:
            xs = [p[0] * k for p in h]
            ys = [p[1] * k for p in h]
            vung.append([min(xs), min(ys), max(xs), max(ys)])
        vung = [v for v in vung if v[0] < anh.width * 0.68]  # bỏ khung comment (thô)
        vung.sort(key=lambda v: (v[1] + v[3]) / 2)
        dong = []
        for v in vung:
            cy = (v[1] + v[3]) / 2
            for d in dong:
                if d["y0"] <= cy <= d["y1"]:
                    d["v"].append(v)
                    break
            else:
                dong.append({"y0": v[1], "y1": v[3], "v": [v]})
        cat, vi_tri = [], []
        for i, d in enumerate(dong):
            for j, v in enumerate(sorted(d["v"])):
                cat.append(anh.crop((v[0] - 6, v[1] - 6, v[2] + 6, v[3] + 6)))
                vi_tri.append((i, j))
        dau_dong = [n for n, (i, j) in enumerate(vi_tri) if j == 0 and cat[n].width < 260]  # vùng ngắn đầu dòng
        doc_lai = {}
        for n in dau_dong:
            r, _ = RAPID(np.array(cat[n])[:, :, ::-1], use_det=False, use_cls=False, use_rec=True)
            txt = r[0][0] if r else ""
            if CHI_SO.match(txt) and "." in txt:
                doc_lai[n] = txt
        for ten, nd in NHAN_DANG.items():
            t0 = time.time()
            chu = nd.predict_batch(cat)
            t_rec = time.time() - t0
            for dung_pp in (False, True):
                ra = [[] for _ in dong]
                for n, ((i, _), s) in enumerate(zip(vi_tri, chu)):
                    ra[i].append(doc_lai.get(n, s) if dung_pp else s)
                ocr = "\n".join(" ".join(x) for x in ra)
                dung = len(so_hieu_goc & set(SO_HIEU.findall(ocr))) / max(len(so_hieu_goc), 1)
                if not dung_pp:
                    c, d0 = cer(chuan(goc), chuan(ocr)), dung
                else:
                    print(f"{so:>5} {det:<20} {ten:<16} {c:>6.1%} {d0:>8.0%} {dung:>8.0%} {t_det + t_rec:>5.0f}",
                          flush=True)
