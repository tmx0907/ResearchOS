# ResearchOS

논문 관리 → 분석 → 쓰기까지 자동화하는 대학원생 연구 도구

## 설치

[설치 가이드](INSTALL.md) 참고

### 뉴비 3줄 설치
```bash
git clone https://github.com/tmx0907/ResearchOS.git ~/ResearchOS
cd ~/ResearchOS
bash scripts/setup_newbie.sh
```

## 배포 문서 (학생용)

- [학생 배포 PRD](PRD_STUDENT_DISTRIBUTION_KR.md)
- [MVP 배포 체크리스트](MVP_RELEASE_CHECKLIST_KR.md)
- [복제 설치 가이드](SHARE_SETUP_GUIDE_KR.md)

## 특징

- Zotero 자동 연동
- AI 분석 (선택)
- Obsidian 카드 시스템
- 진행도 추적
- 태그 기반 분류

## 사용법
```bash
cd ~/ResearchOS/scripts
python3 sync_and_analyze.py --write
python3 track_progress.py
```

## 라이선스

MIT
