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
- Wikipedia 공개 이력 기반 보조 정보
- 나의 팀 자동 스쿼드 구성
- 팀 약점 분석 및 구매 추천
- 스쿼드 저장

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

OpenAI 키가 없거나 API 호출에 실패하면 로컬 템플릿 리포트로 자동 fallback됩니다.

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

## 15. 선수 이미지 캐시

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

## 16. 제출용 캡처 체크리스트

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

## 17. 문제 해결

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

## 18. 최종 제출 형태

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

