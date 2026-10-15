#!/usr/bin/env python3
"""세션 작업 사본 만들기 (git clone이 막힌 예약 세션용, 2026-10-15).

raw.githubusercontent.com 에서 tools/mirror_manifest.txt 에 적힌 파일과
stickers/catalog.json 이 가리키는 스티커 파일을 받아 git 없는 읽기용 사본을 만든다.
thumbs/ · backups/ · jobs/ · cheongyak/ 는 받지 않는다(필요한 파일만 --also 로 받기).

사용:
  python3 raw_mirror.py [대상폴더] [--also 경로 ...]
  대상폴더 기본값: /home/claude/sohyun-blog-kit
끝에 'MIRROR OK <파일 수>' 또는 'MIRROR FAIL ...' 을 출력한다(실패 시 종료코드 1).

manifest 는 GitHub Action(.github/workflows/manifest.yml)이 push 때마다 자동으로 다시 만든다.
"""
import concurrent.futures as cf
import json
import os
import sys
import time
import urllib.parse
import urllib.request

RAW = "https://raw.githubusercontent.com/Revi404/sohyun-blog-kit/main/"


def get(path, tries=3):
    last = None
    for i in range(tries):
        try:
            url = RAW + urllib.parse.quote(path, safe="/")
            with urllib.request.urlopen(url, timeout=60) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"{path}: {last}")


def save(dest, path):
    data = get(path)
    out = os.path.join(dest, path)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(data)
    return path


def main():
    args = sys.argv[1:]
    also = []
    if "--also" in args:
        i = args.index("--also")
        also = args[i + 1:]
        args = args[:i]
    dest = args[0] if args else "/home/claude/sohyun-blog-kit"
    os.makedirs(dest, exist_ok=True)

    manifest = get("tools/mirror_manifest.txt").decode("utf-8")
    paths = [l.strip() for l in manifest.splitlines() if l.strip() and not l.startswith("#")]
    paths += also

    failed = []
    with cf.ThreadPoolExecutor(8) as ex:
        futs = {ex.submit(save, dest, p): p for p in dict.fromkeys(paths)}
        for f in cf.as_completed(futs):
            try:
                f.result()
            except Exception as e:  # noqa: BLE001
                failed.append(str(e))

    # catalog 에 새로 등록됐는데 manifest 갱신 전인 스티커도 받는다
    extra = []
    try:
        cat = json.load(open(os.path.join(dest, "stickers/catalog.json"), encoding="utf-8"))
        for s in cat.get("stickers", []):
            for k in ("full", "blog"):
                p = s.get(k)
                if isinstance(p, str) and not os.path.exists(os.path.join(dest, p)):
                    extra.append(p)
    except Exception as e:  # noqa: BLE001
        failed.append(f"catalog: {e}")
    for p in extra:
        try:
            save(dest, p)
        except Exception as e:  # noqa: BLE001
            failed.append(str(e))

    n = len(set(paths)) + len(extra) - len(failed)
    if failed:
        print("MIRROR FAIL", len(failed), "files")
        for f in failed[:20]:
            print(" -", f)
        sys.exit(1)
    print("MIRROR OK", n, "files ->", dest)


if __name__ == "__main__":
    main()
