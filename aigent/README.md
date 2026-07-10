# FC26 Player Scouting Agent

FC26 Player Scouting Agent는 FC26 선수 CSV 데이터를 기반으로 선수 랭킹, 스카우팅 리포트, 자유 질문 Chat Agent, 나의 팀 스쿼드 분석, AI 구매 추천 기능을 제공하는 FastAPI 웹 애플리케이션입니다.

이 프로젝트는 Oracle Cloud 기반 데이터 파이프라인 과제의 `수집 -> 저장 -> 가공 -> 제공` 흐름에 맞춰 구성했습니다.

## 1. 서비스 개요

축구 구단이 선수 영입을 검토할 때는 선수 능력치, 잠재력, 시장가치, 주급, 포지션 적합도, 국가/대륙, 공개 이력 등을 함께 확인해야 합니다. 이 프로젝트는 FC26 선수 데이터를 활용해 후보 선수를 랭킹화하고, 선택한 선수에 대해 AI 기반 스카우팅 리포트와 자유 질문 답변을 제공합니다.

주요 기능:

- FC26 CSV 데이터 로딩
- 선수명 검색
- 포지션, 국적, 대륙, 리그, 클럽 필터
- 가중치 기반 선수 랭킹
- 선수별 스카우팅 리포트
- OpenAI 기반 Chat Agent
- Middleware 기반 Chat Agent 실행 제어
- OpenAI 실패 시 로컬 미니 분석 fallback
- Wikipedia 공개 이력 기반 보조 정보
- 나의 팀 자동 스쿼드 구성
- 팀 약점 분석 및 구매 추천
- 스쿼드 저장 및 저장 스쿼드 기준 포지션 역할 브리핑

## 2. 데이터 파이프라인 구조

```text
Collect 수집
  - FC26 CSV 파일
  - Wikipedia REST API
  - OpenAI API

Store 저장
  - data/raw/FC26_20250921.csv
  - data/squads/squads.json
  - Oracle Database 테이블
  - OCI Block Volume /mnt/iscsi

Process 가공
  - 결측값 처리
  - 숫자 컬럼 변환
  - 국가 -> 대륙 매핑
  - 포지션 정규화
  - 가중치 기반 scouting_score 계산
  - 팀 약점 및 추천 선수 계산

Serve 제공
  - FastAPI REST API
  - 웹 대시보드
  - 스카우팅 Chat Agent
  - Middleware 세션 상태 및 호출 제한 관리
```

## 3. 실행 환경

권장 환경:

- OS: macOS, Linux, Oracle Linux
- Python: 3.11 이상 권장
- pip
- 웹 브라우저

Oracle Cloud 배포 시:

- OCI Compute VM
- Public IP
- Security List 또는 NSG에서 8001 포트 허용
- 선택: Oracle Database XE
- 선택: Block Volume `/mnt/iscsi`

## 4. 프로젝트 구조

```text
aigent/
  app/
    main.py                    FastAPI 서버 실행 진입점
    api/
      fc26.py                  FC26 API 라우터
    core/
      config.py                파일 경로 및 환경 설정
    schemas/
      fc26.py                  요청 데이터 스키마
    services/
      fc26_agent.py            AI 리포트/채팅 답변 생성
      fc26_middleware.py       Chat Agent middleware 세션/호출 제어
      fc26_loader.py           CSV 로딩 및 전처리
      fc26_scoring.py          선수 점수 계산
    templates/
      index.html               메인 웹 화면
    static/
      css/
        styles.css             웹 스타일
      js/
        app.js                 UI 동작 및 API 호출
      images/
        players/               선수 이미지 캐시
  data/
    raw/
      FC26_20250921.csv        원본 FC26 CSV
    squads/
      squads.json              저장된 스쿼드 JSON
  scripts/
    cache_player_images.py     선수 이미지 캐시 스크립트
  requirements.txt             Python 라이브러리 목록
  README.md
  .env
```

웹 서버 실행 진입점은 `app/main.py`입니다.

`app.main:app`은 `app/main.py` 파일 안에 있는 FastAPI 객체 `app`을 실행한다는 뜻입니다.

## 5. 백지 컴퓨터에서 로컬 실행하기

### 5.1 프로젝트 폴더로 이동

```bash
cd /path/to/aigent
```

예시:

```bash
cd /Users/leezungzoo/Desktop/agent_design/aigent
```

### 5.2 Python 가상환경 생성

```bash
python3 -m venv app/venv
```

### 5.3 가상환경 활성화

macOS/Linux:

```bash
source app/venv/bin/activate
```

Windows PowerShell:

```powershell
app\venv\Scripts\Activate.ps1
```

### 5.4 필수 라이브러리 설치

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

현재 필수 라이브러리:

```text
fastapi==0.118.0
uvicorn[standard]==0.37.0
pandas==2.3.3
requests==2.32.5
jinja2==3.1.6
python-dotenv==1.1.1
```

Oracle DB 연동을 사용할 경우 추가 설치:

```bash
pip install oracledb
```

## 6. 데이터 파일 준비

프로젝트 실행에는 FC26 CSV 파일이 필요합니다.

필수 위치:

```text
data/raw/FC26_20250921.csv
```

CSV 파일이 다른 위치에 있다면 프로젝트 루트에서 아래처럼 복사합니다.

```bash
mkdir -p data/raw
cp /path/to/FC26_20250921.csv data/raw/FC26_20250921.csv
```

예시:

```bash
mkdir -p data/raw
cp ~/Desktop/FC26_20250921.csv data/raw/FC26_20250921.csv
```

데이터 파일 확인:

```bash
ls -lh data/raw/FC26_20250921.csv
```

## 7. 환경변수 설정

프로젝트 루트에 `.env` 파일을 생성합니다.

```bash
touch .env
```

OpenAI 사용 시:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini
```

OpenAI 키가 없거나 API 호출에 실패하면 로컬 미니 분석 답변으로 자동 fallback됩니다.
이 fallback은 단순 고정 문장이 아니라 선수 능력치, 포지션, 시장가치, 주급, 성장성, 약점, 저장 스쿼드 정보를 조합해 질문 의도별 답변을 생성합니다.

Oracle DB 사용 시:

```env
ORACLE_USER=scout_app
ORACLE_PASSWORD=oracle
ORACLE_DSN=localhost:1521/XEPDB1
```

OpenAI 키 로딩 확인:

```bash
python - <<'PY'
from app.services.fc26_agent import get_openai_api_key
key = get_openai_api_key()
print("KEY_LOADED:", bool(key))
print("KEY_PREFIX:", key[:7] if key else "NO_KEY")
PY
```

## 8. 로컬 서버 실행

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

브라우저 접속:

```text
http://127.0.0.1:8001
```

API 확인:

```bash
curl http://127.0.0.1:8001/api/fc26/meta
```

선수 조회 테스트:

```bash
curl "http://127.0.0.1:8001/api/fc26/players?limit=3"
```

## 9. Oracle Cloud VM 배포 실행

### 9.1 로컬에서 Oracle Cloud VM으로 프로젝트 업로드

로컬 Mac 터미널에서 실행합니다.

```bash
rsync -avz --progress \
  -e "ssh -i ~/Downloads/ssh-key-2026-06-23.key" \
  --exclude "app/venv" \
  --exclude ".venv" \
  --exclude "__pycache__" \
  --exclude ".DS_Store" \
  /Users/leezungzoo/Desktop/agent_design/aigent/ \
  opc@147.224.161.6:/home/opc/aigent/
```

### 9.2 Oracle Cloud VM 접속

```bash
ssh -i ~/Downloads/ssh-key-2026-06-23.key opc@147.224.161.6
```

### 9.3 서버에서 라이브러리 설치

```bash
cd /home/opc/aigent
python3 -m venv app/venv
source app/venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install oracledb
```

### 9.4 서버에서 실행

```bash
cd /home/opc/aigent
source app/venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

브라우저 접속:

```text
http://147.224.161.6:8001
```

## 10. OCI 네트워크 설정

외부에서 접속하려면 OCI Console에서 8001 포트를 열어야 합니다.

설정 위치:

```text
VCN -> Subnet -> Security List 또는 Network Security Group
```

Ingress Rule:

```text
Source CIDR: 0.0.0.0/0
IP Protocol: TCP
Destination Port Range: 8001
Description: FastAPI web service
```

## 11. Block Volume 저장 절차

Block Volume이 `/mnt/iscsi`에 마운트되어 있다고 가정합니다.

확인:

```bash
lsblk
df -h /mnt/iscsi
```

저장 폴더 생성:

```bash
mkdir -p /mnt/iscsi/fc26-data/raw
mkdir -p /mnt/iscsi/fc26-data/squads
mkdir -p /mnt/iscsi/fc26-data/backups
```

원본 CSV 저장:

```bash
cp /home/opc/aigent/data/raw/FC26_20250921.csv /mnt/iscsi/fc26-data/raw/
```

스쿼드 저장 결과 백업:

```bash
cp /home/opc/aigent/data/squads/squads.json /mnt/iscsi/fc26-data/squads/
```

프로젝트 백업:

```bash
tar --exclude='aigent/app/venv' --exclude='aigent/.venv' --exclude='__pycache__' \
  -czf /mnt/iscsi/fc26-data/backups/aigent-source-backup.tar.gz \
  -C /home/opc aigent
```

저장 확인:

```bash
ls -lh /mnt/iscsi/fc26-data/raw
du -sh /mnt/iscsi/fc26-data
```

## 12. Oracle DB 준비 절차

Oracle 계정으로 접속:

```bash
sudo su - oracle
sqlplus / as sysdba
```

PDB 전환:

```sql
alter session set container = XEPDB1;
show con_name;
```

사용자 생성:

```sql
create user scout_app identified by oracle;
grant create session to scout_app;
grant create table, create sequence, create view to scout_app;
alter user scout_app quota unlimited on users;
```

사용자 접속:

```sql
connect scout_app/oracle@localhost:1521/XEPDB1
```

테이블 목록 확인:

```sql
select table_name
from user_tables
where table_name like 'SCOUT%';
```

스쿼드 테이블 확인:

```sql
desc scout_squads;
desc scout_squad_players;
desc scout_budget_settings;
```

## 13. 주요 API

```text
GET  /
GET  /api/fc26/meta
GET  /api/fc26/players
GET  /api/fc26/report/{player_id}
POST /api/fc26/chat/{player_id}
POST /api/fc26/team-analysis
POST /api/fc26/squads
GET  /api/fc26/session/status
POST /api/fc26/session/config
POST /api/fc26/session/approve
POST /api/fc26/session/reset
```

## 14. 주요 기능 사용 방법

1. 브라우저에서 `http://127.0.0.1:8001` 또는 `http://OCI_PUBLIC_IP:8001` 접속
2. 상단 필터에서 선수명, 포지션, 대륙, 국가, 리그, 클럽 선택
3. 가중치 기반 랭킹에서 선수 클릭
4. 오른쪽 Chat Agent에 자유 질문 입력
5. 나의 팀 페이지에서 팀 리그와 팀 선택
6. 선택 팀 기준 자동 스쿼드 구성 확인
7. 팀 AI 분석과 구매 추천 선수 확인
8. 저장 버튼으로 스쿼드 저장
9. 저장된 스쿼드를 기준으로 선수 활용 위치와 포지션 역할 질문

Chat Agent 질문 예시:

```text
이 선수 영입하면 어때?
이 선수 우리 팀에 왜 필요해?
단점까지 포함해서 이 선수 어떻게 써야 해?
이 선수를 저장된 스쿼드에서 어디로 쓸 수 있을까?
저장된 스쿼드 기준으로 이 선수 포지션 역할 브리핑해줘.
위키피디아 공개 정보를 더 자세히 보여줘.
```

## 15. Middleware 및 Agent 응답 구조

이 프로젝트의 Chat Agent는 `fc26_middleware.py`를 통해 세션 단위로 실행 상태를 관리합니다.

Middleware 제공 기능:

- `modelRunLimit`: LLM 호출 횟수 제한
- `toolRunLimit`: Wikipedia 같은 외부 도구 호출 횟수 제한
- `summarizeThreshold`: 대화가 길어졌을 때 이전 대화를 요약
- `humanInTheLoop`: 필요 시 도구 호출 승인 흐름 제공
- `session status`: 현재 세션의 호출 횟수, 로그, 요약 상태 확인

응답 생성 순서:

```text
1. 사용자가 선수를 선택하고 질문 입력
2. 저장 스쿼드 질문이면 squads.json 기준으로 우선 답변
3. Wikipedia 공개 정보가 필요한 경우 도구 호출
4. OpenAI API 호출 시도
5. OpenAI 실패 또는 키 미설정 시 local_mini_fallback 실행
6. 답변과 middleware 상태를 API 응답으로 반환
```

`local_mini_fallback`은 다음 질문 유형을 로컬 데이터만으로 분석합니다.

- 영입 판단
- 전술 활용
- 포지션 배치
- 단점 및 리스크
- 성장 가능성
- 이적료, 주급, 가성비
- 저장 스쿼드 기준 역할 브리핑
- Wikipedia 공개 정보 요약

## 16. 선수 이미지 캐시

CSV의 `player_face_url`을 사용해 선수 이미지를 로컬에 저장할 수 있습니다.

```bash
cd /home/opc/aigent
source app/venv/bin/activate
python -m scripts.cache_player_images --limit 500
```

로컬 실행 시:

```bash
cd /Users/leezungzoo/Desktop/agent_design/aigent
source app/venv/bin/activate
python -m scripts.cache_player_images --limit 500
```

## 17. 제출용 캡처 체크리스트

```text
1. OCI Compute VM 인스턴스 화면
2. SSH 접속 터미널
3. Block Volume lsblk 결과
4. /mnt/iscsi/fc26-data 저장 결과
5. Oracle DB scout_squads 테이블 조회 결과
6. FastAPI 서버 실행 터미널
7. Public IP 웹 접속 화면
8. 선수 랭킹 필터 화면
9. 스카우팅 Chat Agent 답변 화면
10. 나의 팀 자동 스쿼드 구성 화면
11. 팀 AI 분석 및 구매 추천 화면
```

## 18. 문제 해결

### ModuleNotFoundError

가상환경을 켜고 패키지를 다시 설치합니다.

```bash
source app/venv/bin/activate
pip install -r requirements.txt
```

### No module named uvicorn

```bash
pip install "uvicorn[standard]"
```

### Address already in use

이미 같은 포트에서 서버가 실행 중인 상태입니다.

```bash
lsof -i :8001
kill -9 PROCESS_ID
```

또는 다른 포트 사용:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002
```

### OpenAI fallback 발생

`.env` 확인:

```bash
grep -E "OPENAI_API_KEY|OPEN_API_KEY|open_api_key|openai_api_key" .env
```

서버 재시작:

```bash
Ctrl + C
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

OpenAI API 키가 없거나 잘못된 경우에도 서비스는 중단되지 않고 `local_mini_fallback`으로 답변합니다.
다만 이 경우 실제 LLM 추론이 아니라 FC26 CSV, 저장 스쿼드 JSON, Wikipedia 공개 정보 기반의 규칙형 분석 응답입니다.

### CSV 없음

아래 파일이 존재해야 합니다.

```bash
ls -lh data/raw/FC26_20250921.csv
```

없으면 복사합니다.

```bash
mkdir -p data/raw
cp /path/to/FC26_20250921.csv data/raw/FC26_20250921.csv
```

### Block Volume Input/output error

마운트는 되어 있는데 쓰기가 안 되는 경우 파일시스템 체크가 필요합니다.

```bash
df -h /mnt/iscsi
lsblk -f
dmesg | tail -50
sudo umount /mnt/iscsi
sudo fsck -y /dev/sdb
sudo mount /dev/sdb /mnt/iscsi
```

## 19. 개선할 점

향후 개선 방향:

- Agent 응답 품질을 단순 규칙형 fallback에서 더 발전시켜, 사용자의 질문 맥락을 장기적으로 기억하고 의도를 세밀하게 분류하는 LLM형 어시스턴트 구조로 고도화할 필요가 있습니다.
- 저장된 스쿼드, 이전 대화, 예산 조건, 포메이션 변화까지 함께 고려하는 컨텍스트 메모리 기반 의사결정 보조 기능을 강화해야 합니다.
- OpenAI API 사용 가능 상태와 fallback 상태를 UI에서 명확히 표시해 사용자가 현재 답변 근거와 추론 수준을 쉽게 구분할 수 있도록 개선해야 합니다.
- Oracle DB 저장 데이터를 API 응답과 더 긴밀히 연결해, JSON 파일뿐 아니라 DB 기반 스쿼드 이력 조회와 비교 분석까지 확장할 수 있습니다.
- 선수 비교 질문에서 두 명 이상의 선수를 자동 인식하고 능력치, 비용, 전술 적합도를 표 형태로 비교하는 기능을 추가할 수 있습니다.

## 20. 최종 제출 형태

제출 자료에는 아래를 포함합니다.

```text
1. Public Web URL: http://OCI_PUBLIC_IP:8001
2. GitHub 또는 압축 파일 링크
3. README.md
4. 아키텍처 다이어그램
5. 실행 캡처 이미지
6. Oracle DB / Block Volume 증빙 캡처
```

한 줄 요약:

```text
FC26 CSV 데이터를 OCI VM/Block Volume에 저장하고 Python으로 전처리 및 점수화한 뒤, FastAPI 웹 서비스와 OpenAI 기반 Chat Agent로 스카우팅 결과를 제공하는 OCI 기반 데이터 파이프라인 프로젝트입니다.
```
