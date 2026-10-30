#!/usr/bin/env python3
"""청약노트용 입주자모집공고문 PDF 추출기 (2026-10-30).

Claude가 PDF 전체 텍스트를 읽는 대신, 파이썬이 공급금액 표와 조건 문장만 뽑아
짧은 JSON으로 돌려준다. 공급금액 표 검증이 실패한 경우에만 Claude가 해당 쪽을 읽는다.

사용:
  python3 -I cheongyak_pdf_extract.py 공고문.pdf [--report report.json] [--out 폴더]

  --report : 청약홈 커넥터 get_complex_report 결과(JSON)를 저장한 파일. 주면 세대수·최고가를 대조한다.
  --check  : 커넥터 값을 짧게 직접 적기(파일 저장 대신). 예: --check "총239 84A:135:63100 84B:42:61700"
             (총세대, 약식주택형:일반+특별 세대수:LTTOT_TOP_AMOUNT 만원)
  --out    : 결과 저장 폴더(기본: PDF와 같은 폴더). 공급금액_동층별_추출.csv, pdf_extract.json 을 쓴다.

표준 출력에는 pdf_extract.json 과 같은 요약 JSON만 찍는다(수 KB 이내).
"""
import argparse, csv, json, os, re, sys

import pdfplumber

NUM = re.compile(r'^-?[\d,]+$')


def num(x):
    if x is None:
        return 0
    s = str(x).replace('\n', '').replace(' ', '').strip()
    if s in ('', '-', '–', '0'):
        return 0
    s = re.sub(r'[^\d,\-]', '', s)
    return int(s.replace(',', '')) if s and NUM.match(s) else None


def clean(x):
    return re.sub(r'\s+', '', str(x)) if x is not None else ''


# ---------------------------------------------------------------- 공급금액 표
def header_labels(rows):
    """머리글 행들을 열마다 '상위>하위' 문자열로 합친다(병합 칸은 왼쪽 값 이어받기)."""
    ncol = max(len(r) for r in rows)
    labels = [''] * ncol
    for r in rows:
        last = ''
        for c in range(ncol):
            v = clean(r[c]) if c < len(r) else ''
            if v:
                last = v
                labels[c] = (labels[c] + '>' + v) if labels[c] else v
            elif last and r is rows[0]:
                labels[c] = last  # 첫 행 병합 칸(예: 공급금액 아래 4칸)
    return labels


def map_columns(labels):
    col = {'mid': [], 'dep': []}
    for i, l in enumerate(labels):
        if '대지비' in l:
            col['land'] = i
        elif '건축비' in l:
            col['build'] = i
        elif '부가' in l:
            col['vat'] = i
        elif '계약금' in l:
            col['dep'].append(i)
        elif '중도금' in l:
            col['mid'].append(i)
        elif '잔금' in l:
            col['bal'] = i
        elif ('공급금액' in l or l.endswith('계')) and 'total' not in col and 'land' in col:
            col['total'] = i
        elif '층' in l and '세대' not in l and 'floor' not in col:
            col['floor'] = i
        elif ('약식' in l or '주택형' in l) and 'type' not in col:
            col['type'] = i
        elif '세대' in l and 'cnt' not in col and 'floor' in col:
            col['cnt'] = i  # 층 다음의 '해당세대수'
    # 계/공급금액 열이 머리글로 안 잡히면 대지비·건축비(·부가세) 다음 열
    if 'total' not in col and 'build' in col:
        col['total'] = max(col['build'], col.get('vat', -1)) + 1
    ok = all(k in col for k in ('type', 'floor', 'cnt', 'land', 'build', 'total', 'bal')) and col['mid']
    return col if ok else None


def pct(labels, key):
    for l in labels:
        if key in l:
            m = re.search(r'\((\d+)%\)', l)
            if m:
                return int(m.group(1))
    return None


def extract_price_rows(pdf):
    rows, pages, col, ratios, ncol = [], [], None, {}, 0
    cur_type = None
    for pi, page in enumerate(pdf.pages):
        for t in page.extract_tables():
            if not t:
                continue
            flat = ' '.join(clean(c) for r in t[:4] for c in r if c)
            start = 0
            if '대지비' in flat and '건축비' in flat:
                # 데이터 첫 행 = 층 칸에 '층' 또는 숫자 구간이 나오는 첫 행
                for k, r in enumerate(t):
                    if any(re.match(r'^\d+(?:[~\-]\d+)?층?(이상|이하)?$', clean(c)) for c in r if c) and \
                       sum(1 for c in r if num(c)) >= 5:
                        start = k
                        break
                labels = header_labels(t[:start])
                newcol = map_columns(labels)
                if not newcol:
                    continue
                col, ncol = newcol, len(labels)
                ratios = {'계약금': pct(labels, '계약금'), '중도금': pct(labels, '중도금'), '잔금': pct(labels, '잔금')}
                cur_type = None
            elif col is None or len(t[0]) != ncol:
                continue  # 이어지는 쪽 표는 열 수가 같을 때만
            used = False
            for r in t[start:]:
                r = list(r) + [None] * (ncol - len(r))
                ty = clean(r[col['type']])
                if ty:
                    m = re.search(r'(\d{2,3}(?:\.\d+)?[A-Z]?\d?)', ty)
                    if m:
                        cur_type = m.group(1)
                if any(k in clean(x) for x in r for k in ('합계', '소계')):
                    continue
                floor = clean(r[col['floor']])
                cnt = num(r[col['cnt']])
                total = num(r[col['total']])
                if not floor or not cnt or not total or cur_type is None:
                    continue
                deps = [num(r[i]) or 0 for i in col['dep']]
                mids = [num(r[i]) or 0 for i in col['mid']]
                rows.append({
                    'type': cur_type, 'floor': floor if '층' in floor else floor + '층', 'cnt': cnt,
                    'land': num(r[col['land']]) or 0, 'build': num(r[col['build']]) or 0,
                    'vat': num(r[col['vat']]) or 0 if 'vat' in col else 0, 'total': total,
                    'dep1': deps[0] if deps else 0, 'dep2': sum(deps[1:]), 'mids': mids,
                    'bal': num(r[col['bal']]) or 0, 'page': pi + 1,
                })
                used = True
            if used and (pi + 1) not in pages:
                pages.append(pi + 1)
    return rows, pages, ratios


def short_type(house_ty):
    """커넥터 HOUSE_TY('084.9424A') → 공고문 약식('84A')."""
    s = house_ty.strip()
    m = re.match(r'0*(\d+)\.\d+([A-Z]*)', s)
    return (m.group(1) + m.group(2)) if m else s


def validate(rows, report):
    errs = []
    for r in rows:
        tag = f"{r['type']} {r['floor']}(p{r['page']})"
        if r['land'] + r['build'] + r['vat'] != r['total']:
            errs.append(f'{tag}: 대지비+건축비+부가세≠공급금액')
        if r['dep1'] + r['dep2'] + sum(r['mids']) + r['bal'] != r['total']:
            errs.append(f'{tag}: 계약금+중도금+잔금≠공급금액')
    by_type = {}
    for r in rows:
        b = by_type.setdefault(r['type'], {'cnt': 0, 'max': 0, 'min': 10**12})
        b['cnt'] += r['cnt']; b['max'] = max(b['max'], r['total']); b['min'] = min(b['min'], r['total'])
    check = {'세대수합계': sum(r['cnt'] for r in rows)}
    if report:
        notice, units = report.get('notice') or {}, report.get('unit_types') or []
        tot = notice.get('TOT_SUPLY_HSHLDCO')
        check['청약홈_총세대'] = tot
        if tot and check['세대수합계'] != tot:
            errs.append(f"세대수 합계 {check['세대수합계']} ≠ 청약홈 {tot}")
        for u in units:
            k = short_type(u['HOUSE_TY'])
            want_cnt = int(u.get('SUPLY_HSHLDCO') or 0) + int(u.get('SPSPLY_HSHLDCO') or 0)
            want_max = int(u.get('LTTOT_TOP_AMOUNT') or 0) * 10000
            got = by_type.get(k)
            if not got:
                errs.append(f'{k}: 공고문 표에서 못 찾음'); continue
            if got['cnt'] != want_cnt:
                errs.append(f"{k}: 세대수 {got['cnt']} ≠ 청약홈 {want_cnt}")
            if got['max'] != want_max:
                errs.append(f"{k}: 최고가 {got['max']:,} ≠ 청약홈 {want_max:,}")
    return errs, by_type, check


# ---------------------------------------------------------------- 조건 문장
TERMS = {  # 키마다 앞쪽 패턴이 우선(먼저 채워짐)
    '중도금': [r'이자\s*후불', r'무이자', r'자납', r'대출\s*알선', r'대납', r'중도금\s*대출'],
    '발코니': [r'발코니.{0,10}(무상|유상)', r'발코니.{0,15}(미포함|포함)', r'발코니\s*확장.{0,20}(금액|비용)'],
    '선택품목': [r'시스템\s*에어컨', r'추가\s*선택\s*품목'],
    '전매·재당첨·거주의무': [r'전매\s*제한\s*기간', r'재당첨\s*제한', r'거주\s*의무'],
    '공급규모': [r'공급\s*규모', r'총\s*[\d,]+\s*세대'],
    '사업주체·시공': [r'(시행|시공|사업주체|위탁자|수탁자).{0,15}(㈜|\(주\)|주식회사)'],
    '접수방법': [r'(특별공급|1순위|2순위).{0,40}(인터넷|청약홈|견본주택|현장)\s*(접수|청약|신청)'],
}
SKIP = re.compile(r'인지세|처벌|부적격|콜센터|중복\s*신청')
MAX_PER_KEY = 4
MAX_LEN = 220


def sentences(text):
    text = re.sub(r'[ \t]+', ' ', text)
    parts = re.split(r'(?:\n\s*(?=[■□•※ㆍ\-①-⑳]))|(?<=다\.)\s+', text)
    for p in parts:
        p = p.replace('\n', ' ').strip()
        if len(p) > 12:
            yield p


def extract_terms(pages_text):
    sents = [(pi, x) for pi, t in enumerate(pages_text) for x in sentences(t) if not SKIP.search(x)]
    out = {k: [] for k in TERMS}
    seen = set()
    for key, pats in TERMS.items():
        for pat in pats:
            for pi, x in sents:
                if len(out[key]) >= MAX_PER_KEY:
                    break
                if re.search(pat, x) and x[:60] not in seen:
                    seen.add(x[:60])
                    out[key].append(f'p{pi + 1}: ' + (x[:MAX_LEN] + '…' if len(x) > MAX_LEN else x))
    # 1쪽 요약표(주택유형·규제지역·재당첨·전매·거주의무 등) 한 덩어리
    first = ' '.join(pages_text[:2]).replace('\n', ' ')
    i = first.find('재당첨')
    summary = first[max(0, i - 150): i + 250] if i >= 0 else None
    return out, summary


AMT = re.compile(r'\d{1,3}(?:,\d{3}){1,}')


def balcony_lines(pages_text, skip_pages):
    """'발코니' 제목 바로 아래 금액 줄(주택형 머리줄 포함)만 뽑는다. 공급금액 표 쪽은 뺀다."""
    out = []
    for pi, t in enumerate(pages_text):
        if pi + 1 in skip_pages or '발코니' not in t:
            continue
        lines = [l.strip() for l in t.split('\n')]
        for j, l in enumerate(lines):
            if AMT.search(l) and any('발코니' in x for x in lines[max(0, j - 6):j + 1]) and not SKIP.search(l):
                for x in (lines[j - 1] if j else '', l):
                    item = f'p{pi + 1}: {x}'
                    if x and item not in out and len(x) < 200:
                        out.append(item)
        if len(out) >= 16:
            break
    return out[:16]


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf')
    ap.add_argument('--report')
    ap.add_argument('--check')
    ap.add_argument('--out')
    a = ap.parse_args()
    out_dir = a.out or os.path.dirname(os.path.abspath(a.pdf))
    os.makedirs(out_dir, exist_ok=True)
    report = json.load(open(a.report, encoding='utf-8')) if a.report else None
    if a.check:
        report = {'notice': {}, 'unit_types': []}
        for tok in a.check.split():
            if tok.startswith('총'):
                report['notice']['TOT_SUPLY_HSHLDCO'] = int(tok[1:])
            else:
                ty, cnt, top = tok.split(':')
                report['unit_types'].append({'HOUSE_TY': ty, 'SUPLY_HSHLDCO': int(cnt),
                                             'SPSPLY_HSHLDCO': 0, 'LTTOT_TOP_AMOUNT': top})

    with pdfplumber.open(a.pdf) as pdf:
        pages_text = [(p.extract_text() or '') for p in pdf.pages]
        rows, price_pages, ratios = extract_price_rows(pdf)
    terms, summary = extract_terms(pages_text)
    balc = balcony_lines(pages_text, set(price_pages))
    cand_pages = [i + 1 for i, t in enumerate(pages_text) if '대지비' in t and '건축비' in t]

    errs, by_type, check = validate(rows, report) if rows else (['공급금액 표를 찾지 못함'], {}, {})
    k = max((len(r['mids']) for r in rows), default=0)
    csv_path = os.path.join(out_dir, '공급금액_동층별_추출.csv')
    if rows:
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.writer(f)
            w.writerow(['주택형', '층구분', '세대수', '대지비', '건축비', '부가세', '공급금액계',
                        '계약금1차', '계약금2차', '중도금회차별', '잔금'])
            for r in rows:
                mid = r['mids'][0] if r['mids'] and len(set(r['mids'])) == 1 else '|'.join(map(str, r['mids']))
                w.writerow([r['type'], r['floor'], r['cnt'], r['land'], r['build'], r['vat'], r['total'],
                            r['dep1'], r['dep2'], mid, r['bal']])

    result = {
        'status': 'ok' if rows and not errs else 'price_table_failed',
        'pages': len(pages_text),
        'price': {
            'pages': price_pages, 'candidate_pages': cand_pages, 'rows': len(rows),
            'mid_installments': k, 'ratios_pct': ratios, 'check': check,
            'by_type': {t: {'세대수': v['cnt'], '최저': v['min'], '최고': v['max']} for t, v in by_type.items()},
            'csv': csv_path if rows else None, 'errors': errs[:15],
        },
        'balcony_lines': balc,
        'summary_block': summary,
        'terms': terms,
    }
    js = json.dumps(result, ensure_ascii=False, indent=1)
    open(os.path.join(out_dir, 'pdf_extract.json'), 'w', encoding='utf-8').write(js)
    print(js)
    return 0 if result['status'] == 'ok' else 2


if __name__ == '__main__':
    sys.exit(main())
