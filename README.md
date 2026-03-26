# 집:착 Backend

> 서울시 생활 만족 개선을 위한 주거 리스크 분석 플랫폼

## 📋 프로젝트 소개

"집:착"은 실거주 시의 주변의 리스크(소음, 인프라, 재난, 치안)로 인한 생활 만족도 저하 예방을 위한 사전 분석 서비스입니다.

## 🚀 주요 기능

- **Update Soon...**

## 🛠️ Backend 기술 스택

### 🔹 Core Environment
- **Python 3.11-slim**: 경량화된 Asynchronous I/O 기반의 메인 런타임
- **FastAPI**: Python 기반의 고성능 웹 프레임워크
- **Update Soon...**

### 🔹 Database
- **PostgreSQL**: 메인 데이터베이스

### 🔹 Infrastructure
- **Compute**: GCP Compute Engine
- **OS**: Ubuntu 22.04 LTS
- **CI/CD**: GitHub Actions (SSH Deploy)

## 📁 프로젝트 구조

```
Project_JIP-CHAK_BE/
├── .github/
│   └── workflows/          # GitHub Actions CI/CD 스크립트
│       └── deploy.yml      # GCP Compute Engine 배포 자동화
├── app/
│   ├── api/                # API 엔드포인트 레이어
│   │   └── v1/
│   │       └── endpoints/  # 도메인별 세부 라우터 (user, data 등)
│   ├── core/               # 앱 전역 설정
│   │   ├── config.py       # 환경변수(Pydantic Settings) 및 상수
│   │   └── security.py     # JWT 인증 및 암호화 관련
│   ├── crud/               # DB CRUD 로직 (Create, Read, Update, Delete)
│   ├── db/                 # 데이터베이스 연결 및 세션 관리
│   │   ├── base.py         # 모든 모델을 Import (Alembic용)
│   │   └── session.py      # PostgreSQL 엔진 및 세션 설정
│   ├── models/             # SQLAlchemy DB 테이블 모델
│   ├── schemas/            # Pydantic 데이터 검증 모델 (Request/Response용)
│   ├── main.py             # FastAPI 앱 초기화 및 실행 (Entry Point)
│   └── tests/              # 유닛/통합 테스트
├── .dockerignore
├── .env                    # 로컬 개발용 환경변수
├── .gitignore
├── alembic.ini             # DB 마이그레이션 설정
├── Dockerfile              # 도커 이미지 정의
├── docker-compose.yml      # 배포 환경용 도커 컴포즈
├── docker-compose-dev.yml  # 로컬 개발 환경용 도커 컴포즈
└── requirements.txt        # 프로젝트 의존성 목록
```

## 🌐 API 구조

### Update Soon...

## 🎯 개발 및 데이터 지침

### Update soon...

### 사전 요구사항 (Prerequisites)

* **Python 3.11** 이상
* **Docker** (로컬 DB 및 배포 환경)
* **Git**
* **Update Soon...**

### 설치 및 로컬 세팅 (Installation)

1. 저장소 클론
```bash
# 저장소 클론
git clone https://github.com/Team-1AM-Club/Project_JIP-CHAK_BE.git

# 디렉토리 이동
cd Project_JIP-CHAK_BE
```
2. Update Soon...

### ⚙️ 설정 (.env)

**[배포 환경]**
운영 서버 배포 시에는 **GitHub Actions**가 **GitHub Secrets** 값을 이용하여 `.env` 파일을 자동으로 생성합니다.

**[로컬 개발 환경]**
로컬 개발 환경에서는 프로젝트 루트에 `.env` 파일을 직접 생성해야 합니다.

```ini
# Database Config
Update Soon...
```

### 🔄 CI/CD Pipeline

이 프로젝트는 **GitHub Actions**를 사용하여 자동 배포됩니다.

1. **Push**: `main` 브랜치에 코드가 푸시되면 워크플로우가 트리거됩니다.
2. **Build**: Docker 이미지를 빌드하고 Docker Hub에 업로드합니다.
3. **Deploy**:
* 운영 서버(GCP Instance)에 SSH로 접속합니다.
* GitHub Secrets에 저장된 환경 변수로 서버 내 `.env` 파일을 갱신합니다.
* 최신 Docker 이미지를 Pull 받아 컨테이너를 재시작합니다.

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
| 🐛 **버그 제보  기능 요청** | [**GitHub Issues**](../../issues) |
| 📧 **기타 문의사항** | [**team.1am.club@gmail.com**](mailto:team.1am.club@gmail.com) |

[![GitHub Issues](https://img.shields.io/badge/GitHub%20Issues-Bug%20Report%20%26%20Feature%20Request-green?style=for-the-badge&logo=github)](../../issues)
[![Email](https://img.shields.io/badge/Team%201AM%20Club-team.1am.club%40gmail.com-EA4335?style=for-the-badge&logo=gmail&logoColor=white)](mailto:team.1am.club@gmail.com)
