# ResearchOS 복제 설치 가이드 (공유용, 뉴비 레벨)

이 문서는 다른 사람이 너와 같은 ResearchOS를 재현하는 최소 절차입니다.

## 1) 공유할 것
- GitHub 저장소 링크: `https://github.com/tmx0907/ResearchOS`
- 문서: `INSTALL.md`, `README_NEWBIE_KR.md`
- 안내 문구: "clone 후 `bash scripts/setup_newbie.sh` 실행"

## 2) 공유하지 말 것
- `secrets/`, `*.env`, `logs/`
- 개인 Zotero 내보내기 원본 JSON
- 개인 카드/논문 메모 원본 (필요 시 샘플만 별도 제공)

## 3) 학생 설치 명령 (복붙)

```bash
git clone https://github.com/tmx0907/ResearchOS.git ~/ResearchOS
cd ~/ResearchOS
bash scripts/setup_newbie.sh
```

## 4) Zotero 자동 Export 설정 (수동 1회)
1. Zotero에서 `My Library` 우클릭 -> Export Library
2. Format: `Better CSL JSON`
3. 저장 위치: `~/ResearchOS/01_zotero_export/library.json`
4. `Keep updated` 체크

## 5) 첫 실행 (MVP)

```bash
cd ~/ResearchOS/scripts
python3 sync_and_analyze.py --write
python3 generate_index.py
```

## 6) 결과물 확인 위치
- 카드: `~/ResearchOS/02_cards_basic/`
- 인덱스: `~/ResearchOS/INDEX_MASTER.md`, `~/ResearchOS/INDEX_TOPIC.md`, `~/ResearchOS/INDEX_PRIORITY.md`
- 문단 초안(선택): `~/ResearchOS/06_thesis/sections/`

## 7) 운영 팁
- 설치 테스트를 학생 3명에게 먼저 수행해서 공통 오류를 수집
- 오류 리포트는 "OS / Python 버전 / 실행 명령 / 에러로그" 4개를 필수로 받기
- 변경사항이 생기면 `README.md`와 `INSTALL.md`를 같이 업데이트
