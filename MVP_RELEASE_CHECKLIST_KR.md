# ResearchOS 학생 배포 MVP 체크리스트

## 0) 배포 목표
"처음 보는 학생이 30분 안에 Zotero -> Obsidian 카드 자동화를 성공"하면 MVP 성공.

## 1) 배포 전 준비 (Maintainer)
- [ ] `README.md` 최신 명령 반영
- [ ] `README_NEWBIE_KR.md` 경로/폴더명 점검
- [ ] `SHARE_SETUP_GUIDE_KR.md`대로 새 환경에서 재현 테스트
- [ ] `.gitignore`에 `secrets/`, `logs/`, `*.env` 포함 확인
- [ ] 샘플 데이터 없이도 health check가 이해 가능한 메시지 출력

## 2) 사용자 온보딩 최소 플로우
1. 저장소 clone
2. `~/ResearchOS` 경로 맞춤 (필요시 symlink)
3. Python 패키지 설치
4. Zotero Better BibTeX export 경로 설정
5. 아래 명령 실행

```bash
cd ~/ResearchOS/scripts
bash health_check.sh
python3 sync_and_analyze.py --write
python3 generate_index.py
```

## 3) 합격 기준 (Acceptance Criteria)
- [ ] `health_check.sh`에서 치명 오류 없이 다음 단계 안내
- [ ] `02_cards_basic`에 카드 파일 1개 이상 생성
- [ ] `INDEX_MASTER.md` 갱신 시간 최신
- [ ] Obsidian에서 카드/인덱스 열람 가능

## 4) 실패 시 트러블슈팅 표준
- 증상: 카드 미생성
  - 조치: Zotero export 파일(`01_zotero_export/library.json`) 갱신 확인
- 증상: 경로 에러
  - 조치: `~/ResearchOS` 경로 여부 확인 또는 symlink 적용
- 증상: AI 모드 에러
  - 조치: `--ai` 없이 메타데이터 모드로 먼저 성공

## 5) 배포 패키지 권장 구성
- 필수 포함
  - `scripts/` 주요 스크립트
  - `README.md`, `README_NEWBIE_KR.md`, `SHARE_SETUP_GUIDE_KR.md`
- 제외
  - `secrets/`, `logs/`, 개인 Zotero export 원본

## 6) 첫 배포 운영 규칙
- 주 1회 문서/스크립트 동기화 릴리즈
- 이슈 템플릿: "OS/파이썬 버전/에러로그/실행 명령" 필수
- Breaking change는 README 상단에 굵게 공지

## 7) 추천 출시 순서
1. 3명 파일럿 사용자에게 설치 테스트
2. 공통 실패 3개 해결
3. GitHub 공개 + 설치 영상/스크린샷 추가
4. 학교 커뮤니티 배포

## 8) 배포 공지 템플릿 (복붙용)
"Zotero에 논문 넣으면 Obsidian 연구카드가 자동 생성되는 ResearchOS를 공개했습니다.
초보자 기준 설치 30분, 첫 실행 5분 루틴입니다.
설치: README_NEWBIE_KR.md / 복제 설치: SHARE_SETUP_GUIDE_KR.md"
