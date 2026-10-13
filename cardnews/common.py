"""소현 카드뉴스·티어표 공통 모듈 (테마, 글꼴, 스티커 목록, 화면 맞춤, 영상 인코딩)

캔버스는 9:16(1080x1920)이고, 모든 내용은 가운데 3:4 영역(1080x1440, y=240~1680) 안에 넣는다.
인스타 프로필 그리드는 릴스를 3:4로 잘라 보여 주므로, 이 영역 밖에는 배경만 둔다.
"""
import json, html, random, subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FONTS = REPO / "fonts"
BRAND = REPO / "brand"
W, H, FPS = 1080, 1920, 30
SAFE_TOP, SAFE_BOTTOM = 240, 1680          # 3:4 안전 영역 (높이 1440)

THEMES = {
    "sohyun": dict(paper="#F4F2E9", ink="#16150F", soft_ink="#595750", accent="#1E9150", deep="#0C5230",
                   soft="#E6F1E2", hl="#CDEE5C", hl_ink="#16150F", coral="#E0563B", coral_soft="#FAE4DC",
                   line="#DEDBCF", brand="소현생정", sub="소비를 현명하게", handle="@sohyun_guide"),
    "richlab": dict(paper="#F1F3F6", ink="#111827", soft_ink="#4B5563", accent="#2457C5", deep="#0F2747",
                    soft="#E3EAF6", hl="#F5C542", hl_ink="#111827", coral="#E0563B", coral_soft="#FBE6DF",
                    line="#D6DCE5", brand="소현생정 리치랩", sub="소득을 현명하게", handle="@sohyun_richlab"),
}

def theme(name_or_dict):
    if isinstance(name_or_dict, dict):
        t = dict(THEMES[name_or_dict.get("base", "sohyun")]); t.update(name_or_dict); return t
    return dict(THEMES[name_or_dict or "sohyun"])

def css_vars(t):
    return ";".join(f"--{k}:{v}" for k, v in t.items() if k not in ("brand", "sub", "handle", "base"))

def font_css():
    F = FONTS.resolve().as_uri()
    return (f"@font-face{{font-family:P;src:url('{F}/Pretendard-Medium.otf');font-weight:500}}"
            f"@font-face{{font-family:P;src:url('{F}/Pretendard-Bold.otf');font-weight:700}}"
            f"@font-face{{font-family:P;src:url('{F}/Pretendard-ExtraBold.otf');font-weight:800}}"
            f"@font-face{{font-family:J;src:url('{F}/Jua-Regular.ttf')}}")

def e(s):
    """HTML 이스케이프. <b> <hl> <c> <small> <span> <br/> 표시만 살린다. 줄바꿈은 <br/>."""
    s = html.escape(str(s))
    for tg in ("b", "hl", "c", "br/", "small", "span", "em", "strong"):
        s = s.replace(f"&lt;{tg}&gt;", f"<{tg}>").replace(f"&lt;/{tg}&gt;", f"</{tg}>")
    return s.replace("\n", "<br/>")

def uri(p):
    return Path(p).resolve().as_uri()

# ------------------------------------------------------------------ 스티커 목록
_CAT = None
def catalog():
    global _CAT
    if _CAT is None:
        _CAT = json.loads((REPO / "stickers" / "catalog.json").read_text(encoding="utf-8"))
    return _CAT

def pick_sticker(spec, used=None, kinds=("full",)):
    """spec: "07_surprised" | {"id": ..} | {"emotion": "놀람"} | {"file": 로컬경로}.
    감정으로 고를 때는 같은 감정 후보 중 이번 콘텐츠에서 안 쓴 것, 최근 추가(added)된 것을 우선한다."""
    used = used if used is not None else set()
    if isinstance(spec, str):
        spec = {"id": spec}
    if spec.get("file"):
        return Path(spec["file"])
    items = catalog()["stickers"]
    if spec.get("id"):
        it = next((x for x in items if x["id"] == spec["id"]), None)
        if it is None:
            raise SystemExit(f"스티커 목록에 없음: {spec['id']} (stickers/catalog.json 확인)")
    else:
        emo = spec["emotion"]
        cand = [x for x in items if emo in x["emotions"] and x["kind"] in spec.get("kinds", kinds)]
        if not cand:
            raise SystemExit(f"감정 '{emo}' 스티커 없음. emotion_groups: {list(catalog()['emotion_groups'])}")
        fresh = [x for x in cand if x["id"] not in used] or cand
        # 처음 세트(2026-10-10) 이후 새로 등록한 스티커는 두 배로 자주 뽑히게 한다
        it = random.choice(fresh + [x for x in fresh if x.get("added", "") > "2026-10-10"])
    used.add(it["id"])
    return REPO / it["full"]

# ------------------------------------------------------------------ 화면 맞춤·점검
FIT_JS = """(sel) => {
  const box = document.querySelector(sel); if (!box) return {ok:true, zoom:1};
  const limit = box.dataset.limit ? +box.dataset.limit : null;
  const over = () => limit ? box.getBoundingClientRect().bottom > limit : box.scrollHeight > box.clientHeight + 1;
  let z = 1;
  while (over() && z > 0.70) { z = +(z - 0.03).toFixed(2); box.style.zoom = z; }
  return {ok: !over(), zoom: z};
}"""

SAFE_JS = """([top, bottom]) => {
  const bad = [];
  document.querySelectorAll('.safe-check, .safe-check *, .sticker').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) return;
    if (r.top < top - 1 || r.bottom > bottom + 1) bad.push((el.className || el.tagName) + ' ' + Math.round(r.top) + '~' + Math.round(r.bottom));
  });
  return bad.slice(0, 8);
}"""

def shoot(pages, out_pngs, size=(W, H), fit_sel=None, safe=True):
    """pages: HTML 파일 목록. 각 장을 PNG로 찍고, 넘침은 zoom으로 줄인 뒤 결과를 돌려준다."""
    from playwright.sync_api import sync_playwright
    report = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": size[0], "height": size[1]})
        for hp, pp in zip(pages, out_pngs):
            pg.goto(uri(hp)); pg.wait_for_timeout(300)
            fit = pg.evaluate(FIT_JS, fit_sel) if fit_sel else {"ok": True, "zoom": 1}
            bad = pg.evaluate(SAFE_JS, [SAFE_TOP, SAFE_BOTTOM]) if safe else []
            pg.screenshot(path=str(pp))
            report.append({"page": Path(pp).name, "fit_ok": fit["ok"], "zoom": fit["zoom"], "outside_3x4": bad})
        b.close()
    for r in report:
        flag = "" if r["fit_ok"] and not r["outside_3x4"] else "  ← 확인 필요"
        print(f"  {r['page']}: zoom {r['zoom']}, 넘침 {'없음' if r['fit_ok'] else '있음'}, 3:4 밖 {r['outside_3x4'] or '없음'}{flag}")
    return report

def grid_preview(png, out):
    """인스타 프로필 그리드처럼 3:4로 자른 미리보기."""
    from PIL import Image
    Image.open(png).crop((0, SAFE_TOP, W, SAFE_BOTTOM)).save(out)

# ------------------------------------------------------------------ 영상
def encode(pngs, durs, mp4, transition=0.3):
    """PNG 여러 장을 장마다 durs초로 이어 붙인다(슬라이드 전환, 무음 트랙 포함 — BGM은 앱에서)."""
    n = len(pngs); tr = transition if n > 1 else 0
    inp = []
    for pp, du in zip(pngs, durs):
        inp += ["-loop", "1", "-t", f"{du + tr:.2f}", "-i", str(pp)]
    total = sum(durs) + tr
    if n == 1:
        fc = f"[0:v]format=yuv420p,fps={FPS}[v]"
    else:
        parts, prev, off = [], "0:v", 0.0
        for i in range(1, n):
            off += durs[i - 1]
            parts.append(f"[{prev}][{i}:v]xfade=transition=slideleft:duration={tr}:offset={off:.2f}[x{i}]")
            prev = f"x{i}"
        parts.append(f"[{prev}]format=yuv420p,fps={FPS}[v]")
        fc = ";".join(parts)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *inp, "-f", "lavfi", "-t", f"{total:.2f}",
                    "-i", "anullsrc=r=48000:cl=stereo", "-filter_complex", fc, "-map", "[v]", "-map", f"{n}:a",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "128k",
                    "-t", f"{total:.2f}", "-movflags", "+faststart", str(mp4)], check=True)
    return total
