#!/usr/bin/env python3
"""소현 카드뉴스 릴스 (9:16 캔버스, 내용은 3:4 안전 영역 안)

  python3 cardreel.py render <slides.json> <출력폴더>

출력: <출력폴더>/png/01.png… (장표), <name>.mp4 (장당 dur초 + 0.3초 슬라이드 전환, 무음),
      <name>_grid.png (프로필 그리드 3:4 미리보기 = 첫 장), report.json (넘침·3:4 밖 점검),
      feed/<name>_NN.png (피드 캐러셀용 3:4 1080x1440 장표, 릴스 장표의 3:4 영역을 그대로 자른 것)

slides.json = {
  "name": "20261017_난방시작전체크", "theme": "sohyun" | "richlab",
  "label": "생활꿀팁 묶음",           # 상단 알약 (뒤에 쪽번호 자동)
  "dur": 3.0, "first": 3.5, "last": 4.0,
  "slides": [ {type, ...}, ... ]
}
type 별 필드 (문자열 안에서 <hl>형광펜</hl> <c>코랄</c> <b>강조</b> <small>작게</small>, 줄바꿈 \n)
  hook    kicker, title, size("m"|"s"), sub, photo | chips[]
  tip     num, title, hook, photo, ph(사진 높이), rows[[항목,내용]x3~4], box[fact|warn, 제목, 내용], source
  table   kicker, title, head[], rows[[...]|{"c":[...]} 강조행], right[열번호], box, note
  bars    kicker, title, fmt("{:,}만"), bars[[이름, 설명, 값, (1=강조)]], box, note
  photos  kicker, title, items[[사진, 제목, 설명] x3]
  steps   kicker, title, steps[[왼쪽칸, 제목, 설명]], box, note
  summary kicker, title, items[[라벨, 내용]], note
  outro   kicker, title, cta, cta_sub, note
공통: sticker = "07_surprised" | {"emotion": "놀람"} | {"id":..,"pos":"br"|"bl"|"tr","w":300} | {"file": 경로}
      (스티커는 stickers/catalog.json에서 고른다. pos: br 오른쪽 아래(기본) / bl / tr / mid 오른쪽 가운데)
사진 경로는 slides.json 기준 상대경로.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *  # noqa

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{width:1080px;height:1920px;background:var(--paper);font-family:P;color:var(--ink);position:relative;overflow:hidden;word-break:keep-all}
.blob{position:absolute;right:-220px;top:20px;width:700px;height:700px;border-radius:50%;background:var(--soft)}
.top{position:absolute;left:64px;right:64px;top:278px;display:flex;align-items:center;justify-content:space-between}
.brand{display:flex;align-items:center;gap:14px;font-weight:800;font-size:38px;letter-spacing:-1px}
.brand img{height:50px}
.brand small{font-weight:700;font-size:23px;color:var(--soft_ink);margin-left:4px}
.pill{background:var(--accent);color:#fff;font-weight:700;font-size:28px;padding:11px 26px;border-radius:40px;white-space:nowrap}
.pill span{opacity:.7;margin-left:12px}
.main{position:absolute;left:64px;right:64px;top:380px;height:1260px;display:flex;flex-direction:column}
.kicker{font-weight:700;font-size:42px;color:var(--soft_ink);letter-spacing:-1px;margin-bottom:20px}
.title{font-weight:800;font-size:118px;line-height:1.1;letter-spacing:-4px}
.title.m{font-size:90px;letter-spacing:-3px}
.title.s{font-size:72px;letter-spacing:-2.5px;line-height:1.15}
hl{background:linear-gradient(transparent 58%,var(--hl) 58%);color:var(--hl_ink);padding:0 4px}
c{color:var(--coral)}
b{color:var(--accent);font-weight:800}
.sub{font-family:J;font-size:56px;color:var(--deep);margin-top:28px}
.photo{border-radius:40px;overflow:hidden;background:var(--soft);position:relative;flex:none}
.photo img{width:100%;height:100%;object-fit:cover;display:block}
.num{display:inline-block;background:var(--deep);color:#fff;font-weight:800;font-size:36px;border-radius:14px;padding:8px 20px;margin-bottom:20px;align-self:flex-start}
.hook{font-family:J;font-size:52px;color:var(--coral);margin:14px 0 26px}
table{width:100%;border-collapse:separate;border-spacing:0;background:#fff;border-radius:32px;overflow:hidden;font-size:39px}
td,th{padding:23px 30px;border-bottom:2px solid var(--line);text-align:left;vertical-align:middle}
tr:last-child td{border-bottom:none}
th{background:var(--deep);color:#fff;font-weight:700;font-size:33px}
td small{display:block;font-size:27px;color:var(--soft_ink);font-weight:500;margin-top:4px}
td.k{font-weight:800;color:var(--deep);white-space:nowrap;width:1%}
td.r{text-align:right;font-weight:800;white-space:nowrap}
tr.me td{background:var(--soft)}
.box{border-radius:28px;padding:28px 34px;margin-top:28px;font-size:35px;line-height:1.45}
.box.fact{background:var(--soft);color:var(--deep)}
.box.warn{background:var(--coral_soft);color:#7A2414}
.box strong{font-weight:800;display:block;font-size:40px;margin-bottom:4px}
.src{font-size:27px;color:var(--soft_ink);margin-top:14px}
.sticker{position:absolute}
.bars{display:flex;flex-direction:column;gap:32px;margin-top:10px}
.bar{display:grid;grid-template-columns:400px 1fr;align-items:center;gap:20px;font-size:36px}
.bar .n{font-weight:700;line-height:1.2}
.bar .n small{display:block;font-size:27px;color:var(--soft_ink);font-weight:500}
.bar .t{height:80px;border-radius:14px;background:var(--line);position:relative}
.bar .t i{position:absolute;left:0;top:0;bottom:0;border-radius:14px;background:#A7B4C7}
.bar .t span{position:absolute;right:16px;top:50%;transform:translateY(-50%);font-weight:800}
.bar.me .t i{background:var(--coral)}
.bar.me .n{color:var(--coral);font-weight:800}
.grid3{display:grid;grid-template-rows:repeat(3,minmax(0,1fr));gap:22px;flex:1;min-height:0}
.prow{min-height:0;height:100%;display:grid;grid-template-columns:400px 1fr;gap:28px;align-items:center;background:#fff;border-radius:32px;overflow:hidden}
.prow img{width:400px;height:100%;min-height:0;object-fit:cover;display:block}
.prow h3{font-weight:800;font-size:46px;letter-spacing:-1.5px}
.prow p{font-size:32px;color:var(--soft_ink);margin-top:10px;line-height:1.4;padding-right:24px}
.steps{display:flex;flex-direction:column;gap:22px}
.step{display:grid;grid-template-columns:150px 1fr;background:#fff;border-radius:30px;overflow:hidden}
.step .d{background:var(--deep);color:#fff;font-weight:800;font-size:36px;display:flex;align-items:center;justify-content:center;text-align:center;line-height:1.2}
.step .x{padding:26px 30px;font-size:36px;line-height:1.4}
.step .x strong{display:block;font-weight:800;font-size:40px;margin-bottom:4px}
.sum{display:flex;flex-direction:column;gap:24px}
.sum div{background:#fff;border-radius:30px;padding:34px 36px;font-size:43px;line-height:1.4;display:flex;gap:22px;align-items:flex-start}
.sum div em{font-style:normal;background:var(--hl);color:var(--hl_ink);font-weight:800;border-radius:12px;padding:4px 16px;font-size:37px;flex:none;margin-top:2px}
.chips{display:flex;flex-wrap:wrap;gap:18px;margin-top:56px}
.chips span{background:#fff;border-radius:44px;padding:22px 40px;font-weight:800;font-size:46px}
.cta{margin-top:auto;background:var(--deep);border-radius:36px;color:#fff;padding:40px 44px}
.cta .a{font-weight:800;font-size:62px;letter-spacing:-1.5px;line-height:1.2}
.cta .a span{color:var(--hl)}
.cta .b{font-size:33px;opacity:.85;margin-top:14px;line-height:1.45}
.note{font-size:29px;color:var(--soft_ink);margin-top:18px;line-height:1.5}
"""

def frame(t, body, page, total, label):
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{font_css()}{CSS}</style></head>
<body style="{css_vars(t)}"><div class="blob"></div>
{body}
<div class="top safe-check"><div class="brand"><img src="{uri(BRAND / 'mark.png')}"/>{e(t['brand'])}<small>{e(t['sub'])}</small></div><div class="pill">{e(label)}<span>{page}/{total}</span></div></div>
</body></html>"""

POS = {"br": (None, 64, None, SAFE_BOTTOM), "bl": (64, None, None, SAFE_BOTTOM), "tr": (None, 60, SAFE_TOP + 120, None),
       "mid": (None, 80, 860, None)}   # mid = 오른쪽 가운데(마무리 장 CTA 위 빈 곳)

def sticker_html(spec, used, base):
    if not spec:
        return ""
    if isinstance(spec, dict) and spec.get("file"):
        spec = dict(spec, file=str((base / spec["file"]).resolve()))
    path = pick_sticker(spec, used)
    s = spec if isinstance(spec, dict) else {}
    w = s.get("w", 300)
    if "x" in s and "y" in s:
        st = f"left:{s['x']}px;top:{s['y']}px"
    else:
        l, r, tp, bt = POS[s.get("pos", "br")]
        st = ";".join(x for x in [f"left:{l}px" if l is not None else "", f"right:{r}px" if r is not None else "",
                                  f"top:{tp}px" if tp is not None else "", f"bottom:{H - bt + 48}px" if bt is not None else ""] if x)
    return f'<img class="sticker" src="{uri(path)}" style="width:{w}px;{st}"/>'

def box(s):
    if not s.get("box"):
        return ""
    kind, h, txt = s["box"]
    return f'<div class="box {kind}">{"<strong>" + e(h) + "</strong>" if h else ""}{e(txt)}</div>'

def head(s, cls="s", mb=34):
    return f'<div class="kicker">{e(s.get("kicker", ""))}</div><div class="title {cls}" style="margin-bottom:{mb}px">{e(s["title"])}</div>'

def r_hook(s, base):
    b = f'<div class="kicker">{e(s.get("kicker", ""))}</div><div class="title {s.get("size", "")}">{e(s["title"])}</div>'
    if s.get("sub"): b += f'<div class="sub">{e(s["sub"])}</div>'
    if s.get("photo"):
        b += f'<div class="photo" style="flex:1;min-height:0;margin-top:36px"><img src="{uri(base / s["photo"])}"/></div>'
    elif s.get("chips"):
        b += '<div class="chips">' + "".join(f"<span>{e(c)}</span>" for c in s["chips"]) + "</div>"
    return b

def r_tip(s, base):
    b = f'<div class="num">{e(s["num"])}</div><div class="title s">{e(s["title"])}</div>'
    if s.get("hook"): b += f'<div class="hook">{e(s["hook"])}</div>'
    if s.get("photo"):
        b += f'<div class="photo" style="height:{s.get("ph", 320)}px;margin-bottom:24px"><img src="{uri(base / s["photo"])}"/></div>'
    b += "<table>" + "".join(f'<tr><td class="k">{e(k)}</td><td>{e(v)}</td></tr>' for k, v in s["rows"]) + "</table>"
    b += box(s)
    if s.get("source"): b += f'<div class="src">출처: {e(s["source"])}</div>'
    return b

def r_table(s, base):
    b = head(s) + "<table>"
    if s.get("head"): b += "<tr>" + "".join(f"<th>{e(h)}</th>" for h in s["head"]) + "</tr>"
    for row in s["rows"]:
        me = isinstance(row, dict); cells = row["c"] if me else row
        b += f'<tr class="{"me" if me else ""}">' + "".join(
            f'<td class="{"k" if i == 0 else ("r" if i in s.get("right", []) else "")}">{e(c)}</td>' for i, c in enumerate(cells)) + "</tr>"
    b += "</table>" + box(s)
    if s.get("note"): b += f'<div class="note">{e(s["note"])}</div>'
    return b

def r_bars(s, base):
    mx = max(v for _, _, v, *_ in s["bars"])
    b = head(s, mb=40) + '<div class="bars">'
    for name, sub, v, *flag in s["bars"]:
        b += f'<div class="bar {"me" if flag and flag[0] else ""}"><div class="n">{e(name)}<small>{e(sub)}</small></div><div class="t"><i style="width:{v / mx * 100:.1f}%"></i><span>{e(s.get("fmt", "{:,}").format(v))}</span></div></div>'
    b += "</div>" + box(s)
    if s.get("note"): b += f'<div class="note">{e(s["note"])}</div>'
    return b

def r_photos(s, base):
    b = head(s) + '<div class="grid3">'
    for p, h3, txt in s["items"]:
        b += f'<div class="prow"><img src="{uri(base / p)}"/><div><h3>{e(h3)}</h3><p>{e(txt)}</p></div></div>'
    return b + "</div>"

def r_steps(s, base):
    b = head(s) + '<div class="steps">'
    for d, h3, txt in s["steps"]:
        b += f'<div class="step"><div class="d">{e(d)}</div><div class="x"><strong>{e(h3)}</strong>{e(txt)}</div></div>'
    b += "</div>" + box(s)
    if s.get("note"): b += f'<div class="note">{e(s["note"])}</div>'
    return b

def r_summary(s, base):
    b = head(s, "m", 38) + '<div class="sum">' + "".join(f"<div><em>{e(k)}</em><span>{e(v)}</span></div>" for k, v in s["items"]) + "</div>"
    if s.get("note"): b += f'<div class="note">{e(s["note"])}</div>'
    return b

def r_outro(s, base):
    b = f'<div class="kicker">{e(s.get("kicker", ""))}</div><div class="title m">{e(s["title"])}</div>'
    b += f'<div class="cta"><div class="a">{e(s["cta"])}</div><div class="b">{e(s.get("cta_sub", ""))}</div></div>'
    if s.get("note"): b += f'<div class="note">{e(s["note"])}</div>'
    return b

R = dict(hook=r_hook, tip=r_tip, table=r_table, bars=r_bars, photos=r_photos, steps=r_steps, summary=r_summary, outro=r_outro)

def render(cfg_path, out):
    cfg = json.loads(Path(cfg_path).read_text(encoding="utf-8"))
    base = Path(cfg_path).resolve().parent
    out = Path(out).resolve(); (out / "png").mkdir(parents=True, exist_ok=True)
    t = theme(cfg.get("theme", "sohyun"))
    n = len(cfg["slides"]); used = set(); pages, pngs = [], []
    for i, s in enumerate(cfg["slides"], 1):
        body = f'<div class="main safe-check">{R[s["type"]](s, base)}</div>' + sticker_html(s.get("sticker"), used, base)
        hp = out / "png" / f"{i:02d}.html"; hp.write_text(frame(t, body, i, n, cfg["label"]), encoding="utf-8")
        pages.append(hp); pngs.append(out / "png" / f"{i:02d}.png")
    print("장표 점검:")
    rep = shoot(pages, pngs, fit_sel=".main")
    d = cfg.get("dur", 3.0)
    durs = [cfg.get("first", d + 0.5)] + [d] * (n - 2) + [cfg.get("last", d + 1.0)] if n > 1 else [cfg.get("first", 8.0)]
    mp4 = out / f"{cfg['name']}.mp4"
    total = encode(pngs, durs, mp4)
    grid_preview(pngs[0], out / f"{cfg['name']}_grid.png")
    (out / "feed").mkdir(exist_ok=True)
    for i, pp in enumerate(pngs, 1):
        grid_preview(pp, out / "feed" / f"{cfg['name']}_{i:02d}.png")
    (out / "report.json").write_text(json.dumps({"slides": rep, "stickers": sorted(used), "seconds": round(total, 1)}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{mp4}  {n}장  {total:.1f}초  스티커 {sorted(used)}")

if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "render":
        render(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
