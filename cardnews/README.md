# 소현 카드뉴스·티어표 도구

| 파일 | 역할 |
|---|---|
| `common.py` | 테마(sohyun/richlab), 글꼴, 스티커 목록(`../stickers/catalog.json`) 고르기, 넘침 자동 축소, 3:4 점검, 영상 인코딩 |
| `cardreel.py` | 카드뉴스 릴스: `python3 cardnews/cardreel.py render slides.json out/` |
| `tier.py` | 공통 티어표: `python3 cardnews/tier.py render tier.json out/` |

화면 규칙: 9:16(1080x1920) 캔버스, 내용은 가운데 3:4(1080x1440, y=240~1680) 안. 프로필 그리드 미리보기에서 잘리지 않게 하기 위함.
필요 패키지: playwright(+chromium), Pillow, ffmpeg. 글꼴은 `../fonts/`(Pretendard, Jua — OFL).
예약 작업은 이 저장소를 읽기만 한다(쓰기 금지). 도구 수정·스티커 등록은 수동 세션에서.
