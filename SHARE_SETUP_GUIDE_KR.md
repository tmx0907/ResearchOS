# ResearchOS 복제 설치 가이드 (공유용, 뉴비 레벨)

이 문서는 다른 사람이 **너와 똑같은 구조**로 ResearchOS를 만드는 방법입니다.

## 1) 준비물
- macOS 또는 Linux
- Python 3.9+
- Zotero 7 + Better BibTeX
- (선택) Obsidian + Dataview

## 2) 폴더 생성

```bash
mkdir -p ~/ResearchOS/{00_search_design/scopus_exports,01_zotero_export,02_cards_quick,03_cards_deep,04_index,06_thesis/sections,secrets,scripts,logs}
```

## 3) 환경변수 파일

```bash
cat > ~/ResearchOS/secrets/.env << 'ENVEND'
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
LLM_PROVIDER=claude
ENVEND
```

## 4) 패키지 설치

```bash
pip3 install --break-system-packages python-dotenv pyyaml tqdm pymupdf
# 선택(LLM 쓰려면)
pip3 install --break-system-packages anthropic openai
```

## 5) Zotero 자동 Export 설정
1. Zotero에서 `My Library` 우클릭 -> Export Library
2. Format: `Better CSL JSON`
3. 저장 위치: `~/ResearchOS/01_zotero_export/library.json`
4. `Keep updated` 체크

## 6) 스크립트 복사
아래 파일들을 공유 받아서 `~/ResearchOS/scripts/`에 넣는다.
- `sync_and_analyze.py`
- `generate_index.py`
- `ai_screener.py`
- `citation_paragraph_builder.py`
- `health_check.sh`
- `reddit_pain_scraper.py` (선택)

실행권한 부여:

```bash
chmod +x ~/ResearchOS/scripts/*.py ~/ResearchOS/scripts/*.sh
```

## 7) 초기 점검

```bash
cd ~/ResearchOS/scripts
bash health_check.sh
```

## 8) 첫 실행 (MVP)

```bash
# 1) Zotero에서 논문 3~5개 저장 후
python3 sync_and_analyze.py --write

# 2) 인덱스 생성
python3 generate_index.py

# 3) 문단 초안 생성
python3 citation_paragraph_builder.py \
  --focus "anxiety,depression,meaning,purpose,art therapy" \
  --max 10 \
  --section pilot
```

## 9) 결과물 확인 위치
- 카드: `~/ResearchOS/02_cards_quick/`
- 인덱스: `~/ResearchOS/INDEX_MASTER.md`, `~/ResearchOS/INDEX_TOPIC.md`, `~/ResearchOS/INDEX_PRIORITY.md`
- 문단 초안: `~/ResearchOS/06_thesis/sections/PARAGRAPH_BANK_*.md`
- 인용 추적표: `~/ResearchOS/06_thesis/CITATION_TRACE_*.csv`

## 10) 팀/지인 공유 팁
- `.env`, `secrets/`, `logs/`는 공유하지 않기
- 스크립트와 템플릿 파일만 공유
- 버전 꼬임 방지를 위해 같은 Python 버전(3.9+) 권장

## 11) 권장 `.gitignore`

```gitignore
secrets/
*.env
__pycache__/
logs/
```

