"""
ResearchOS → thesis-coach 자동 연동 스크립트
- library.json에서 새 논문을 읽어 thesis-coach API로 전송
- thesis-coach가 꺼져있으면 조용히 스킵
"""

import json, os, sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError

# ── 설정 ────────────────────────────────────────────────────
BASE_DIR = Path.home() / "ResearchOS"
LIBRARY_JSON = BASE_DIR / "01_zotero_export" / "library.json"
STATE_FILE = BASE_DIR / "logs" / ".state" / "thesis_coach_synced.json"

THESIS_COACH_URL = "http://localhost:3001/api"
USER_ID = "00000000-0000-0000-0000-000000000001"  # demo user
TIMEOUT = 3  # seconds


def load_synced_keys():
    """이미 보낸 논문 키 목록 로드"""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            return set(json.load(f).get("synced_keys", []))
    return set()


def save_synced_keys(keys):
    """보낸 논문 키 목록 저장"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump({"synced_keys": sorted(keys)}, f, indent=2)


def health_check():
    """thesis-coach가 살아있는지 확인"""
    try:
        req = Request(f"{THESIS_COACH_URL}/../health")
        urlopen(req, timeout=TIMEOUT)
        return True
    except Exception:
        # /health가 없으면 papers 목록으로 확인
        try:
            req = Request(f"{THESIS_COACH_URL}/papers")
            req.add_header("x-user-id", USER_ID)
            urlopen(req, timeout=TIMEOUT)
            return True
        except Exception:
            return False


def register_paper(item):
    """논문 1개를 thesis-coach에 등록"""
    # 저자 추출
    authors = ""
    if "author" in item:
        names = []
        for a in item["author"]:
            name = f"{a.get('family', '')} {a.get('given', '')}".strip()
            if name:
                names.append(name)
        authors = ", ".join(names)

    # 연도 추출
    year = None
    if "issued" in item and "date-parts" in item["issued"]:
        parts = item["issued"]["date-parts"]
        if parts and parts[0]:
            year = parts[0][0]

    payload = {
        "title": item.get("title", "Untitled"),
        "authors": authors,
        "year": year,
        "journal": item.get("container-title", ""),
        "doi": item.get("DOI", ""),
        "abstract": item.get("abstract", ""),
        "zotero_key": item.get("id", ""),
    }

    data = json.dumps(payload).encode("utf-8")
    req = Request(
        f"{THESIS_COACH_URL}/papers/register-meta",
        data=data,
        method="POST",
    )
    req.add_header("Content-Type", "application/json")
    req.add_header("x-user-id", USER_ID)

    resp = urlopen(req, timeout=TIMEOUT)
    return json.loads(resp.read().decode("utf-8"))


def main():
    # 1) thesis-coach 살아있는지 확인
    if not health_check():
        print("⏭️  thesis-coach 미실행 → 스킵")
        return

    # 2) library.json 읽기
    if not LIBRARY_JSON.exists():
        print(f"❌ {LIBRARY_JSON} 없음")
        return

    with open(LIBRARY_JSON, "r", encoding="utf-8") as f:
        items = json.load(f)

    # 3) 이미 보낸 논문 확인
    synced = load_synced_keys()
    new_items = [item for item in items if item.get("id", "") not in synced]

    if not new_items:
        print(f"📋 thesis-coach: 새 논문 없음 (전체 {len(items)}편 동기화 완료)")
        return

    # 4) 새 논문 전송
    success = 0
    for item in new_items:
        key = item.get("id", "")
        title = item.get("title", "Untitled")
        try:
            result = register_paper(item)
            status = result.get("status", "unknown")
            synced.add(key)
            success += 1
            print(f"  ✅ [{status}] {title[:50]}")
        except Exception as e:
            print(f"  ❌ {title[:50]}: {e}")

    # 5) 상태 저장
    save_synced_keys(synced)
    print(f"🔗 thesis-coach: {success}/{len(new_items)}편 연동 완료")


if __name__ == "__main__":
    main()
