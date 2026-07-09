# FC26 Player Scouting Agent

축구게임인 FC26 선수 데이터셋을 기반으로 실제 스카우팅에 쓸 축구선수를 데이터 가중치로 랭킹을 나누고, 스카우팅 리포트를 생성하는 로컬 FastAPI 웹입니다.

## 실행

```bash
python3 -m venv app/venv
source app/venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8001
```

실행 파일은 `app/main.py`입니다.
위 명령의 `app.main:app`은 `app/main.py` 파일 안에 있는 FastAPI 객체 `app`을 실행한다는 뜻입니다.

브라우저에서 아래 주소로 접속합니다.

```text
http://127.0.0.1:8001
```

## 기능

- FC26 CSV 로딩
- 선수 검색
- 포지션/국적/지역/리그 필터
- 즉시전력형, 유망주형, 가성비형, 지역 스카우팅형 프리셋
- 가중치 기반 스카우팅 점수 계산
- 선수별 AI 스카우팅 리포트 생성
- 국적, 리그, 클럽을 활용한 지역/고향 proxy 반영
- 나의 팀 스쿼드 선택 
- AI로 영입 추천 선수 받음
- 나의 팀 스쿼드 점수 (종합, OVR, POT)


## 데이터 준비

아래 파일을 앱 데이터 폴더에 둡니다.

```text
data/raw/FC26_20250921.csv
```


## OpenAI 리포트

`.env`에 OpenAI API 키를 넣으면 선수 상세 리포트가 OpenAI 기반으로 생성됩니다.

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4.1-mini
```

키가 없거나 호출에 실패하면 기존 로컬 템플릿 리포트로 자동 fallback 합니다.

## API

```text
GET /api/fc26/meta
GET /api/fc26/players
GET /api/fc26/report/{player_id}
POST /api/fc26/chat/{player_id}
```

## 선수 이미지 캐시

CSV의 `player_face_url`을 사용해 선수 이미지를 로컬에 저장할 수 있습니다.

```bash
cd /Users/leezungzoo/Desktop/agent_design/aigent
source app/venv/bin/activate
python -m scripts.cache_player_images --limit 500
```

## 구조

```text
aigent/
  app/
    main.py                    웹 서버 실행 진입점
    api/
      fc26.py                  FC26 API 라우터
    core/
      config.py                파일 경로, 환경 설정
    schemas/
      fc26.py                  요청/응답 데이터 구조
    services/
      fc26_agent.py            스카우팅 리포트/채팅 답변 생성
      fc26_loader.py           CSV 로딩, 필터 옵션 생성
      fc26_scoring.py          선수 랭킹 점수 계산
    templates/
      index.html               메인 웹 화면
    static/
      css/
        styles.css             화면 스타일
      js/
        app.js                 화면 상호작용, API 호출
      images/
        players/               선수 이미지 캐시
  data/
    raw/
      FC26_20250921.csv        FC26 원본 데이터
  scripts/
    cache_player_images.py     선수 이미지 다운로드 스크립트
  requirements.txt             Python 라이브러리 목록
  README.md
```

## 실행 흐름

```text
app/main.py
  -> app/api/fc26.py
    -> app/services/fc26_loader.py
    -> app/services/fc26_scoring.py
    -> app/services/fc26_agent.py
  -> app/templates/index.html
  -> app/static/css/styles.css
  -> app/static/js/app.js
```
