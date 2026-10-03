#!/usr/bin/env python3
"""
소현생정 블로그 대표 이미지(썸네일) 생성기 — 1080x1350, 소현 양식
사용법:
  python3 thumbnail.py --tag "[소현생정] 리빙포인트" --right "생활 꿀팁" \
    --kicker "자취생이라면 꼭 알아둘" --line1 "전기요금" --line2 "한 달 30% 줄이는 법" \
    --note "누진 구간 · 대기전력 · 계절별 설정" [--photo 사진.jpg] --out thumbs/파일.jpg
  --photo 가 없으면 소현 베이지·코랄 그래픽 패널로 채움
필요: pip install pillow
"""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

HERE = Path(__file__).parent
B = lambda s: ImageFont.truetype(str(HERE / "fonts/IBMPlexSansKR-Bold.ttf"), s)
R = lambda s: ImageFont.truetype(str(HERE / "fonts/IBMPlexSansKR-Regular.ttf"), s)
WHITE, BLACK, CORAL, GRAY, LIGHT, BEIGE, SAGE = (255,255,255),(17,17,17),(255,107,91),(110,110,110),(240,240,240),(213,199,186),(122,160,150)
W, H = 1080, 1350

def fit(d, text, maxw, size, font):
    while size > 40 and d.textlength(text, font=font(size)) > maxw: size -= 2
    return font(size)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True); ap.add_argument("--right", default="")
    ap.add_argument("--kicker", default=""); ap.add_argument("--line1", required=True); ap.add_argument("--line2", default="")
    ap.add_argument("--note", default=""); ap.add_argument("--photo"); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    im = Image.new("RGB", (W, H), WHITE); d = ImageDraw.Draw(im)
    top = 90
    d.text((80, top), a.tag, font=B(34), fill=CORAL)
    if a.right: d.text((W - 80, top), a.right, font=B(34), fill=BLACK, anchor="ra")
    d.line([(80, top + 70), (W - 80, top + 70)], fill=BLACK, width=4)
    if a.kicker: d.text((80, 215), a.kicker, font=fit(d, a.kicker, W - 160, 40, R), fill=GRAY)
    d.text((80, 275), a.line1, font=fit(d, a.line1, W - 160, 92, B), fill=BLACK)
    if a.line2: d.text((80, 385), a.line2, font=fit(d, a.line2, W - 160, 92, B), fill=CORAL)
    pw, ph, px, py = W - 160, 520, 80, 540
    if a.photo:
        p = ImageOps.fit(ImageOps.exif_transpose(Image.open(a.photo)).convert("RGB"), (pw, ph), Image.LANCZOS)
        p = p.filter(ImageFilter.UnsharpMask(radius=2, percent=50, threshold=2))
    else:
        p = Image.new("RGB", (pw, ph), BEIGE); g = ImageDraw.Draw(p)
        g.rectangle((pw * 0.32, 0, pw * 0.68, ph), fill=(245, 245, 245))
        r = ph * 0.22; cx, cy = pw / 2, ph / 2
        g.ellipse((cx - r, cy - r, cx + r, cy + r), fill=SAGE)
        for i in range(5):
            x = pw * 0.08 + i * 46
            g.ellipse((x, ph - 90, x + 30, ph - 60), fill=CORAL if i < 4 else LIGHT)
        g.text((pw - 40, 50), "소현생정", font=B(40), fill=WHITE, anchor="ra")
    m = Image.new("L", (pw, ph), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, pw, ph), radius=28, fill=255)
    im.paste(p, (px, py), m)
    if a.note:
        d.rounded_rectangle((80, 1100, W - 80, 1200), radius=28, fill=LIGHT)
        d.text((W // 2, 1150), a.note, font=fit(d, a.note, W - 220, 36, R), fill=BLACK, anchor="mm")
    d.text((W // 2, 1290), "소현 · 소비를 현명하게", font=B(30), fill=BLACK, anchor="mm")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    im.save(a.out, quality=95); print(a.out)

if __name__ == "__main__":
    main()
