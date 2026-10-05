# sohyun-blog-kit

소현생정 네이버 블로그 초안 자동화용 도구 모음.

| 파일 | 용도 |
|---|---|
| `thumbnail.py` | 소현 양식 대표 이미지(1080x1350) 생성 |
| `fonts/` | IBM Plex Sans KR (SIL OFL 1.1, `fonts/OFL.txt`) |
| `thumbs/` | 블로그에 올릴 대표 이미지. uplika가 raw 주소로 내려받음 |
| `thumbs/jobs/*.json` | 사진 넣은 썸네일 주문서. push 하면 GitHub Action(`.github/workflows/thumbnail.yml`)이 사진을 내려받아 `thumbs/<같은 이름>.jpg`를 만들어 커밋 |
| `config.json` | 발행 설정. `publish_mode`: `private`(비공개 저장 후 보고) / `public`(바로 공개) |
| `log.md` | 작성한 초안 기록 (주제 중복 방지) |

## 사진 넣은 썸네일 (GitHub Action)

작업 환경에서는 Unsplash·uplika CDN 이 막혀 있어 사진을 직접 받을 수 없으므로 GitHub Action 이 대신 받는다.
Unsplash 다운로드 주소는 GitHub 서버에서 401 이 나므로, 먼저 uplika `media_from_url` 로 사진을 올리고 그 응답의 `publicUrl`(cdn.uplika.com, 약 2일 유지)을 쓴다.

```json
{"photo_url": "https://cdn.uplika.com/.../med_xxx.jpg", "tag": "[소현생정] 리빙포인트", "right": "살림 꿀팁",
 "kicker": "...", "line1": "...", "line2": "...", "note": "... · ... · ..."}
```

`thumbs/jobs/<YYYYMMDD>_<슬러그>.json` 으로 push → 약 1분 뒤 `Render thumbnails` 커밋이 생기면 `git pull` 후 이미지 확인 → raw 주소로 `media_from_url`.
