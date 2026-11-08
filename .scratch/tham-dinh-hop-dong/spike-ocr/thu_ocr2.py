import glob, time, yaml, sys, unicodedata, re
import numpy as np, pypdfium2 as pdfium
from PIL import Image
Image.ANTIALIAS = Image.LANCZOS
from rapidocr_onnxruntime import RapidOCR
from vietocr.tool.config import Cfg
from vietocr.tool.predictor import Predictor
sys.path.insert(0, "src")
from thamdinh.so_hoa.lop_text import doc_trang

cfg = yaml.safe_load(open("models/vietocr/base.yml", encoding="utf-8"))
cfg.update(yaml.safe_load(open("models/vietocr/vgg-seq2seq.yml", encoding="utf-8")))
cfg = Cfg(cfg); cfg["weights"] = "models/vietocr/vgg_seq2seq.pth"; cfg["device"] = "cpu"; cfg["cnn"]["pretrained"] = False
rec = Predictor(cfg)
eng = RapidOCR()
f = [p for p in glob.glob("Sample/*.pdf") if "TOSS" in p][0]
pdf = pdfium.PdfDocument(f)

def cer(a, b):
    import difflib
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return 1 - sum(m.size for m in sm.get_matching_blocks()) / max(len(a), 1)

def chuan(s):
    s = unicodedata.normalize("NFC", s)
    s = re.sub(r"\[(xóa|thêm|sửa): ", "", s).replace("]", "")
    s = re.sub(r"[“”\"'‘’?]", "", s)
    return re.sub(r"\s+", "", s)

for so in map(int, sys.argv[1:]):
    pg = pdf[so - 1]
    img = pg.render(scale=300/72).to_pil().convert("RGB")
    W = img.width
    for det_dpi in (150,):
        k = 300 / det_dpi
        small = img.resize((int(img.width / k), int(img.height / k)))
        t = time.time()
        boxes, _ = eng(np.array(small)[:, :, ::-1], use_det=True, use_cls=False, use_rec=False)
        tdet = time.time() - t
    rects = []
    for b in boxes:
        xs = [p[0] * k for p in b]; ys = [p[1] * k for p in b]
        rects.append([min(xs), min(ys), max(xs), max(ys)])
    # bỏ khung comment (thô): bỏ vùng bắt đầu ở 68% bề ngang trở đi
    rects = [r for r in rects if r[0] < W * 0.68]
    rects.sort(key=lambda r: (r[1] + r[3]) / 2)
    dong = []
    for r in rects:
        cy = (r[1] + r[3]) / 2
        for d in dong:
            if d["y0"] <= cy <= d["y1"]:
                d["r"].append(r); break
        else:
            dong.append({"y0": r[1], "y1": r[3], "r": [r]})
    crops, idx = [], []
    for i, d in enumerate(dong):
        for r in sorted(d["r"]):
            crops.append(img.crop((r[0] - 6, r[1] - 6, r[2] + 6, r[3] + 6))); idx.append(i)
    t = time.time()
    txt = rec.predict_batch(crops)
    trec = time.time() - t
    out = [[] for _ in dong]
    for i, s in zip(idx, txt): out[i].append(s)
    ocr = "\n".join(" ".join(x) for x in out)
    goc = "\n".join(d.noi_dung for d in doc_trang(pg, so).dong)
    print(f"trang {so}: det {tdet:.1f}s rec {trec:.1f}s, {len(dong)} dòng, CER {cer(chuan(goc), chuan(ocr)):.2%}")
    if so == 2: print(ocr[:700])
