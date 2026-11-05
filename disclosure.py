#!/usr/bin/env python3
"""
협찬·광고 고지(공정위 경제적 이해관계 표시) 이미지 생성기 — 블로그 본문 맨 위에 넣는 가로 배너
사용법:
  python3 disclosure.py --list                                   # 문구 목록 보기
  python3 disclosure.py --preset brandconnect --brand 아르페 --out disclosure/out/20261105_아르페.png
  python3 disclosure.py --preset experience --brand 수수햄부대찌개 --platform 레뷰 --out ...
  python3 disclosure.py --preset brandconnect-fee --preset coupang --out ...   # 여러 문구 겹치기
  python3 disclosure.py --preset brandconnect --brand 아르페 \
      --extra "본 콘텐츠는 아르페 제품을 체험하고 솔직하게 작성한 후기입니다." --out ...  # 캠페인 지정 문구 추가
  python3 disclosure.py --badge 협찬 --text "직접 쓴 문구 ({brand} 강조 가능)" --brand OO --out ...
옵션:
  --josa 로|으로 : 브랜드가 영문·숫자로 끝나 '으로/로'를 자동으로 못 고를 때 지정
  --text-line    : 본문 첫 줄에 같이 넣을 텍스트 문구만 출력(이미지 안 만듦)
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


def render(blocks, extras, out):
    """blocks: [(badge, text)], extras: [str]"""
    s = SS
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    inner = (W - PAD * 2 - 54 - 44) * s
    fb, fm, fbadge, fcap = font("Bold", 34 * s), font("Medium", 27 * s), font("ExtraBold", 26 * s), font("Medium", 22 * s)
    lh_main, lh_extra = int(34 * 1.55 * s), int(27 * 1.6 * s)

    badges = []
    for b, _ in blocks:
        if b not in badges:
            badges.append(b)
    main_lines = [wrap(probe, t, fb, inner) for _, t in blocks]
    extra_lines = [wrap(probe, t, fm, inner) for t in extras]

    card_top = PAD * s
    y = card_top + 40 * s + 50 * s + 26 * s   # 위 여백 + 딱지 줄 + 간격
    body_h = sum(len(ls) * lh_main for ls in main_lines) + (len(main_lines) - 1) * 14 * s
    if extra_lines:
        body_h += 22 * s + 2 * s + 22 * s + sum(len(ls) * lh_extra for ls in extra_lines)
    card_bot = y + body_h + 34 * s
    H = card_bot + PAD * s

    img = Image.new("RGB", (W * s, H), CARD)   # 네이버 블로그 흰 바탕에 맞춤
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([PAD * s, card_top, (W - PAD) * s, card_bot], radius=28 * s, fill=ACCENT_DEEP)
    d.rounded_rectangle([PAD * s + 10 * s, card_top, (W - PAD) * s, card_bot], radius=26 * s, fill=PAPER2, outline=LINE, width=2 * s)

    # 딱지 줄
    x0 = (PAD + 54) * s
    bx, by = x0, card_top + 40 * s
    for b in badges:
        tw = d.textlength(f"[{b}]", font=fbadge)
        d.rounded_rectangle([bx, by, bx + tw + 36 * s, by + 50 * s], radius=25 * s, fill=BADGE_COLOR.get(b, CORAL))
        d.text((bx + 18 * s, by + 25 * s), f"[{b}]", font=fbadge, fill=CARD, anchor="lm")
        bx += tw + 36 * s + 12 * s
    d.text((bx + 6 * s, by + 25 * s), "경제적 이해관계 표시", font=fcap, fill=INK_SOFT, anchor="lm")
    mark = HERE / "brand/mark.png"
    if mark.exists():
        m = Image.open(mark).convert("RGBA")
        mh = 46 * s
        m = m.resize((int(m.width * mh / m.height), mh), Image.LANCZOS)
        img.paste(m, ((W - PAD - 40) * s - m.width, by + 2 * s), m)

    for i, ls in enumerate(main_lines):
        if i:
            y += 14 * s
        for ln in ls:
            draw_line(d, x0, y, ln, fb, INK, 34 * s)
            y += lh_main
    if extra_lines:
        y += 22 * s
        d.line([x0, y, (W - PAD - 44) * s, y], fill=LINE, width=2 * s)
        y += 2 * s + 22 * s
        for ls in extra_lines:
            for ln in ls:
                draw_line(d, x0, y, ln, fm, INK_SOFT, 27 * s)
                y += lh_extra

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
                print(f"{k:18} [{v['badge']}] {v['label']}\n{'':18} {v['text']}")
        return
    blocks = []
    for p in a.preset:
        if p not in PRESETS or p.startswith("_"):
            sys.exit(f"없는 문구: {p} (목록: python3 disclosure.py --list)")
        blocks.append((PRESETS[p]["badge"], fill(PRESETS[p]["text"], a.brand, a.platform, a.josa)))
    if a.text:
        if not a.badge:
            sys.exit("--text 를 쓸 때는 --badge 광고|협찬 을 같이 지정하세요.")
        blocks.append((a.badge, fill(a.text, a.brand, a.platform, a.josa)))
    if not blocks:
        sys.exit("--preset 또는 --text 가 필요합니다.")
    extras = [fill(e, a.brand, a.platform, a.josa) for e in a.extra]

    badges = "/".join(dict.fromkeys(b for b, _ in blocks))
    line = f"[{badges}] " + " ".join(plain(t) for _, t in blocks)
    if a.text_line:
        print(line); return
    if not a.out:
        sys.exit("--out 경로가 필요합니다.")
    w, h = render(blocks, extras, a.out)
    print(f"저장: {a.out} ({w}x{h})")
    print(f"텍스트 병기용: {line}")

if __name__ == "__main__":
    main()
