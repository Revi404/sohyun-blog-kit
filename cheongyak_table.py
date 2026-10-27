"""청약노트 주택형별 공급금액 요약표 이미지 생성 (v3 공식 규격).

입력:
  --rows   모집공고문에서 추출한 동·층별 CSV
           (주택형,층구분,세대수,대지비,건축비,부가세,공급금액계,계약금1차,계약금2차,중도금회차별,잔금)
  --area   주택형별 공급면적 JSON, 예: {"84A":110.3043,...}
  --name   단지 약칭 (예: 트리븐센텀 1단지)
  --date   모집공고일 YYYY.MM.DD
  --out    출력 PNG 경로
"""
import argparse, json, csv
from pathlib import Path
from collections import OrderedDict
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent

def get_font(bold=False, size=24):
    """OS 무관 폰트 로더"""
    font_name = "Pretendard-Bold.otf" if bold else "Pretendard-Medium.otf"
    font_path = HERE / "fonts" / font_name
    if font_path.exists():
        return ImageFont.truetype(str(font_path), size)
    linux_f = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    if Path(linux_f).exists():
        return ImageFont.truetype(linux_f, size)
    win_f = "C:/Windows/Fonts/malgunbd.ttf" if bold else "C:/Windows/Fonts/malgun.ttf"
    if Path(win_f).exists():
        return ImageFont.truetype(win_f, size)
    return ImageFont.load_default()

GREEN = "#0E4D33"       # 딥그린 헤더
CORAL = "#E2583B"       # 코랄 라인
BG = "#F4F1EA"          # 배경 paper
ALT = "#E7EFE3"         # 교대 행 연녹색
INK = "#151515"         # 본문 텍스트
GRAY = "#5B5B5B"        # 주석 텍스트


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True)
    ap.add_argument("--area", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    with open(a.rows, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        data = list(reader)

    grouped = OrderedDict()
    for row in data:
        t = row["주택형"].strip()
        cnt = int(row["세대수"])
        price = float(row["공급금액계"])
        vat = float(row.get("부가세", 0))

        if t not in grouped:
            grouped[t] = {"prices": [], "counts": [], "vats": []}
        grouped[t]["prices"].append(price)
        grouped[t]["counts"].append(cnt)
        grouped[t]["vats"].append(vat)

    sup = json.loads(a.area)
    rows = []
    vat_types = []
    for t, item in grouped.items():
        prices = item["prices"]
        counts = item["counts"]
        tot_cnt = sum(counts)
        avg = sum(p * c for p, c in zip(prices, counts)) / tot_cnt if tot_cnt > 0 else 0
        min_p = min(prices)
        max_p = max(prices)

        if any(v > 0 for v in item["vats"]):
            vat_types.append(t)

        # 공급금액 범위: 6.5억~6.9억
        range_str = f"{min_p / 1e8:.1f}억~{max_p / 1e8:.1f}억"
        # 가중평균: 6.6억
        avg_str = f"{avg / 1e8:.1f}억"

        # 공급 평당가: @22,600 (천원 단위 100천원 반올림)
        if t in sup and sup[t] > 0:
            pyeong = sup[t] / 3.305785
            # 천원 단위: round(avg / 1000 / pyeong, -2)
            pyeong_cheon = round((avg / 1000.0) / pyeong, -2)
            per_str = f"@{int(pyeong_cheon):,}"
        else:
            per_str = "-"

        rows.append([t, f"{tot_cnt}", range_str, avg_str, per_str])

    # 렌더링 규격 (v3 공식 레이아웃)
    W, pad, rh = 1080, 56, 64
    cw = [120, 120, 260, 220, 220]
    x0 = (W - sum(cw)) // 2
    H = pad + 130 + rh * (len(rows) + 1) + 150
    im = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(im)

    # 상단 뱃지 & 타이틀
    dr.rounded_rectangle([x0, pad, x0 + 250, pad + 44], radius=22, fill=GREEN)
    dr.text((x0 + 24, pad + 6), "[소현생정] 청약노트", font=get_font(bold=True, size=22), fill="white")
    dr.text((x0, pad + 62), f"{a.name} 주택형별 공급금액", font=get_font(bold=True, size=36), fill=INK)

    y = pad + 130
    fh, fb = get_font(bold=True, size=24), get_font(bold=False, size=26)

    def draw_row(vals, y_pos, font_obj, fill_color, bg_color):
        dr.rectangle([x0, y_pos, x0 + sum(cw), y_pos + rh], fill=bg_color)
        curr_x = x0
        for v, w in zip(vals, cw):
            tw = dr.textlength(v, font=font_obj)
            dr.text((curr_x + (w - tw) / 2, y_pos + (rh - 32) / 2), v, font=font_obj, fill=fill_color)
            curr_x += w

    # 헤더: v3 공식 컬럼
    draw_row(["주택형", "세대수", "공급금액 범위", "가중평균", "공급 평당가"], y, fh, "white", GREEN)
    y += rh

    # 본문 행
    for i, r in enumerate(rows):
        bg_row = "white" if i % 2 == 0 else ALT
        draw_row(r, y, fb, INK, bg_row)
        y += rh

    # 하단 코랄 라인
    dr.line([x0, y, x0 + sum(cw), y], fill=CORAL, width=4)

    # 하단 각주 (v3 공식 주석)
    fs = get_font(bold=False, size=20)
    vat_notice = f" · {', '.join(vat_types)}형은 부가세 포함 금액" if vat_types else ""
    notes = [
        f"출처: 입주자모집공고문({a.date}) '공급금액 및 납부일정' · 평당가는 공급면적 기준 · 세대수 가중",
        f"※ 금액은 천만원 단위 반올림 · 발코니 확장비 별도{vat_notice}"
    ]
    for k, note in enumerate(notes):
        dr.text((x0, y + 26 + k * 34), note, font=fs, fill=GRAY)

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    im.save(a.out)
    print(f"[v3 완료] {a.out} (행 수: {len(rows)})")


if __name__ == "__main__":
    main()
