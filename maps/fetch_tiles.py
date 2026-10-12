"""(PC에서 실행) OSM z10 타일을 받아 한 장으로 붙인다. 컨테이너는 OSM에 접속 못 함.
사용: python3 fetch_tiles.py <남lat> <서lon> <북lat> <동lon> <출력.png> [zoom]
출력 첫 줄: Z TX0 TY0  → route_map.py stops.json 의 z, tx0, ty0 에 그대로 넣는다.
타일 정책: User-Agent 명시, 0.3초 간격, 한 번에 30장 이하. 지도에는 © OpenStreetMap contributors 표기.
"""
import io, math, sys, time, urllib.request
from PIL import Image
s, w, n, e, out = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
z = int(sys.argv[6]) if len(sys.argv) > 6 else 10
def t(lat, lon):
    k = 2 ** z
    return (lon + 180) / 360 * k, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * k
x0, y0 = t(n, w); x1, y1 = t(s, e)
tx0, ty0, tx1, ty1 = int(x0), int(y0), int(x1), int(y1)
cnt = (tx1 - tx0 + 1) * (ty1 - ty0 + 1)
if cnt > 30: sys.exit(f"타일 {cnt}장: 범위를 줄이거나 zoom을 낮추세요")
im = Image.new("RGB", ((tx1 - tx0 + 1) * 256, (ty1 - ty0 + 1) * 256))
for tx in range(tx0, tx1 + 1):
    for ty in range(ty0, ty1 + 1):
        req = urllib.request.Request(f"https://tile.openstreetmap.org/{z}/{tx}/{ty}.png", headers={"User-Agent": "sohyun-blog-map/1.0 (revi404@naver.com)"})
        im.paste(Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=30).read())).convert("RGB"), ((tx - tx0) * 256, (ty - ty0) * 256))
        time.sleep(0.3)
with open(out, "wb") as f:
    im.save(f, "PNG")
print(z, tx0, ty0)
