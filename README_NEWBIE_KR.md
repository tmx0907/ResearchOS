# ResearchOS 뉴비 사용법 (한국어)

이 문서는 **심리학 대학원생 기준**으로, 논문 수집부터 카드 생성, 인덱스 정리, 문단 초안까지 빠르게 쓰는 방법입니다.

## 0) 한 줄 요약
1. Zotero에 논문 넣기
2. `sync_and_analyze.py` 실행해서 카드 만들기
3. `generate_index.py` 실행해서 인덱스 갱신
4. `citation_paragraph_builder.py` 실행해서 문단 초안 + 인용 매칭 만들기

---

## 1) 오늘 바로 쓰는 최소 루틴 (5~10분)

터미널에서 아래 순서로 실행:

```bash
cd ~/ResearchOS/scripts

# 상태 점검
bash health_check.sh

# Zotero -> 카드 생성 (메타데이터 모드, 무료)
python3 sync_and_analyze.py --write

# 인덱스 갱신
python3 generate_index.py

# 내 논문용 문단 초안 + citation trace 생성
python3 citation_paragraph_builder.py \
  --focus "meaning,purpose,depression,art therapy" \
  --max 15 \
  --section lit_review_rq1
```

생성 결과:
- 카드: `~/ResearchOS/02_cards_basic/`
- 인덱스: `~/ResearchOS/INDEX_MASTER.md` 등
- 문단 초안: `~/ResearchOS/06_thesis/sections/`
- 인용 추적 CSV: `~/ResearchOS/06_thesis/`

---

## 2) AI 스크리닝(대량 검색 결과 정리)

Scopus CSV를 받은 뒤:

```bash
python3 ~/ResearchOS/scripts/ai_screener.py \
  ~/ResearchOS/00_search_design/scopus_exports/your_export.csv \
  --write
```

- LLM SDK가 없으면 자동으로 **룰베이스 스크리닝**으로 동작합니다.
- 결과 파일은 `/Users/jungeunkim/ResearchOS/00_search_design/`에 저장됩니다.

---

## 3) 자주 막히는 포인트

### Q1. `anthropic/openai 없음` 경고가 떠요
정상입니다. 지금은 메타데이터/룰베이스 모드로 돌아갑니다.

### Q2. 카드가 안 생겨요
이미 같은 제목 카드가 있으면 새로 안 만듭니다. Zotero에 새 논문 추가 후 다시 실행하세요.

### Q3. 문단 초안은 그대로 제출해도 되나요?
아니요. 반드시 원문 PDF 확인 후 숫자/효과크기/방향을 검증해서 수정하세요.

---

## 4) 추천 주간 루틴

- 매일 20~30분
  - Zotero 저장
  - `sync_and_analyze.py --write`
  - `generate_index.py`
- 주 1회
  - Scopus CSV export
  - `ai_screener.py ... --write`
  - High/Medium만 Zotero 반영
