"""Xử lý ảnh trang trước khi OCR (không cần model): cắt khung comment, chỉnh nghiêng, phát hiện redline, ghép dòng."""

from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image

# Khung comment của Word khi in ra PDF: dải nền xám nhạt (khoảng 242) chạy gần hết chiều cao, ở lề phải trang.
# Bản scan có nhiễu và JPEG làm nền trắng tối đi (khoảng 248), nên không dùng ngưỡng tuyệt đối: làm mờ ảnh theo chiều
# dọc cho hết nhiễu (không làm mờ ngang để mép dải và các đường dọc mảnh không bị trải ra), lấy mức xám của dải ở phần
# lề phải, so với nền trang (nửa trái); điểm có độ sáng gần mức xám đó là điểm xám. Cột là cột xám khi quá nửa số điểm
# là điểm xám, nên phần bảng tràn vào dải xám (trang 51 của TOSS) không bị cắt.
TOI_HON_NEN = 5
GAN_MUC_XAM = 5
XAM_TOI_THIEU = 200
DO_LECH_MAU_XAM = 10
TY_LE_COT_XAM = 0.5
LAM_MO_DOC = 31
# Dải xám có thể cách mép phải một lề trắng hẹp (trang khổ ngang / Letter, góc trang scan đã chỉnh nghiêng).
LE_PHAI_TOI_DA = 0.05
VUNG_DO_MUC_XAM = (0.8, 0.95)  # phần bề ngang để đo mức xám của dải
DAI_XAM_TOI_THIEU = 0.04  # dải xám hẹp hơn tỉ lệ bề ngang này không phải khung comment


def cat_khung_comment(anh: Image.Image) -> tuple[Image.Image, bool]:
    """Bỏ dải nền xám bên phải trang (khung comment). Trả về ảnh đã cắt và có tìm thấy khung hay không."""
    x = cv2.blur(np.asarray(anh.convert("RGB")), (1, LAM_MO_DOC))[::4].astype(np.int16)
    sang = x.mean(2)
    lech_mau = x.max(2) - x.min(2)
    rong = anh.width
    nen = np.percentile(sang[:, : rong // 2], 90)  # mức sáng của giấy trắng, kể cả trang chữ dày
    muc_xam = np.median(sang[:, int(rong * VUNG_DO_MUC_XAM[0]) : int(rong * VUNG_DO_MUC_XAM[1])])
    if not XAM_TOI_THIEU <= muc_xam <= nen - TOI_HON_NEN:
        return anh, False
    diem_xam = (np.abs(sang - muc_xam) <= GAN_MUC_XAM) & (lech_mau < DO_LECH_MAU_XAM)
    cot_xam = diem_xam.mean(0) > TY_LE_COT_XAM
    # Tìm từ mép phải sang: bỏ qua lề trắng và các vệt xám hẹp (mép trang scan) trong phạm vi lề cho phép.
    bat_dau = rong
    while True:
        ket_thuc = bat_dau
        while ket_thuc > rong * (1 - LE_PHAI_TOI_DA) and not cot_xam[ket_thuc - 1]:
            ket_thuc -= 1
        bat_dau = ket_thuc
        while bat_dau > 0 and cot_xam[bat_dau - 1]:
            bat_dau -= 1
        if bat_dau == ket_thuc:
            return anh, False
        if ket_thuc - bat_dau >= DAI_XAM_TOI_THIEU * rong:
            break
    if bat_dau < rong // 2:
        return anh, False
    return anh.crop((0, 0, bat_dau, anh.height)), True


# Chỉnh nghiêng bằng hình chiếu theo hàng: góc đúng làm các dòng chữ thẳng hàng, tổng theo hàng "nhọn" nhất.
NGHIENG_TOI_DA = 5.0
BO_QUA_NGHIENG = 0.15
RONG_DO_NGHIENG = 600


def chinh_nghieng(anh: Image.Image) -> tuple[Image.Image, float]:
    """Tìm góc nghiêng (độ, ngược chiều kim đồng hồ) và xoay lại; góc dưới 0,15° thì giữ nguyên ảnh."""
    ti_le = RONG_DO_NGHIENG / anh.width
    nho = anh.convert("L").resize((RONG_DO_NGHIENG, max(1, round(anh.height * ti_le))))
    muc = Image.fromarray(((np.asarray(nho) < 160) * 255).astype(np.uint8))

    def do_net(goc: float) -> float:
        hang = np.asarray(muc.rotate(-goc, resample=Image.Resampling.BILINEAR)).sum(1, dtype=np.float64)
        return float(np.square(np.diff(hang)).sum())

    tot_nhat = max(np.arange(-NGHIENG_TOI_DA, NGHIENG_TOI_DA + 0.01, 0.5), key=do_net)
    tot_nhat = max(np.arange(tot_nhat - 0.5, tot_nhat + 0.51, 0.05), key=do_net)
    goc = round(float(tot_nhat), 2)
    if abs(goc) < BO_QUA_NGHIENG:
        return anh, 0.0
    return anh.rotate(-goc, resample=Image.Resampling.BICUBIC, fillcolor="white"), goc


# Hộp chữ (trái, trên, phải, dưới) theo pixel ảnh.
Hop = tuple[float, float, float, float]
# Hai hộp cùng dòng khi phần chồng theo chiều dọc chiếm ít nhất tỉ lệ này của hộp thấp hơn.
CHONG_CUNG_DONG = 0.5


def ghep_dong(hop: list[Hop]) -> list[list[Hop]]:
    """Ghép các hộp chữ cùng dòng (số hiệu khoản và nội dung có thể là hai hộp), trên xuống, trái sang."""
    dong: list[list[Hop]] = []
    for h in sorted(hop, key=lambda h: (h[1] + h[3]) / 2):
        for d in dong:
            dau = d[0]
            chong = min(h[3], dau[3]) - max(h[1], dau[1])
            if chong >= CHONG_CUNG_DONG * min(h[3] - h[1], dau[3] - dau[1]):
                d.append(h)
                break
        else:
            dong.append([h])
    return [sorted(d) for d in dong]


# ---- Redline trên ảnh một hộp chữ ----
# Mực: điểm đủ tối (nền highlight vàng, nền cam nhạt của Word không tính).
NGUONG_MUC = 180
# Màu lõi (các điểm tối nhất) của một nét chữ: kênh nhỏ nhất trên ngưỡng này (chữ xám) hoặc lệch màu rõ thì là chữ
# redline, giống `NGUONG_DEN` của lớp text. Chữ đen in ra có lõi gần 0.
NGUONG_DEN_ANH = 50
LECH_MAU = 60
# Nét gạch là dải ngang dài; độ dài tối thiểu tính theo chiều cao hộp (lượt đầu) rồi theo chiều cao chữ x.
NET_TOI_THIEU_CAO_HOP = 0.9
NET_TOI_THIEU_CAO_X = 1.6
TY_LE_HANG_THAN_CHU = 0.35
# Vị trí nét theo thân chữ (0 = đỉnh chữ x, 1 = chân chữ): khoảng giữa là gạch ngang, dưới chân là gạch chân.
GACH_NGANG = (0.2, 0.85)
GACH_CHAN_TU = 1.05
# Nét gạch phải đè lên chữ ở ít nhất tỉ lệ này số cột của nó (gạch ngang dài "——", dòng kẻ để điền không tính).
NET_DE_CHU = 0.3
# Một nét chữ mang nhãn của nét gạch khi nét gạch phủ ít nhất nửa bề ngang của nó; riêng gạch ngang còn phải xuyên
# qua (có nét ngay sát hai bên), vì nét gạch dừng ở giữa chữ có thể nối liền nét ngang của chữ (như chữ "4").
NET_PHU_CHU = 0.5
SAT_BEN = 4
# Nét chữ thấp hơn tỉ lệ này của chữ x (dấu chấm, nét đứt của đường nối comment, dấu neo) không quyết định nhãn.
CHU_THAP_NHAT = 0.4
# Vạch dọc mảnh (dấu neo comment, con trỏ sửa): nét dọc liền gần hết chiều cao chỉ dày tối đa VACH_MANH điểm, hoặc cả
# nhóm mực chỉ rộng tối đa VACH_HEP điểm; nét chữ ở 300 dpi dày 4–5 điểm, có chân serif thì rộng hơn nữa.
VACH_MANH = 2
VACH_CAO = 0.9
VACH_HEP = 4
DOAN_TOI_THIEU_CAO_X = 0.5
DAU_CACH_CAO_X = 0.35


@dataclass(frozen=True)
class DoanVung:
    x0: int
    x1: int
    nhan: str | None  # xóa | thêm | sửa | None (chữ thường)
    cach_truoc: bool = False  # có dấu cách giữa đoạn này và đoạn trước


def tim_redline(anh_vung: Image.Image) -> list[DoanVung]:
    """Chia ảnh một hộp chữ thành các đoạn liên tiếp phủ hết bề ngang, mỗi đoạn kèm nhãn redline."""
    x = np.asarray(anh_vung.convert("RGB")).astype(np.int16)
    cao, rong = x.shape[:2]
    do_sang = x @ np.array([0.299, 0.587, 0.114])
    muc = do_sang < NGUONG_MUC

    tren, duoi = _than_chu(muc & ~_dai_ngang(muc, NET_TOI_THIEU_CAO_HOP * cao))
    if tren is None:
        return [DoanVung(0, rong, None)]
    cao_x = duoi - tren + 1
    net = _dai_ngang(muc, NET_TOI_THIEU_CAO_X * cao_x)
    chu = muc & ~net
    net &= _de_len_chu(net, chu, tren, duoi)
    vi_tri = (np.arange(cao) - tren) / cao_x
    gach_ngang = (net & ((vi_tri >= GACH_NGANG[0]) & (vi_tri <= GACH_NGANG[1]))[:, None]).any(0)
    net_chan = net & (vi_tri >= GACH_CHAN_TU)[:, None]
    gach_chan = net_chan.any(0)

    # Mỗi chữ (các mảnh mực chồng nhau theo chiều ngang, sau khi bỏ nét gạch) mang một nhãn.
    nhan_cot: list = [False] * rong  # False: cột không có chữ
    for trai, phai, tr, du, diem in _cac_chu(chu, tren, duoi):
        if du - tr < CHU_THAP_NHAT * cao_x:
            continue  # dấu chấm, nét đứt của đường nối comment, dấu neo
        o = (slice(tr, du), slice(trai, phai))
        if (phai - trai <= VACH_HEP and du - tr >= cao_x) or (
            0 < (_doan_doc_dai_nhat(diem) >= VACH_CAO * (du - tr)).sum() <= VACH_MANH
        ):
            continue  # vạch dọc mảnh
        if _xuyen_qua(gach_ngang, trai, phai):
            n = "xóa"
        elif _la_mau(x[o][diem], do_sang[o][diem]):
            co_chan = gach_chan[trai:phai].mean() >= NET_PHU_CHU
            n = "thêm" if co_chan and _net_mau(x, net_chan, trai, phai) else "sửa"
        else:
            n = None
        nhan_cot[trai:phai] = [n] * (phai - trai)
    return _gom_doan(nhan_cot, DOAN_TOI_THIEU_CAO_X * cao_x, DAU_CACH_CAO_X * cao_x)


def _cac_chu(chu: np.ndarray, tren: int, duoi: int) -> list[tuple[int, int, int, int, np.ndarray]]:
    """Gom mảnh mực thành chữ: (trái, phải, trên, dưới, mặt nạ điểm trong khung đó).

    Bỏ mảnh không chạm thân chữ (chữ của dòng trên/dưới lọt vào hộp); mảnh chồng nhau quá nửa bề ngang là cùng một chữ
    (chữ bị nét gạch cắt đôi)."""
    so_nhan, nhan_diem, thong_ke, _ = cv2.connectedComponentsWithStats(chu.astype(np.uint8), connectivity=8)
    manh = sorted(
        (int(t[0]), int(t[0] + t[2]), int(t[1]), int(t[1] + t[3]), i)
        for i, t in enumerate(thong_ke[1:], start=1)
        if t[1] <= duoi and t[1] + t[3] > tren
    )
    nhom: list[list] = []
    for trai, phai, tr, du, i in manh:
        if nhom:
            n = nhom[-1]
            if min(phai, n[1]) - max(trai, n[0]) >= 0.5 * min(phai - trai, n[1] - n[0]):
                n[0], n[1], n[2], n[3] = min(n[0], trai), max(n[1], phai), min(n[2], tr), max(n[3], du)
                n[4].append(i)
                continue
        nhom.append([trai, phai, tr, du, [i]])
    return [(a, b, c, d, np.isin(nhan_diem[c:d, a:b], i)) for a, b, c, d, i in nhom]


def _doan_doc_dai_nhat(diem: np.ndarray) -> np.ndarray:
    """Độ dài đoạn mực liền dài nhất của từng cột."""
    dai = np.zeros(diem.shape[1], dtype=int)
    hien_tai = np.zeros(diem.shape[1], dtype=int)
    for hang in diem:
        hien_tai = np.where(hang, hien_tai + 1, 0)
        dai = np.maximum(dai, hien_tai)
    return dai


def _xuyen_qua(co_net: np.ndarray, x0: int, x1: int) -> bool:
    trai = co_net[max(0, x0 - SAT_BEN) : x0]
    phai = co_net[x1 : x1 + SAT_BEN]
    return bool(
        co_net[x0:x1].mean() >= NET_PHU_CHU and (trai.any() or x0 == 0) and (phai.any() or x1 == len(co_net))
    )


def _la_mau(diem: np.ndarray, do_sang: np.ndarray) -> bool:
    loi = diem[do_sang <= do_sang.min() + 25].mean(0)
    return bool(loi.min() > NGUONG_DEN_ANH or loi.max() - loi.min() > LECH_MAU)


def _net_mau(x: np.ndarray, net: np.ndarray, x0: int, x1: int) -> bool:
    """Nét gạch chân dưới đoạn [x0, x1) có màu (gạch chân đen là định dạng thường, không phải redline)."""
    o = net[:, x0:x1]
    return bool(o.any()) and _la_mau(x[:, x0:x1][o], x[:, x0:x1][o] @ np.array([0.299, 0.587, 0.114]))


def _dai_ngang(muc: np.ndarray, do_dai: float) -> np.ndarray:
    """Các điểm thuộc dải mực ngang liên tục dài ít nhất `do_dai` điểm."""
    ra = np.zeros_like(muc)
    for y in range(muc.shape[0]):
        hang = np.concatenate(([0], muc[y].astype(np.int8), [0]))
        canh = np.flatnonzero(np.diff(hang))
        for a, b in zip(canh[::2], canh[1::2]):
            if b - a >= do_dai:
                ra[y, a:b] = True
    return ra


def _than_chu(chu: np.ndarray) -> tuple[int | None, int | None]:
    """Dải hàng của thân chữ x (các hàng dày mực nhất), không tính nét gạch."""
    hang = chu.sum(1)
    if hang.max(initial=0) == 0:
        return None, None
    day = np.flatnonzero(hang >= TY_LE_HANG_THAN_CHU * hang.max())
    return int(day[0]), int(day[-1])


def _de_len_chu(net: np.ndarray, chu: np.ndarray, tren: int, duoi: int) -> np.ndarray:
    """Giữ các nét gạch đè lên chữ: đủ nhiều cột của nét có chữ trong thân chữ."""
    co_chu = chu[tren : duoi + 1].any(0)
    giu = np.zeros_like(net)
    for y in np.flatnonzero(net.any(1)):
        hang = np.concatenate(([0], net[y].astype(np.int8), [0]))
        canh = np.flatnonzero(np.diff(hang))
        for a, b in zip(canh[::2], canh[1::2]):
            if co_chu[a:b].mean() >= NET_DE_CHU:
                giu[y, a:b] = True
    return giu


def _gom_doan(nhan_cot: list, toi_thieu: float, dau_cach: float) -> list[DoanVung]:
    rong = len(nhan_cot)
    co_chu = [c for c in range(rong) if nhan_cot[c] is not False]
    if not co_chu:
        return [DoanVung(0, rong, None)]
    # Cột trống: hai bên cùng nhãn thì theo nhãn đó, khác thì chia đôi khoảng trống. Ghi lại độ rộng khoảng trống
    # ở ranh giới để biết hai đoạn có cách nhau một dấu cách không.
    nhan = list(nhan_cot)
    trong_truoc = {}
    for c in range(co_chu[0]):
        nhan[c] = nhan_cot[co_chu[0]]
    for a, b in zip(co_chu, co_chu[1:]):
        giua = (a + b + 1) // 2
        for c in range(a + 1, b):
            nhan[c] = nhan_cot[a] if c < giua else nhan_cot[b]
        if nhan_cot[a] != nhan_cot[b]:
            trong_truoc[giua] = b - a - 1
    for c in range(co_chu[-1] + 1, rong):
        nhan[c] = nhan_cot[co_chu[-1]]

    doan: list[list] = []
    for c, n in enumerate(nhan):
        if doan and doan[-1][2] == n:
            doan[-1][1] = c + 1
        else:
            doan.append([c, c + 1, n])
    # Đoạn quá hẹp (nhiễu) nhập vào đoạn rộng hơn bên cạnh.
    while len(doan) > 1:
        hep = min(range(len(doan)), key=lambda i: doan[i][1] - doan[i][0])
        if doan[hep][1] - doan[hep][0] >= toi_thieu:
            break
        ben = [i for i in (hep - 1, hep + 1) if 0 <= i < len(doan)]
        j = max(ben, key=lambda i: doan[i][1] - doan[i][0])
        doan[j][0], doan[j][1] = min(doan[j][0], doan[hep][0]), max(doan[j][1], doan[hep][1])
        del doan[hep]
        i = 0
        while i < len(doan) - 1:
            if doan[i][2] == doan[i + 1][2]:
                doan[i][1] = doan[i + 1][1]
                del doan[i + 1]
            else:
                i += 1
    return [DoanVung(a, b, n, trong_truoc.get(a, 0) >= dau_cach) for a, b, n in doan]
