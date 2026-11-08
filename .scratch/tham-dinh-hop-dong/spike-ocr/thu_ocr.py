import glob, time, yaml, sys
import numpy as np, pypdfium2 as pdfium
from PIL import Image
Image.ANTIALIAS = Image.LANCZOS
from rapidocr_onnxruntime import RapidOCR
from vietocr.tool.config import Cfg
from vietocr.tool.predictor import Predictor

cfg = yaml.safe_load(open("models/vietocr/base.yml", encoding="utf-8"))
cfg.update(yaml.safe_load(open("models/vietocr/vgg-seq2seq.yml", encoding="utf-8")))
cfg = Cfg(cfg)
cfg["weights"] = "models/vietocr/vgg_seq2seq.pth"
cfg["device"] = "cpu"
cfg["cnn"]["pretrained"] = False
t = time.time(); rec = Predictor(cfg); print("load vietocr", round(time.time()-t, 1))

f = [p for p in glob.glob("Sample/*.pdf") if "TOSS" in p][0]
trang = int(sys.argv[1]) if len(sys.argv) > 1 else 2
img = pdfium.PdfDocument(f)[trang - 1].render(scale=300/72).to_pil().convert("RGB")
eng = RapidOCR()
for lan in range(2):
    t = time.time()
    boxes, _ = eng(np.array(img)[:, :, ::-1], use_det=True, use_cls=False, use_rec=False)
    print("det", round(time.time()-t, 1))
boxes = sorted(boxes, key=lambda b: (b[0][1], b[0][0]))
crops = []
for b in boxes:
    xs = [p[0] for p in b]; ys = [p[1] for p in b]
    crops.append(img.crop((min(xs)-4, min(ys)-4, max(xs)+4, max(ys)+4)))
t = time.time()
txt = rec.predict_batch(crops)
print("rec", round(time.time()-t, 1), "s cho", len(crops), "dòng")
for s in txt[:16]: print(" ", s)
