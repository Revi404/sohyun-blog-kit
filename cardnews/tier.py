#!/usr/bin/env python3
"""공통 티어표 (주제 무관) — 3:4 피드 이미지 + 9:16 릴스

  python3 tier.py render <tier.json> <출력폴더>

출력: <name>_feed.png (1080x1440, 3:4 — 피드 게시물/캐러셀용)
      <name>_reel.png (1080x1920, 3:4 이미지를 가운데 둔 릴스 한 장)
      <name>.mp4 (릴스, 기본 8초, 무음 — BGM은 앱에서), report.json

tier.json = {
  "name": "20261016_후쿠오카버스투어_티어표", "theme": "sohyun" | "richlab" | {"base":"sohyun", "accent":"#..."},
  "label": "여행 티어표",                    # 오른쪽 위 알약. <b>강조</b> 가능
  "kicker": "첫 후쿠오카라면 저장!", "title": "후쿠오카 근교\n<hl>버스투어 티어표</hl>", "sub": "한 줄 설명",
  "sticker": {"emotion": "추천"},            # 제목 오른쪽 (stickers/catalog.json)
  "layout": "card" | "metric" | "chip",
  "columns": 5,                              # card 레이아웃 한 줄 칸 수 (항목 2개 이하인 티어는 가로형 큰 카드)
  "tiers": [ {"key":"S", "label":"검증 끝\n바로 담기", "range":"리뷰 3,000+", "color":"#E0563B", "fg":"#fff",
              "items":[...], "empty":"이번엔 해당 없음"} , ...],
  "criteria": "<b>티어 기준</b> ...",       # 아래 진한 상자 (줄바꿈 \n). 기준·출처·조회일은 반드시 넣는다
  "seconds": 25
}
items:
  card   {"img": 경로, "name", "sub", "price", "meta"}           (사진 카드: 상품·장소·제품)
         {"tip": "고르는 팁", "text": "..."}                     (빈 칸 채우는 팁 상자, 2칸 차지)
  metric {"name", "sub", "big": "77", "unit": "%", "bar": [값, 최대, 기준선], "left", "right", "memo", "memo_kind": "warn"|"note"}
                                                                 (수치 비교: 단지·금리·요금 등)
  chip   {"name", "sub"}                                         (글자만: 키워드·장소명)
티어 색 기본값(색 미지정 시): S 코랄/금색, A 초록/파랑, B 겨자/연파랑, C 회색, D 연회색
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *  # noqa

DEFAULT_COLORS = {
    "sohyun": ["#E0563B", "#1E9150", "#C9A227", "#8A8F86", "#B7B9B1"],
    "richlab": ["#F5C542", "#2457C5", "#5B7BC4", "#7C8798", "#A9B1BE"],
}
DEFAULT_FG = {"#F5C542": "#111827"}

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1440px;background:var(--paper);font-family:P;color:var(--ink);position:relative;overflow:hidden;word-break:keep-all}
.blob{position:absolute;right:-180px;top:-260px;width:620px;height:620px;border-radius:50%;background:var(--soft)}
.hd{position:absolute;left:48px;right:48px;top:42px;display:flex;justify-content:space-between;align-items:center}
.brand{display:flex;align-items:center;gap:12px;font-weight:800;font-size:31px}
.brand img{height:42px}
.brand small{font-size:20px;color:var(--soft_ink);font-weight:700}
.pill{background:var(--deep);color:#fff;font-weight:700;font-size:24px;padding:9px 22px;border-radius:30px}
.pill b{color:var(--hl)}
.ti{position:absolute;left:48px;right:260px;top:108px}
.k{font-family:J;font-size:32px;color:var(--coral)}
h1{font-weight:800;font-size:66px;letter-spacing:-3px;line-height:1.06;margin-top:6px}
hl{background:linear-gradient(transparent 58%,var(--hl) 58%);color:var(--hl_ink);padding:0 4px}
c{color:var(--coral)} b{color:var(--accent)}
.sub{font-size:24px;color:var(--soft_ink);font-weight:700;margin-top:12px}
.sub b{color:var(--deep)}
.st{position:absolute;right:48px;top:112px;width:200px;clip-path:inset(0 0 0 8%)}
.tb{position:absolute;left:36px;right:36px;top:var(--tbtop);display:flex;flex-direction:column;gap:12px;transform-origin:top center}
.row{display:flex;background:#fff;border-radius:26px;overflow:hidden;box-shadow:0 4px 0 var(--line)}
.tag{width:132px;flex:none;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;padding:10px 4px}
.L{font-weight:800;font-size:72px;line-height:1}
.l{font-weight:800;font-size:19px;text-align:center;line-height:1.25}
.rg{font-size:15px;font-weight:700;opacity:.85;margin-top:2px;text-align:center}
.none{font-size:22px;color:var(--soft_ink);font-weight:700;padding:20px 22px;align-self:center}
/* card */
.cards{flex:1;display:grid;grid-template-columns:repeat(var(--cols),1fr);gap:10px;padding:14px;min-width:0}
.cards.two{grid-template-columns:1fr 1fr}
.card{display:flex;flex-direction:column;min-width:0}
.ph{border-radius:14px;overflow:hidden;aspect-ratio:1/1;background:var(--soft)}
.ph img{width:100%;height:100%;object-fit:cover;display:block}
.nm{font-weight:800;font-size:21px;margin-top:8px;letter-spacing:-.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cs{font-size:16px;color:var(--soft_ink);margin-top:2px;line-height:1.3;max-height:42px;overflow:hidden}
.pr{display:flex;flex-direction:column;margin-top:4px;font-size:17px}
.pr strong{font-weight:800;font-size:21px;color:var(--deep)}
.pr span{font-weight:700}
.card.big{flex-direction:row;gap:16px;align-items:center}
.card.big .ph{width:170px;flex:none}
.card.big .info{display:flex;flex-direction:column;min-width:0}
.card.big .nm{font-size:30px;margin-top:0} .card.big .cs{font-size:20px;max-height:none}
.card.big .pr{font-size:21px} .card.big .pr strong{font-size:30px}
.tip{grid-column:span 2;background:var(--coral_soft);border-radius:16px;padding:20px 22px;color:#7A2414}
.tip .tt{font-family:J;font-size:28px;margin-bottom:8px} .tip p{font-size:21px;line-height:1.5;font-weight:700}
/* metric */
.mets{flex:1;display:flex;flex-direction:column;padding:6px 22px;min-width:0}
.met{padding:11px 0;border-bottom:2px dashed var(--line)}
.met:last-child{border-bottom:none}
.mt{display:flex;justify-content:space-between;align-items:flex-end;gap:16px}
.mn{font-weight:800;font-size:27px;letter-spacing:-1px}
.ms{font-size:18px;color:var(--soft_ink);margin-top:3px;font-weight:500}
.bv{font-weight:800;font-size:46px;color:var(--deep);line-height:1;letter-spacing:-1.5px;white-space:nowrap}
.bv small{font-size:24px}
.mb{position:relative;height:12px;background:var(--soft);border-radius:8px;margin-top:8px}
.mb i{position:absolute;left:0;top:0;bottom:0;border-radius:8px;background:var(--accent)}
.mb u{position:absolute;top:-5px;bottom:-5px;width:3px;background:var(--coral);border-radius:2px}
.mlr{display:flex;justify-content:space-between;font-size:17px;color:var(--soft_ink);margin-top:5px;gap:12px}
.mlr strong{color:var(--ink);font-weight:800}
.memo{font-size:16px;font-weight:700;margin-top:4px;color:var(--soft_ink)}
.memo.warn{color:#B4412A}
/* chip */
.chips{flex:1;display:flex;flex-wrap:wrap;gap:10px;padding:16px;align-content:center}
.chip{background:var(--soft);border-radius:18px;padding:12px 18px}
.chip .cn{font-weight:800;font-size:24px} .chip .cs2{font-size:16px;color:var(--soft_ink);margin-top:2px}
.ft{position:absolute;left:36px;right:36px;bottom:30px;background:var(--deep);color:#E8EAE4;border-radius:20px;padding:15px 24px;font-size:17px;line-height:1.55}
.ft b{color:var(--hl);font-weight:800}
"""

def tag_colors(t, tiers, theme_name):
    pal = DEFAULT_COLORS.get(theme_name if isinstance(theme_name, str) else theme_name.get("base", "sohyun"), DEFAULT_COLORS["sohyun"])
    out = []
    for i, tr in enumerate(tiers):
        bg = tr.get("color") or pal[min(i, len(pal) - 1)]
        out.append((bg, tr.get("fg") or DEFAULT_FG.get(bg, "#fff")))
    return out

def card(it, base, big=False):
    if "tip" in it:
        return f'<div class="tip"><div class="tt">{e(it["tip"])}</div><p>{e(it["text"])}</p></div>'
    ph = f'<div class="ph"><img src="{uri(base / it["img"])}"/></div>' if it.get("img") else '<div class="ph"></div>'
    info = (f'<div class="nm">{e(it["name"])}</div><div class="cs">{e(it.get("sub", ""))}</div>'
            f'<div class="pr">{"<strong>" + e(it["price"]) + "</strong>" if it.get("price") else ""}<span>{e(it.get("meta", ""))}</span></div>')
    return f'<div class="card big">{ph}<div class="info">{info}</div></div>' if big else f'<div class="card">{ph}{info}</div>'

def metric(it):
    bar = ""
    if it.get("bar"):
        v, mx, *mk = it["bar"]
        bar = f'<div class="mb"><i style="width:{min(v, mx) / mx * 100:.1f}%"></i>' + (f'<u style="left:{mk[0] / mx * 100:.1f}%"></u>' if mk else "") + "</div>"
    lr = f'<div class="mlr"><span>{e(it.get("left", ""))}</span><span>{e(it.get("right", ""))}</span></div>' if it.get("left") or it.get("right") else ""
    memo = f'<div class="memo {it.get("memo_kind", "note")}">{e(it["memo"])}</div>' if it.get("memo") else ""
    return (f'<div class="met"><div class="mt"><div><div class="mn">{e(it["name"])}</div><div class="ms">{e(it.get("sub", ""))}</div></div>'
            f'<div class="bv">{e(it.get("big", ""))}<small>{e(it.get("unit", ""))}</small></div></div>{bar}{lr}{memo}</div>')

def build(cfg, base):
    t = theme(cfg.get("theme", "sohyun"))
    lay = cfg.get("layout", "card")
    cols = tag_colors(t, cfg["tiers"], cfg.get("theme", "sohyun"))
    rows = ""
    for tr, (bg, fg) in zip(cfg["tiers"], cols):
        items = tr.get("items", [])
        if not items:
            body = f'<div class="none">{e(tr.get("empty", "이번엔 해당 없음"))}</div>'
        elif lay == "card":
            big = len([x for x in items if "tip" not in x]) <= 2 and len(items) <= 2
            body = f'<div class="cards {"two" if big else ""}">{"".join(card(x, base, big) for x in items)}</div>'
        elif lay == "metric":
            body = f'<div class="mets">{"".join(metric(x) for x in items)}</div>'
        else:
            body = '<div class="chips">' + "".join(f'<div class="chip"><div class="cn">{e(x["name"])}</div>{"<div class=cs2>" + e(x["sub"]) + "</div>" if x.get("sub") else ""}</div>' for x in items) + "</div>"
        rows += (f'<div class="row"><div class="tag" style="background:{bg};color:{fg}"><div class="L">{e(tr["key"])}</div>'
                 f'<div class="l">{e(tr.get("label", ""))}</div>{"<div class=rg>" + e(tr["range"]) + "</div>" if tr.get("range") else ""}</div>{body}</div>')
    used = set()
    st = f'<img class="st" src="{uri(pick_sticker(cfg["sticker"], used))}"/>' if cfg.get("sticker") else ""
    tbtop = cfg.get("table_top", 330)
    html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{font_css()}{CSS}</style></head>
<body style="{css_vars(t)};--cols:{cfg.get('columns', 5)};--tbtop:{tbtop}px"><div class="blob"></div>
<div class="hd"><div class="brand"><img src="{uri(BRAND / 'mark.png')}"/>{e(t['brand'])}<small>{e(t['sub'])}</small></div><div class="pill">{e(cfg.get('label', '티어표'))}</div></div>
<div class="ti"><div class="k">{e(cfg.get('kicker', ''))}</div><h1>{e(cfg['title'])}</h1>{"<div class=sub>" + e(cfg['sub']) + "</div>" if cfg.get('sub') else ""}</div>
{st}
<div class="tb" id="tb">{rows}</div>
<div class="ft" id="ft">{e(cfg.get('criteria', ''))}</div>
</body></html>"""
    return html, used, t

FIT_TB = """() => {
  const tb = document.getElementById('tb'), ft = document.getElementById('ft');
  const limit = ft.getBoundingClientRect().top - 14;
  let z = 1; tb.style.zoom = 1;
  while (tb.getBoundingClientRect().bottom > limit && z > 0.70) { z = +(z - 0.02).toFixed(2); tb.style.zoom = z; }
  const r = tb.getBoundingClientRect();
  // 남는 공간이 크면 표를 가운데로
  const gap = limit - r.bottom; if (gap > 30) tb.style.top = (parseFloat(getComputedStyle(tb).top) + gap / 2 / z) + 'px';
  return {zoom: z, ok: tb.getBoundingClientRect().bottom <= limit + 1};
}"""

def render(cfg_path, out):
    cfg = json.loads(Path(cfg_path).read_text(encoding="utf-8"))
    base = Path(cfg_path).resolve().parent
    out = Path(out).resolve(); out.mkdir(parents=True, exist_ok=True)
    html, used, t = build(cfg, base)
    hp = out / f"{cfg['name']}_feed.html"; hp.write_text(html, encoding="utf-8")
    feed = out / f"{cfg['name']}_feed.png"
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1440})
        pg.goto(uri(hp)); pg.wait_for_timeout(400)
        fit = pg.evaluate(FIT_TB); pg.screenshot(path=str(feed))
        # 릴스: 9:16 캔버스 가운데(3:4 영역)에 피드 이미지
        rh = out / f"{cfg['name']}_reel.html"
        rh.write_text(f'<!doctype html><html><body style="margin:0;width:1080px;height:1920px;background:{t["paper"]}">'
                      f'<img src="{uri(feed)}" style="position:absolute;left:0;top:{SAFE_TOP}px;width:1080px;height:1440px"/></body></html>', encoding="utf-8")
        pg.set_viewport_size({"width": 1080, "height": 1920}); pg.goto(uri(rh)); pg.wait_for_timeout(200)
        reel = out / f"{cfg['name']}_reel.png"; pg.screenshot(path=str(reel)); b.close()
    secs = cfg.get("seconds", 25)
    encode([reel], [secs], out / f"{cfg['name']}.mp4")
    rep = {"zoom": fit["zoom"], "fits": fit["ok"], "stickers": sorted(used), "seconds": secs}
    (out / "report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{feed}\n{out / (cfg['name'] + '.mp4')}  표 zoom {fit['zoom']} {'OK' if fit['ok'] else '← 넘침: 항목·글자를 줄일 것'}")

if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "render":
        render(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
