# 집:착 Backend

> 서울시 생활 만족 개선을 위한 주거 리스크 분석 플랫폼

## 📋 프로젝트 소개

"집:착"은 실거주 시의 주변의 리스크(소음, 인프라, 재난, 치안)로 인한 생활 만족도 저하 예방을 위한 사전 분석 서비스입니다.

## 🚀 주요 기능

- **주소 기반 리스크 종합 분석**: 입력된 주소(또는 좌표)를 기반으로 반경 내의 공공 데이터(CCTV, 배수장, 약국 등)를 PostGIS 공간 쿼리로 집계하여 리스크 수치를 도출합니다.
- **맞춤형 라이프스타일 가중치**: 청년 1인 가구, 신혼부부, 노부모 동거 가구 등 사용자 유형에 따라 치안, 소음, 침수, 의료, 혼잡도의 가중치를 다르게 적용하여 최적화된 생활 점수를 제공합니다.
- **다중 리포트 비교**: 여러 주소에 대한 분석 리포트를 동시에 비교하여 더 나은 거주지를 선택할 수 있도록 돕습니다.
- **비동기 분석 파이프라인**: 대량의 데이터 공간 집계로 인한 병목을 막기 위해 Background Tasks를 통해 분석을 비동기 처리하고 진행률(Processing Status)을 제공합니다.

## 🛠️ Backend 기술 스택

### 🔹 Core Environment
- **Python 3.11-slim**: 경량화된 Asynchronous I/O 기반의 메인 런타임
- **FastAPI**: Python 기반의 고성능 웹 프레임워크
- **SQLAlchemy (Async)**: 비동기 데이터베이스 ORM
- **Shapely & GeoAlchemy2**: GeoJSON 파싱 및 공간 쿼리(PostGIS) 연동

### 🔹 Database & Cache
- **PostgreSQL 16 (+ PostGIS 3.4)**: 메인 데이터베이스 및 지리 정보 시스템 확장
- **Redis 7**: 비동기 작업 큐 상태 관리 및 캐싱

### 🔹 Infrastructure
- **Compute**: GCP Compute Engine
- **Web Server**: Nginx (Reverse Proxy)
- **Container**: Docker & Docker Compose
- **CI/CD**: GitHub Actions (GHCR 빌드 & SCP/SSH Deploy)

## 📁 프로젝트 구조

```text
Project_JIP-CHAK_BE/
├── .github/
│   └── workflows/          # GitHub Actions CI/CD (GHCR 빌드 및 GCP 자동 배포)
├── app/
│   ├── api/                # API 엔드포인트 레이어 (v1/endpoints)
│   ├── core/               # 환경변수(Pydantic Settings) 및 전역 상수/보안 설정
│   ├── crud/               # DB CRUD 로직
│   ├── db/                 # 데이터베이스 연결, 세션 관리, Alembic 베이스
│   ├── models/             # SQLAlchemy DB 테이블 모델 (users, reports 등)
│   ├── repositories/       # PostGIS 공간 쿼리 등 복잡한 DB 접근 추상화 계층
│   ├── schemas/            # Pydantic 데이터 검증 모델 (Request/Response)
│   ├── services/           # 비즈니스 로직 (분석, 리포트 생성, 가중치 계산)
│   └── main.py             # FastAPI 앱 초기화 및 실행 (Entry Point)
├── data/                   # 분석용 공공데이터 원천 (CSV, GeoJSON, Meta JSON)
├── nginx/                  # 배포용 Nginx 리버스 프록시 설정
├── scripts/                # DB Seeding 스크립트 등 유틸리티
├── .dockerignore
├── .env                    # 환경변수 템플릿 및 설정
├── alembic.ini             # DB 마이그레이션 설정
├── Dockerfile              # 프로덕션 도커 이미지 빌드 스펙 (Multi-stage)
├── docker-compose.yml      # 프로덕션 배포용 컨테이너 오케스트레이션
├── docker-compose-dev.yml  # 로컬 개발 환경용 컨테이너 구성 (DB, Redis)
└── requirements.txt        # 프로젝트 의존성 목록
```

## 🌐 API 구조

- **`POST /api/v1/reports/analysis`**: 주소 정보를 입력받아 리스크 분석 요청 (Background Task ID 반환)
- **`GET  /api/v1/reports/status/{task_id}`**: 비동기 분석 작업 진행 상태 조회
- **`GET  /api/v1/reports/{report_id}`**: 종합 리포트 점수 및 카테고리 요약 정보 반환
- **`GET  /api/v1/reports/{report_id}/detail/{category}`**: 치안, 침수 등 세부 항목별 딥다이브 리포트 및 지표 반환
- **`POST /api/v1/reports/compare`**: 저장된 2개 이상의 리포트 점수 비교

## 🎯 개발 및 데이터 지침

프로젝트 내 분석 시스템은 `app/repositories` 내의 공간 쿼리와 `data/` 디렉토리 내의 사전 계산된 통계 지표(`meta_*.json`)를 결합하여 구동됩니다. 데이터를 추가하거나 업데이트할 경우, `scripts/seed_reference_data.py`를 통해 PostGIS 테이블(`ref_*`)에 적재해야 합니다.

### 사전 요구사항 (Prerequisites)

* **Python 3.11** 이상
* **Docker & Docker Compose** (로컬 DB 및 배포 환경)
* **Git**

### 설치 및 로컬 세팅 (Installation)

1. **저장소 클론 및 패키지 설치**
```bash
git clone https://github.com/Team-1AM-Club/Project_JIP-CHAK_BE.git
cd Project_JIP-CHAK_BE

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **환경변수 설정**
루트 디렉토리에 `.env` 파일을 생성하고 아래 **설정** 템플릿을 참고하여 값을 기입합니다.

3. **로컬 데이터베이스 구동 및 마이그레이션**
```bash
# PostGIS 및 Redis 컨테이너 백그라운드 실행
docker compose -f docker-compose-dev.yml up -d

# 테이블 스키마 생성
alembic upgrade head

# 기초 데이터베이스 시딩 (최초 1회 필수)
python scripts/seed_reference_data.py
```

4. **서버 실행**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### ⚙️ 설정 (.env)

**[로컬 개발 환경]**
로컬 루트에 다음을 포함하는 `.env` 파일을 작성하십시오.

```ini
# Database & Cache
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/jipchak
REDIS_URL=redis://localhost:6379/0

# App Settings
DATA_PROVIDER=db  # "mock" 또는 "db"

# Security
JWT_SECRET=your_super_secret_key
JWT_ALGORITHM=HS256

# OAuth & External APIs
KAKAO_CLIENT_ID=your_kakao_key
NAVER_CLIENT_ID=your_naver_key
GOOGLE_CLIENT_ID=your_google_key
GEOCODING_PROVIDER=naver
NAVER_MAPS_CLIENT_ID=your_maps_client_id
NAVER_MAPS_CLIENT_SECRET=your_maps_secret
```

### 🔄 CI/CD Pipeline

이 프로젝트는 **GitHub Actions**를 사용하여 GCP Compute Engine으로 자동 배포됩니다.

1. **Push**: `main` 브랜치에 코드가 푸시되면 워크플로우가 트리거됩니다.
2. **Build**: Docker 이미지를 빌드하고 **GHCR(GitHub Container Registry)**에 업로드합니다.
3. **Deploy**:
   - `scp-action`을 이용해 최신 `docker-compose.yml`과 `nginx.conf`를 서버로 복사합니다.
   - 운영 서버(GCP Instance)에 SSH로 접속합니다.
   - GitHub Secrets에 저장된 환경 변수로 서버 내 `.env` 파일을 갱신합니다.
   - 최신 Docker 이미지를 Pull 받아 `docker compose up -d`로 무중단 재시작합니다.

## 🎯 개발 가이드

### Git 컨벤션

- 브랜치, 커밋 메세지는 "type: 간단한 설명"
> 예시: `feat: 로그인 API 구현`

**타입 (Type)**

| 타입 (Type) | 설명 (Description) | 비고 |
| :--- | :--- | :--- |
| **`feat`** | **새로운 기능 추가** | 사용자에게 영향을 주는 새로운 기능 |
| **`fix`** | **버그 수정** | 사용자에게 영향을 주는 버그 수정 |
| **`docs`** | **문서 수정** | README.md, 주석 등 코드 로직과 무관한 문서 변경 |
| **`style`** | **코드 포맷팅** | **비즈니스 로직 변경 없음**. (오타 수정, 탭 사이즈 변경, 세미콜론 누락 등) |
| **`refactor`** | **코드 리팩토링** | 결과는 같으나 코드를 개선함 (변수명 변경, 코드 구조 개선) |
| **`perf`** | **성능 개선** | 실행 시간 단축, 메모리 효율 개선 등 |
| **`test`** | **테스트 코드** | 테스트 코드 추가, 수정, 삭제 (프로덕션 코드 변경 없음) |
| **`build`** | **빌드 시스템, 종속성 변경** | Gradle, npm 패키지 설치/삭제, 설정 파일 변경 |
| **`ci`** | **CI 구성 파일 변경** | GitHub Actions, CircleCI 설정 스크립트 등 |
| **`chore`** | **기타 자잘한 수정** | `.gitignore` 수정, 빌드 스크립트 수정 등 (소스코드 건드리지 않음) |
| **`revert`** | **커밋 되돌리기** | 이전 커밋을 취소할 때 사용 |

## 📝 License

![MIT License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge&logo=license&logoColor=white)

본 프로젝트의 소스 코드는 **MIT License**를 따릅니다.

## 👥 Contact

**Team 1AM-Club**에게 전하고 싶은 말씀이 있으신가요? 목적에 맞게 아래 채널로 연락해 주세요!

| **분류 (Category)** | **채널 (Channel)** |
| :--- | :--- |
| 🐛 **버그 제보 & 기능 요청** | [**GitHub Issues**](../../issues) |
| 📧 **기타 문의사항** | [**team.1am.club@gmail.com**](mailto:team.1am.club@gmail.com) |

[![GitHub Issues](https://img.shields.io/badge/GitHub%20Issues-Bug%20Report%20%26%20Feature%20Request-green?style=for-the-badge&logo=github)](../../issues)
[![Email](https://img.shields.io/badge/Team%201AM%20Club-team.1am.club%40gmail.com-EA4335?style=for-the-badge&logo=gmail&logoColor=white)](mailto:team.1am.club@gmail.com)
