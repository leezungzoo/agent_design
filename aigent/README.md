# FC26 Player Scouting Agent

FC26 선수 데이터셋을 기반으로 가중치별 선수 랭킹과 스카우팅 리포트를 생성하는 로컬 FastAPI 웹 앱입니다.

## 실행

```bash
cd ~/Desktop/aigent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8001
```

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

## 데이터 준비

아래 파일을 앱 데이터 폴더에 둡니다.

```text
data/raw/FC26_20250921.csv
```

현재 작업에서는 `/Users/leezungzoo/Desktop/FC26_20250921.csv`를 복사해 사용합니다.

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
```

## 전체 타자 데이터 크롤링

STATIZ의 타자 기본 지표 테이블을 크롤링해서 앱이 읽는 CSV로 저장합니다.

```bash
cd ~/Desktop/aigent
source .venv/bin/activate
python -m scripts.crawl_batters --year-start 2024 --year-end 2024 --limit 1000 --min-pa 0
```

생성 파일:

```text
data/raw/statiz_batters_2024_2024.csv
data/processed/batters.csv
```

앱은 `data/processed/batters.csv`가 있으면 샘플 데이터 대신 이 파일을 사용합니다.
현재 기본 STATIZ 테이블에는 RAA가 없을 수 있어 `raa=0`으로 저장합니다.
RAA가 포함된 URL을 추가하면 `player` 기준으로 병합해 확장하면 됩니다.

현재 STATIZ 기록실이 로그인 페이지를 반환하면 로그인 쿠키가 필요합니다.
브라우저에서 STATIZ 로그인 후 개발자도구의 Request Headers에서 `Cookie` 값을 복사해 아래처럼 실행합니다.

```bash
python -m scripts.crawl_batters \
  --url "브라우저에서 복사한 STATIZ 기록실 URL" \
  --cookie "PHPSESSID=...; other_cookie=..."
```

## 2026 전체 선수 목록 크롤링

`https://www.statiz.co.kr/player/`에서 2026년 선수 목록을 크롤링해 CSV로 저장합니다.
현재 STATIZ 선수 페이지도 로그인 페이지를 반환하므로 로그인 쿠키가 필요합니다.

```bash
cd ~/Desktop/aigent
source .venv/bin/activate
python -m scripts.crawl_players \
  --year 2026 \
  --url "https://www.statiz.co.kr/player/" \
  --cookie "PHPSESSID=...; other_cookie=..."
```

생성 파일:

```text
data/processed/statiz_players_2026.csv
```

웹 앱은 `/api/statiz/players?year=2026`에서 이 CSV를 JSON으로 제공하고,
메인 화면 하단의 `2026 STATIZ 선수 CSV` 테이블에도 표시합니다.

## 구조

```text
app/
  main.py          FastAPI 엔트리포인트
  scoring.py       위험도 점수 계산
  crawler.py       HTML table 크롤링 유틸
  sample_data.py   데모용 샘플 데이터
  templates/
    index.html
  static/
    styles.css
    app.js
```
