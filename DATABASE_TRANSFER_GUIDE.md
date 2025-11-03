# 데이터베이스 전달 가이드

## 1. 데이터베이스 덤프 생성 (이미 완료됨)

```bash
# 덤프 파일 생성
docker exec pgvec pg_dump -U postgres cosmetic_reviews > cosmetic_reviews_backup.sql

# 압축 (선택사항 - 전송 시간 단축)
gzip cosmetic_reviews_backup.sql
```

현재 생성된 파일: `cosmetic_reviews_backup.sql` (4.2GB)

---

## 2. 팀원에게 전달 방법

### 옵션 A: 클라우드 스토리지 (권장)
- Google Drive, Dropbox, OneDrive 등에 업로드
- 링크를 팀원에게 공유

### 옵션 B: 직접 파일 전송
- USB 드라이브
- 네트워크 공유 폴더

### 옵션 C: 원격 서버
```bash
# SCP로 전송
scp cosmetic_reviews_backup.sql user@server:/path/to/destination/
```

---

## 3. 팀원이 데이터베이스 복원하는 방법

### Step 1: Docker 컨테이너 실행

```bash
# pgvector 이미지로 PostgreSQL 컨테이너 실행
docker run -d \
  --name pgvec \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=postgres \
  -v pgvector_data:/var/lib/postgresql/data \
  ankane/pgvector
```

### Step 2: 데이터베이스 생성

```bash
# 컨테이너에 접속
docker exec -it pgvec psql -U postgres

# PostgreSQL에서 실행
CREATE DATABASE cosmetic_reviews;
\q
```

### Step 3: 덤프 파일 복원

```bash
# 압축된 경우 먼저 압축 해제
gunzip cosmetic_reviews_backup.sql.gz

# 덤프 파일 복원 (시간이 걸릴 수 있음)
docker exec -i pgvec psql -U postgres cosmetic_reviews < cosmetic_reviews_backup.sql
```

### Step 4: 복원 확인

```bash
docker exec -it pgvec psql -U postgres cosmetic_reviews

# PostgreSQL에서 실행
\dt  -- 테이블 목록 확인
SELECT COUNT(*) FROM reviews;  -- 데이터 개수 확인
\q
```

---

## 4. 환경 설정

팀원은 프로젝트 루트에 `.env` 파일을 생성하거나 `dashboard/.streamlit/secrets.toml`을 설정해야 합니다:

### `.env` 파일 예시:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=cosmetic_reviews
DB_USER=postgres
DB_PASSWORD=postgres

OPENAI_API_KEY=your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_API_KEY=your-google-api-key
```

### `dashboard/.streamlit/secrets.toml` 예시:
```toml
GEMINI_API_KEY = "your-gemini-api-key"
GOOGLE_API_KEY = "your-google-api-key"
```

---

## 5. 프로젝트 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# Streamlit 대시보드 실행
cd dashboard
streamlit run main.py
```

---

## 트러블슈팅

### 문제: 포트 충돌
```bash
# 다른 포트 사용
docker run -d --name pgvec -p 5433:5432 ... ankane/pgvector
```

### 문제: 메모리 부족
- 대용량 덤프 파일의 경우 분할 복원 필요
- Docker Desktop 메모리 설정 증가 (8GB 이상 권장)

### 문제: pgvector 확장 오류
```sql
-- PostgreSQL에서 실행
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## 참고사항

- 백업 파일 크기: 4.2GB
- 예상 복원 시간: 10-30분 (시스템 사양에 따라)
- 필요한 디스크 공간: 최소 15GB (데이터 + 인덱스)
