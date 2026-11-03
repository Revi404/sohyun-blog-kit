"""소현생정 티스토리(sohyunguide) 애드센스 승인 글 20편 발행기.

PC에서 실행. 소현생정 티스토리스킨 tools 폴더의 tistory_client.py 를 씁니다.
  set TISTORY_BLOG=sohyunguide
  set TISTORY_PROFILE=D:\\소현생정_티스토리\\_browser\\tistory
  python publish_adsense.py --client-dir <tistory_client.py 폴더> --nos 1-4 --mode now
  python publish_adsense.py --client-dir ... --nos 11-19 --mode schedule --first-day 2026-11-05 --time 07:30

- 카테고리: 'IT 꿀팁/윈도우·PC' (없으면 'IT 꿀팁'). --category-id 로 직접 지정 가능.
- 이미 발행한 번호는 result.json 에 기록되어 다시 올리지 않습니다.
- 403(하루 한도) 등 실패가 나오면 그 자리에서 멈춥니다.
- 예약(schedule)은 published=Unix 초, 첫 글이 first-day, 이후 하루 1편.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import random
import string
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
KST = dt.timezone(dt.timedelta(hours=9))


def parse_nos(s: str) -> list[int]:
    out = []
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-")
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def find_category(t, explicit: int | None) -> int:
    if explicit:
        return explicit
    ids = t.category_ids()
    norm = {k.replace("&middot;", "·").replace(" ", ""): v for k, v in ids.items()}
    for key in ("IT꿀팁/윈도우·PC", "IT꿀팁"):
        if key in norm:
            print(f"카테고리 {key} = {norm[key]}")
            return norm[key]
    print("카테고리를 찾지 못함:", list(ids)[:30])
    sys.exit(2)


def public_ok(url: str) -> int:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status
    except Exception as e:  # noqa: BLE001
        return getattr(e, "code", 0) or -1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client-dir", required=True)
    ap.add_argument("--nos", required=True)
    ap.add_argument("--mode", choices=["now", "schedule"], required=True)
    ap.add_argument("--first-day", help="예약 첫 날 YYYY-MM-DD (KST)")
    ap.add_argument("--time", default="07:30")
    ap.add_argument("--category-id", type=int)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    sys.path.insert(0, a.client_dir)
    from tistory_client import Tistory  # noqa: E402

    manifest = {x["no"]: x for x in json.load(open(HERE / "manifest.json", encoding="utf-8"))}
    res_path = HERE / "result.json"
    results = json.load(open(res_path, encoding="utf-8")) if res_path.exists() else {}
    nos = [n for n in parse_nos(a.nos) if str(n) not in results]
    if not nos:
        print("올릴 글 없음 (모두 result.json 에 있음)")
        return

    with Tistory() as t:
        if not t.ensure_login():
            print("로그인 필요: python tistory_client.py login 으로 대표가 직접 로그인")
            sys.exit(3)
        cat = find_category(t, a.category_id)
        for i, n in enumerate(nos):
            m = manifest[n]
            content = (HERE / m["file"]).read_text(encoding="utf-8")
            assert "<a " not in content and "http" not in content, f"{n}번에 링크가 있음"
            if a.mode == "schedule":
                day = dt.date.fromisoformat(a.first_day) + dt.timedelta(days=i)
                hh, mm = map(int, a.time.split(":"))
                when = dt.datetime(day.year, day.month, day.day, hh, mm, tzinfo=KST)
                published = int(when.timestamp())
            else:
                when, published = None, 1
            body = {"id": "0", "title": m["title"], "content": content, "slogan": "", "visibility": 20,
                    "category": cat, "tag": ",".join(m["tags"]), "published": published,
                    "password": "".join(random.choices(string.ascii_letters + string.digits, k=8)),
                    "uselessMarginForEntry": 1, "daumLike": None, "cclCommercial": 0, "cclDerive": 0,
                    "type": "post", "attachments": [], "recaptchaValue": "", "draftSequence": None,
                    "totalWritingTimeMs": random.randint(300000, 900000)}
            print(f"[{n:02d}] {m['title']} ({'예약 ' + when.strftime('%m-%d %H:%M') if when else '즉시 공개'})")
            if a.dry_run:
                continue
            try:
                j = t.json("POST", "/manage/post.json", body)
            except Exception as e:  # noqa: BLE001
                print("  실패, 중단:", str(e)[:300])
                break
            url = (j.get("entryUrl") or j.get("url")) if isinstance(j, dict) else None
            if not url:
                print("  응답에 주소 없음, 중단:", str(j)[:300])
                break
            st = public_ok(url) if a.mode == "now" else None
            results[str(n)] = {"url": url, "mode": a.mode, "scheduled": when.isoformat() if when else None,
                               "public_status": st, "at": dt.datetime.now(KST).isoformat(timespec="seconds")}
            json.dump(results, open(res_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print("  ->", url, "비로그인 상태코드", st)
            time.sleep(random.uniform(20, 40))
    print("완료. 기록:", res_path)


if __name__ == "__main__":
    main()
