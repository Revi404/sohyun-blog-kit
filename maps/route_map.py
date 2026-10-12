"""OSM 바탕(z10 타일 스티치) 위에 소현 스타일 코스 경로를 그린다."""
import math, sys
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
K = "/home/claude/sohyun-blog-kit/fonts/Pretendard-"
f = lambda w, s: ImageFont.truetype(K + w + ".otf", s)
Z, TX0, TY0 = 10, 882, 409
def px(lat, lon):
    n = 2 ** Z
    x = (lon + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return (x - TX0) * 256, (y - TY0) * 256
base = Image.open(sys.argv[1]).convert("RGB")
# 부드러운 톤: 채도·대비 낮추고 종이색 살짝 덮기
base = ImageEnhance.Color(base).enhance(0.55)
base = Image.blend(base, Image.new("RGB", base.size, (244, 242, 233)), 0.28)
stops = [("후쿠오카(하카타)", 33.590, 130.420, "1·3일차 시내"),
         ("다자이후", 33.519, 130.535, "2일차 버스투어"),
         ("유후인", 33.265, 131.355, "2일차 버스투어"),
         ("벳푸", 33.284, 131.491, "2일차 버스투어")]
pts = [px(a, b) for _, a, b, _ in stops]
# 크롭 영역
xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
pad_x, pad_y = 170, 190
L, R = min(xs) - pad_x, max(xs) + pad_x
T, B = min(ys) - pad_y - 60, max(ys) + pad_y
im = base.crop((int(L), int(T), int(R), int(B)))
pts = [(x - L, y - T) for x, y in pts]
S = 3
big = im.resize((im.width * S, im.height * S), Image.LANCZOS)
d = ImageDraw.Draw(big)
ACC, DEEP, CORAL, INK, WHITE = (30, 145, 80), (12, 82, 48), (224, 86, 59), (22, 21, 15), (255, 255, 255)
P = [(x * S, y * S) for x, y in pts]
# 경로(점선): 하카타→다자이후→유후인→벳푸→하카타(복귀)
route = [0, 1, 2, 3, 0]
def dashed(a, b, col, w, dash=26, gap=16):
    (x1, y1), (x2, y2) = a, b
    L_ = math.hypot(x2 - x1, y2 - y1); ux, uy = (x2 - x1) / L_, (y2 - y1) / L_
    t = 0
    while t < L_:
        e = min(t + dash, L_)
        d.line([(x1 + ux * t, y1 + uy * t), (x1 + ux * e, y1 + uy * e)], fill=col, width=w)
        t += dash + gap
for i in range(len(route) - 1):
    a, b = P[route[i]], P[route[i + 1]]
    if route[i + 1] == 0:
        # 복귀 경로는 아래로 살짝 우회해 겹치지 않게
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 150 * S)
        dashed(a, mid, CORAL, 6 * S); dashed(mid, b, CORAL, 6 * S)
    else:
        dashed(a, b, DEEP, 7 * S)
# 마커
nf, lf, sf = f("ExtraBold", 26 * S), f("Bold", 30 * S), f("Medium", 21 * S)
offsets = {0: (1, -1), 1: (-1, 1), 2: (-1, 1), 3: (-1, -1)}
for i, ((x, y), (name, _, _, sub)) in enumerate(zip(P, stops)):
    r = 26 * S
    d.ellipse((x - r - 5 * S, y - r - 5 * S, x + r + 5 * S, y + r + 5 * S), fill=WHITE)
    d.ellipse((x - r, y - r, x + r, y + r), fill=ACC if i else CORAL)
    d.text((x, y + S), str(i + 1), font=nf, fill=WHITE, anchor="mm")
    ox, oy = offsets[i]
    tw = max(d.textlength(name, font=lf), d.textlength(sub, font=sf))
    bx = x + ox * (r + 18 * S) - (tw + 40 * S if ox < 0 else 0)
    by = y + oy * (r + 8 * S) - (92 * S if oy < 0 else 0)
    d.rounded_rectangle((bx, by, bx + tw + 40 * S, by + 92 * S), radius=18 * S, fill=WHITE, outline=(217, 215, 206), width=2 * S)
    d.text((bx + 20 * S, by + 16 * S), name, font=lf, fill=INK)
    d.text((bx + 20 * S, by + 56 * S), sub, font=sf, fill=(89, 87, 80))
im = big.resize(im.size, Image.LANCZOS)
# 상단 타이틀 바 + 하단 출처
W = im.width
out = Image.new("RGB", (W, im.height + 150), (244, 242, 233))
out.paste(im, (0, 110))
d2 = ImageDraw.Draw(out)
d2.text((36, 30), "후쿠오카 2박3일 코스 한눈에 보기", font=f("ExtraBold", 40), fill=INK)
d2.text((36, im.height + 122), "지도 © OpenStreetMap contributors · 버스투어 방문 순서는 상품마다 달라요 · 소현생정", font=f("Medium", 18), fill=(89, 87, 80))
lx = W - 36
for label, col in [("복귀", CORAL), ("버스투어", DEEP)]:
    tw = d2.textlength(label, font=f("Medium", 20))
    d2.text((lx - tw, 44), label, font=f("Medium", 20), fill=INK); lx -= tw + 10
    d2.line([(lx - 40, 56), (lx, 56)], fill=col, width=6); lx -= 64
out.save(sys.argv[2], quality=92)
print(out.size)
