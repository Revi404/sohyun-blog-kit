"""청약노트 주택형별 공급금액 요약표 이미지 생성.

입력
  --rows   모집공고문에서 추출한 동·층별 CSV
           (주택형,층구분,세대수,대지비,건축비,부가세,공급금액계,계약금1차,계약금2차,중도금회차별,잔금)
  --area   주택형별 공급면적 JSON, 예: {"84A":110.3043,...}  (청약홈 커넥터 SUPLY_AR)
  --name   단지 약칭 (예: 화서역 아너스빌)
  --date   모집공고일 YYYY.MM.DD
  --out    출력 PNG 경로
"""
import argparse, json
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

F = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FB = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
GREEN, CORAL, BG, ALT = "#0E4D33", "#E2583B", "#F4F1EA", "#E7EFE3"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", required=True)
    ap.add_argument("--area", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    d = pd.read_csv(a.rows)
    assert ((d.대지비 + d.건축비 + d.부가세) == d.공급금액계).all(), "대지비+건축비+부가세 != 계"
    sup = json.loads(a.area)
    rows = []
    for t, x in d.groupby("주택형", sort=False):
        avg = (x.공급금액계 * x.세대수).sum() / x.세대수.sum()
        per = f"{avg / 1e4 / (sup[t] / 3.305785):,.0f}만" if t in sup else "-"
        rows.append([t, f"{int(x.세대수.sum())}", f"{x.공급금액계.min() / 1e8:.2f}억",
                     f"{x.공급금액계.max() / 1e8:.2f}억", per, "포함" if x.부가세.max() > 0 else "-"])

    W, pad, rh = 1080, 56, 64
    cw = [150, 130, 200, 200, 210, 110]
    x0 = (W - sum(cw)) // 2
    H = pad + 130 + rh * (len(rows) + 1) + 150
    im = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle([x0, pad, x0 + 250, pad + 44], radius=22, fill=GREEN)
    dr.text((x0 + 22, pad + 6), "[소현생정] 청약노트", font=ImageFont.truetype(FB, 22), fill="white")
    dr.text((x0, pad + 62), f"{a.name} 주택형별 공급금액", font=ImageFont.truetype(FB, 36), fill="#151515")
    y = pad + 130
    fh, fb = ImageFont.truetype(FB, 24), ImageFont.truetype(F, 26)

    def row(vals, y, font, fill, bg):
        dr.rectangle([x0, y, x0 + sum(cw), y + rh], fill=bg)
        x = x0
        for v, w in zip(vals, cw):
            tw = dr.textlength(v, font=font)
            dr.text((x + (w - tw) / 2, y + (rh - 32) / 2), v, font=font, fill=fill)
            x += w

    row(["주택형", "세대수", "최저", "최고", "3.3㎡당 평균", "부가세"], y, fh, "white", GREEN)
    y += rh
    for i, r in enumerate(rows):
        row(r, y, fb, "#151515", "white" if i % 2 == 0 else ALT)
        y += rh
    dr.line([x0, y, x0 + sum(cw), y], fill=CORAL, width=4)
    fs = ImageFont.truetype(F, 20)
    for k, t in enumerate([f"출처: 입주자모집공고문({a.date}) '공급금액 및 납부일정' · 단위 원(억) · 3.3㎡당은 공급면적·세대수 가중",
                           "※ 동·층별 금액은 공고문 원문 확인 · 선택품목(옵션) 비용 별도"]):
        dr.text((x0, y + 26 + k * 34), t, font=fs, fill="#5B5B5B")
    im.save(a.out)
    print(a.out, len(d), int(d.세대수.sum()))


if __name__ == "__main__":
    main()
