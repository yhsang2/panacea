# CareGuide – Medical Triage PoC

## 포함 기능
- Rule-based Triage (규칙 기반) + **Rule weight / confidence score**
- PubMed RAG (PoC용 Mock 데이터) 기반 참고 문헌 노출
- 모바일 PoC UI (frontend/index.html)

## 실행 방법

### 1) Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

- API 문서: http://127.0.0.1:8000/docs

### 2) Frontend
`frontend/index.html` 파일을 브라우저(또는 iOS WebView)에서 여세요.

## 응답 필드
- `confidence`: 0~1 범위의 **휴리스틱 신뢰 지표** (진단 확률 아님)
- `confidence_label`: 높음/중간/낮음
- `rule_id`: 적용된 규칙 ID
- `evidence`: 키워드 매칭 근거
- `candidates`: (옵션) 후보 규칙 목록 (의료진 모드에 활용)

## 주의
본 프로젝트는 의료 진단/처방을 제공하지 않습니다.
