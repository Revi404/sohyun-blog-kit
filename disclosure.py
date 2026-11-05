#!/usr/bin/env python3
"""
협찬·광고 고지(공정위 경제적 이해관계 표시) 이미지 생성기 — 블로그 본문 맨 위에 넣는 가로 배너
사용법 (이미지 한 장 = 문구 한 줄이 기본):
  python3 disclosure.py --list                                              # 문구 목록·출처 보기
  python3 disclosure.py --preset review --brand 아르페 --out disclosure/out/20261105_아르페.png
  python3 disclosure.py --preset shoppingconnect --out ...
  python3 disclosure.py --text "캠페인 가이드 지정 문구 원문" --out ...         # 가이드 문구가 있으면 이걸로
옵션:
  --josa 로|으로 : 브랜드가 영문·숫자로 끝나 '으로/로'를 자동으로 못 고를 때 지정
  --text-line    : 이미지 대체텍스트로 쓸 문구만 출력(이미지 안 만듦)
문구는 disclosure/presets.json 에서 고친다. 필요: pip install pillow
"""
import argparse, json, re, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
PRESETS = json.loads((HERE / "disclosure/presets.json").read_text(encoding="utf-8"))
_F = {}
def font(weight, size):
    if (weight, size) not in _F:
        _F[(weight, size)] = ImageFont.truetype(str(HERE / f"fonts/Pretendard-{weight}.otf"), size)
    return _F[(weight, size)]

# 소현생정 디자인 토큰 (thumbnail.py와 같음)
PAPER, PAPER2, CARD = (244, 242, 233), (251, 250, 244), (255, 255, 255)
INK, INK_SOFT = (22, 21, 15), (89, 87, 80)
ACCENT_DEEP, HIGHLIGHT, CORAL = (12, 82, 48), (205, 238, 92), (224, 86, 59)
LINE = (217, 215, 206)

W, PAD, SS = 1080, 16, 2
BADGE_COLOR = {"광고": CORAL, "협찬": ACCENT_DEEP}
MARK_ON, MARK_OFF = "\x01", "\x02"

# 영문·숫자로 끝나는 브랜드(읽는 소리 기준). 확실한 것만 자동, 나머지(k·t·p 등)는 --josa 로 지정
_NUM_BATCHIM = {"0": "o", "1": "ㄹ", "3": "o", "6": "o", "7": "ㄹ", "8": "ㄹ", "2": None, "4": None, "5": None, "9": None}

def _en_batchim(w):
    w = w.lower()
    if w.endswith(("ng", "m", "n")):
        return "o"
    if w.endswith("l"):
        return "ㄹ"
    if w[-1] in "aeiouy" or w.endswith(("le", "re")):
        return None
    return "?"

def batchim(word):
    """마지막 글자의 받침: None=없음, 'ㄹ'=ㄹ받침, 'o'=그 밖의 받침, '?'=판단 불가"""
    w = re.sub(r"[\s\W_]+$", "", word)
    if not w:
        return "?"
    c = w[-1]
    if "가" <= c <= "힣":
        jong = (ord(c) - 0xAC00) % 28
        return None if jong == 0 else ("ㄹ" if jong == 8 else "o")
    if c.isdigit():
        return _NUM_BATCHIM[c]
    if c.isascii() and c.isalpha():
        return _en_batchim(w)
    return "?"

def ro(word, override=None):
    if override:
        return override
    b = batchim(word)
    if b == "?":
        sys.exit(f"'{word}' 뒤에 '로/으로' 중 무엇을 쓸지 모르겠습니다. --josa 로 또는 --josa 으로 를 붙여 주세요.")
    return "으로" if b == "o" else "로"

def platform_phrase(p):
    if not p:
        return ""
    return f"{p}{'을' if batchim(p) in ('o', 'ㄹ') else '를'} 통해 "

def fill(text, brand, platform, josa):
    if "{brand}" in text and not brand:
        sys.exit("이 문구에는 브랜드명이 필요합니다: --brand 브랜드명")
    text = text.replace("{platform}", platform_phrase(platform))
    text = text.replace("{ro}", ro(brand, josa) if brand else "")
    return text.replace("{brand}", f"{MARK_ON}{brand}{MARK_OFF}" if brand else "")

def plain(s):
    return s.replace(MARK_ON, "").replace(MARK_OFF, "")


def wrap(d, text, f, maxw):
    """띄어쓰기 단위 줄바꿈. 강조 표시(MARK)는 단어 안에 그대로 둔다."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = f"{cur} {word}" if cur else word
        if d.textlength(plain(trial), font=f) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur); cur = word
    if cur:
        lines.append(cur)
    # 강조가 줄을 넘어가면 각 줄에서 다시 열고 닫는다
    out, on = [], False
    for ln in lines:
        s = (MARK_ON if on else "") + ln
        on = s.rfind(MARK_ON) > s.rfind(MARK_OFF)
        out.append(s + (MARK_OFF if on else ""))
    return out

def draw_line(d, x, y, line, f, color, size):
    """강조 구간은 형광펜(아래쪽 45%)을 칠한 뒤 글자를 쓴다."""
    parts = re.split(f"({MARK_ON}.*?{MARK_OFF})", line)
    cx = x
    for p in parts:
        if not p:
            continue
        t = plain(p)
        w = d.textlength(t, font=f)
        if p.startswith(MARK_ON):
            d.rectangle([cx - 4 * SS, y + size * 0.55, cx + w + 4 * SS, y + size * 1.12], fill=HIGHLIGHT)
        d.text((cx, y), t, font=f, fill=color)
        cx += w


def sentences(text):
    """'...다.' 로 끝나는 문장마다 끊는다(한 문장 = 한 줄)."""
    return [x.strip() for x in re.split(r"(?<=[다요]\.)\s+", text) if x.strip()]


def render(blocks, extras, out):
    """blocks: [(badge, text)], extras: [str]
    2026-11-05 대표 지시: 딱지·강조 없이 얇은 작은 글씨, 한 문장은 한 줄(넘치면 글씨를 줄여 맞춘다)"""
    s = SS
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    lines = []
    for t in [plain(t) for _, t in blocks] + [plain(e) for e in extras]:
        lines += sentences(t)
    x0 = (PAD + 40) * s
    mark_w = 36
    inner = (W - PAD * 2 - 40 - 28 - mark_w - 20) * s
    size = 26
    while size > 18 and max(probe.textlength(l, font=font("Medium", size * s)) for l in lines) > inner:
        size -= 1
    if max(probe.textlength(l, font=font("Medium", size * s)) for l in lines) > inner:
        sys.exit("문장이 너무 길어 한 줄에 안 들어갑니다(18px 기준). 문구를 줄이거나 두 문장으로 나눠 주세요.")
    f = font("Medium", size * s)
    lh = int(size * 1.65 * s)

    card_top = PAD * s
    card_bot = card_top + 24 * s + len(lines) * lh + 20 * s
    H = card_bot + PAD * s

    img = Image.new("RGB", (W * s, H), CARD)   # 네이버 블로그 흰 바탕에 맞춤
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([PAD * s, card_top, (W - PAD) * s, card_bot], radius=20 * s, fill=ACCENT_DEEP)
    d.rounded_rectangle([PAD * s + 6 * s, card_top, (W - PAD) * s, card_bot], radius=19 * s, fill=PAPER2, outline=LINE, width=2 * s)

    y = card_top + 24 * s
    for ln in lines:
        d.text((x0, y), ln, font=f, fill=INK_SOFT)
        y += lh
    mark = HERE / "brand/mark.png"
    if mark.exists():
        m = Image.open(mark).convert("RGBA")
        mh = 34 * s
        m = m.resize((int(m.width * mh / m.height), mh), Image.LANCZOS)
        img.paste(m, ((W - PAD - 28) * s - m.width, (card_top + card_bot) // 2 - mh // 2), m)

    img = img.resize((W, H // s), Image.LANCZOS)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, optimize=True)
    return img.size


def main():
    ap = argparse.ArgumentParser(description="협찬·광고 고지 이미지 생성")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--preset", action="append", default=[])
    ap.add_argument("--brand", default="")
    ap.add_argument("--platform", default="")
    ap.add_argument("--josa", choices=["로", "으로"])
    ap.add_argument("--badge", choices=["광고", "협찬"])
    ap.add_argument("--text", help="직접 쓴 문구({brand}, {ro} 사용 가능)")
    ap.add_argument("--extra", action="append", default=[], help="캠페인 지정 문구(작은 글씨로 아래에)")
    ap.add_argument("--text-line", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()

    if a.list:
        for k, v in PRESETS.items():
            if not k.startswith("_"):
                print(f"{k:16} {v['label']}  (출처: {v['source']})\n{'':16} {v['text']}")
        return
    blocks = []
    for p in a.preset:
        if p not in PRESETS or p.startswith("_"):
            sys.exit(f"없는 문구: {p} (목록: python3 disclosure.py --list)")
        blocks.append(("", fill(PRESETS[p]["text"], a.brand, a.platform, a.josa)))
    if a.text:
        blocks.append((a.badge or "", fill(a.text, a.brand, a.platform, a.josa)))
    if not blocks:
        sys.exit("--preset 또는 --text 가 필요합니다.")
    extras = [fill(e, a.brand, a.platform, a.josa) for e in a.extra]

    line = " ".join(plain(t) for _, t in blocks)
    if a.text_line:
        print(line); return
    if not a.out:
        sys.exit("--out 경로가 필요합니다.")
    w, h = render(blocks, extras, a.out)
    print(f"저장: {a.out} ({w}x{h})")
    print(f"대체텍스트: {line}")

if __name__ == "__main__":
    main()
