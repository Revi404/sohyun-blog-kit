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

## 사진 넣은 썸네일 (Canva AI + GitHub Action)

썸네일 사진에는 글 주제의 대상 자체가 보여야 한다(제습제 글이면 제습제 통). 무료 사진에 없으면 Canva AI 로 만든다.

1. 대상의 실제 생김새(모양·재질·색·뚜껑 등 세부)를 먼저 조사하고, Canva `generate-image`(LANDSCAPE_16_9)에 영어로 구체적으로 적는다. 상표·글자 없이. 생김새가 틀리면 프롬프트를 고쳐 다시 만든다.
2. Canva 디자인 `DAHXG8rqYnU`(썸네일 사진 모음)에 1680x944 페이지를 추가하고 이미지를 꽉 채워 넣은 뒤 저장 → `export-design`(jpg, 그 페이지, width 1680)으로 원본 크기 URL 을 받는다. (generate-image 결과는 작은 미리보기만 받을 수 있어서 이 단계를 거친다.)
3. 그 URL 을 `photo_url` 로 `thumbs/jobs/<YYYYMMDD>_<슬러그>.json` 을 push → Action 이 `thumbs/<같은 이름>.jpg` 를 만들어 커밋.
4. raw 주소로 uplika `media_from_url`(aiGenerated: true).

작업 환경에서는 Unsplash·uplika CDN·Canva 다운로드 주소가 막혀 있어 사진을 직접 받을 수 없으므로 GitHub Action 이 대신 받는다. Unsplash 다운로드 주소는 GitHub 서버에서도 401 이 나므로, Unsplash 사진을 쓸 때는 uplika `media_from_url` 응답의 `publicUrl`(cdn.uplika.com, 약 2일 유지)을 쓴다.

```json
{"photo_url": "https://export-download.canva.com/...", "tag": "[소현생정] 리빙포인트", "right": "살림 꿀팁",
 "kicker": "...", "line1": "...", "line2": "...", "note": "... · ... · ..."}
```
