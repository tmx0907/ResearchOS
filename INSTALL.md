# ResearchOS 설치 가이드 (뉴비용)

이 문서는 "처음 설치하는 사람" 기준입니다.

## 1) 준비물
- macOS 또는 Linux
- Python 3.9+
- Zotero 7 + Better BibTeX
- (선택) Obsidian

## 2) 설치 (복붙)

```bash
git clone https://github.com/tmx0907/ResearchOS.git ~/ResearchOS
cd ~/ResearchOS
bash scripts/setup_newbie.sh
```

위 스크립트가 자동으로 처리하는 것:
- `~/ResearchOS` 경로 정렬
- 필수 폴더 생성
- `secrets/.env` 기본 파일 생성
- 필수 Python 패키지 설치
- `health_check.sh` 실행

## 3) Zotero 연결 (수동 1회)
1. Zotero에서 `My Library` 우클릭 -> Export Library
2. Format: `Better CSL JSON`
3. 파일 경로: `~/ResearchOS/01_zotero_export/library.json`
4. `Keep updated` 체크

## 4) 첫 실행

```bash
cd ~/ResearchOS/scripts
python3 sync_and_analyze.py --write
python3 generate_index.py
```

## 5) 결과 확인
- 카드: `~/ResearchOS/02_cards_basic/`
- 인덱스: `~/ResearchOS/INDEX_MASTER.md`

## 6) 자주 막히는 경우
- `library.json 없음`:
  Zotero export 경로가 다르면 안 돌아갑니다. 경로를 정확히 확인하세요.
- `패키지 설치 실패`:
  아래를 다시 실행하세요.
  `python3 -m pip install --user python-dotenv pyyaml tqdm pymupdf`
- `경로 꼬임`:
  `ls -ld ~/ResearchOS`로 확인하고, 다른 폴더를 가리키면 symlink를 정리하세요.
