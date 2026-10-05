#!/usr/bin/env python3
"""
소현생정 블로그 대표 이미지(썸네일) 생성기 — 1080x1350, 소현생정 디자인 시스템(새싹 팔레트)
사용법:
  python3 thumbnail.py --tag "[소현생정] 리빙포인트" --right "생활 꿀팁" \
    --kicker "자취생이라면 꼭 알아둘" --line1 "전기요금 절약법" --line2 "한 달 30% 줄이는 법" \
    --note "누진 구간 · 대기전력 · 계절별 설정" [--mark "절약법"] [--photo 사진.jpg] --out thumbs/파일.jpg
레이아웃 (디자인 시스템 ReelsThumbnail):
  상단 820px 사진(없으면 새싹 그래픽) + 좌상단 태그 칩 / 하단 종이색 패널에 키커 · 1줄(ink) · 2줄(coral) · 포인트 칩
  --mark : 1줄에서 라임 형광펜을 칠할 단어 (기본: 1줄의 마지막 단어, "-" 이면 없음)
  프로필 그리드 3:4 크롭(좌우 약 34px)을 고려해 글자는 좌우 64px 안쪽에만 둔다.
필요: pip install pillow
"""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

HERE = Path(__file__).parent
_F = {}
def font(weight, size):
    key = (weight, size)
    if key not in _F:
        _F[key] = ImageFont.truetype(str(HERE / f"fonts/Pretendard-{weight}.otf"), size)
    return _F[key]

# 디자인 토큰 (소현생정 디자인 시스템 tokens.json)
PAPER       = (244, 242, 233)   # paper  #F4F2E9
PAPER2      = (251, 250, 244)   # paper-2
CARD        = (255, 255, 255)
INK         = (22, 21, 15)      # #16150F
INK_SOFT    = (89, 87, 80)      # #595750
ACCENT      = (30, 145, 80)     # #1E9150
ACCENT_DEEP = (12, 82, 48)      # #0C5230
ACCENT_SOFT = (230, 241, 226)   # #E6F1E2
HIGHLIGHT   = (205, 238, 92)    # #CDEE5C
ON_ACCENT   = (251, 255, 246)
CORAL       = (224, 86, 59)     # #E0563B
AMBER       = (255, 194, 77)
LINE        = (217, 215, 206)   # line rgba(22,21,15,.12) on paper

W, H = 1080, 1350
PHOTO_H = 820
PANEL_Y = 764
GUT = 64
SS = 3  # 도형 안티앨리어싱용 슈퍼샘플링 배율


def fit(d, text, maxw, size, weight, floor=48):
    while size > floor and d.textlength(text, font=font(weight, size)) > maxw:
        size -= 2
    return font(weight, size)


def _bez(p0, p1, p2, p3, n=24):
    out = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        out.append((u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
                    u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]))
    return out


def sprout(size, stem=ACCENT_DEEP, leaf1=ACCENT, leaf2=ACCENT_DEEP):
    """새싹 마크 (viewBox 32) → RGBA 이미지"""
    s = size * SS / 32
    im = Image.new("RGBA", (size * SS, size * SS), (0, 0, 0, 0)); g = ImageDraw.Draw(im)
    P = lambda pts: [(x * s, y * s) for x, y in pts]
    l1 = _bez((16, 17), (14.8, 11.5), (10.6, 9), (6, 9.4)) + _bez((6, 9.4), (5.4, 14.4), (9.6, 18), (16, 17))
    l2 = _bez((16, 14), (16.8, 9.4), (20.6, 7.2), (24.6, 7.6)) + _bez((24.6, 7.6), (25, 11.8), (21.4, 15), (16, 14))
    w = 2.4 * s
    g.rounded_rectangle((16 * s - w / 2, 15 * s - w / 2, 16 * s + w / 2, 30 * s + w / 2), radius=w / 2, fill=stem)
    g.polygon(P(l1), fill=leaf1)
    g.polygon(P(l2), fill=leaf2)
    return im.resize((size, size), Image.LANCZOS)


def chip(im, xy, text, size, bg, fg, border=None):
    """알약형 칩. 반환: 칩 너비"""
    d = ImageDraw.Draw(im)
    f = font("Bold", size)
    tw = d.textlength(text, font=f)
    ph, pv = round(size * 1.0), round(size * 0.55)
    w, h = round(tw + ph * 2), round(size + pv * 2)
    x, y = xy
    layer = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0)); g = ImageDraw.Draw(layer)
    g.rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), radius=h * SS // 2, fill=border or bg)
    if border:
        b = 2 * SS
        g.rounded_rectangle((b, b, w * SS - 1 - b, h * SS - 1 - b), radius=h * SS // 2 - b, fill=bg)
    layer = layer.resize((w, h), Image.LANCZOS)
    im.paste(layer, (x, y), layer)
    d.text((x + w / 2, y + h / 2), text, font=f, fill=fg, anchor="mm")
    return w


def placeholder(pw, ph):
    """사진이 없을 때: accent-soft 바탕 + 블롭 + 새싹 마크"""
    p = Image.new("RGB", (pw, ph), ACCENT_SOFT)
    big = Image.new("L", (pw * SS // 2, ph * SS // 2), 0); g = ImageDraw.Draw(big)
    k = SS / 2
    g.ellipse((pw * 0.42 * k, -ph * 0.25 * k, pw * 1.15 * k, ph * 0.95 * k), fill=255)
    m = big.resize((pw, ph), Image.LANCZOS)
    p.paste(Image.new("RGB", (pw, ph), PAPER2), (0, 0), m)
    sp = sprout(300)
    p.paste(sp, (int(pw * 0.62), int(ph * 0.18)), sp)
    dots = Image.new("RGBA", (pw * SS // 2, ph * SS // 2), (0, 0, 0, 0)); g = ImageDraw.Draw(dots)
    for cx, cy, r, c in [(0.12, 0.62, 0.16, ACCENT_DEEP), (0.30, 0.78, 0.06, CORAL), (0.40, 0.60, 0.04, AMBER)]:
        g.ellipse(((cx - r) * pw * k, (cy * ph - r * pw) * k, (cx + r) * pw * k, (cy * ph + r * pw) * k), fill=c)
    dots = dots.resize((pw, ph), Image.LANCZOS)
    p.paste(dots, (0, 0), dots)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True); ap.add_argument("--right", default="")
    ap.add_argument("--kicker", default=""); ap.add_argument("--line1", required=True); ap.add_argument("--line2", default="")
    ap.add_argument("--note", default=""); ap.add_argument("--mark", default=None)
    ap.add_argument("--photo"); ap.add_argument("--out", required=True)
    a = ap.parse_args()

    im = Image.new("RGB", (W, H), PAPER)
    # 1) 사진 영역
    if a.photo:
        p = ImageOps.fit(ImageOps.exif_transpose(Image.open(a.photo)).convert("RGB"), (W, PHOTO_H), Image.LANCZOS)
        p = p.filter(ImageFilter.UnsharpMask(radius=2, percent=50, threshold=2))
    else:
        p = placeholder(W, PHOTO_H)
    im.paste(p, (0, 0))

    # 2) 하단 종이색 패널 (상단 모서리 56px 라운드) + 약한 그림자
    sh = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sh).rounded_rectangle((0, PANEL_Y - 6, W, H + 60), radius=56, fill=70)
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    im.paste(Image.new("RGB", (W, H), (16, 28, 18)), (0, 0), sh.point(lambda v: v * 0.35))
    pm = Image.new("L", (W * SS, (H - PANEL_Y + 60) * SS), 0)
    ImageDraw.Draw(pm).rounded_rectangle((0, 0, W * SS, (H - PANEL_Y + 60) * SS), radius=56 * SS, fill=255)
    pm = pm.resize((W, H - PANEL_Y + 60), Image.LANCZOS)
    im.paste(Image.new("RGB", pm.size, PAPER), (0, PANEL_Y), pm)

    # 3) 좌상단 칩: 태그(딥그린) + 분류(흰색)
    x = GUT
    x += chip(im, (x, GUT), a.tag, 28, ACCENT_DEEP, ON_ACCENT) + 12
    if a.right:
        chip(im, (x, GUT), a.right, 28, CARD, INK)

    d = ImageDraw.Draw(im)
    maxw = W - GUT * 2
    y = PANEL_Y + 76
    # 4) 키커
    if a.kicker:
        f = fit(d, a.kicker, maxw, 40, "Bold", 30)
        d.text((GUT, y), a.kicker, font=f, fill=INK_SOFT, anchor="lt")
        y += 40 + 30
    # 5) 1줄 (ink) + 형광펜
    f1 = fit(d, a.line1, maxw, 104, "ExtraBold")
    sz = f1.size
    mark = a.mark if a.mark is not None else a.line1.split()[-1]
    if mark and mark != "-" and mark in a.line1:
        i = a.line1.rfind(mark)
        x0 = GUT + d.textlength(a.line1[:i], font=f1)
        x1 = x0 + d.textlength(mark, font=f1)
        d.rectangle((x0 - sz * 0.04, y + sz * 0.50, x1 + sz * 0.04, y + sz * 0.90), fill=HIGHLIGHT)
    d.text((GUT, y), a.line1, font=f1, fill=INK, anchor="lt")
    y += round(sz * 1.12)
    # 6) 2줄 (coral, 결론·숫자)
    if a.line2:
        f2 = fit(d, a.line2, maxw, sz, "ExtraBold")
        d.text((GUT, y), a.line2, font=f2, fill=CORAL, anchor="lt")
        y += round(f2.size * 1.12)
    # 7) 포인트 칩 (note 를 ' · ' 로 나눔)
    if a.note:
        items = [t.strip() for t in a.note.replace("·", "|").split("|") if t.strip()]
        size = 28
        def total(s):
            return sum(d.textlength(t, font=font("Bold", s)) + s * 2 + 12 for t in items) - 12
        while size > 22 and total(size) > maxw:
            size -= 1
        cx, cy = GUT, max(y + 28, 1150)
        for t in items:
            cx += chip(im, (cx, cy), t, size, PAPER, INK, border=LINE) + 12
    # 8) 푸터: 새싹 + 소현생정
    sp = sprout(34)
    im.paste(sp, (GUT - 4, H - 70), sp)
    d.text((GUT + 36, H - 53), "소현생정 · 소비를 현명하게", font=font("Bold", 24), fill=INK_SOFT, anchor="lm")

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    im.save(a.out, quality=95); print(a.out)


if __name__ == "__main__":
    main()
