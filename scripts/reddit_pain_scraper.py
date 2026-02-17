#!/usr/bin/env python3
"""Reddit 대학원생 고충 스크래핑 + pain point 분류.

사용 예시:
  python3 reddit_pain_scraper.py --write
  python3 reddit_pain_scraper.py --subreddits GradSchool,PhD,AskAcademia --queries "literature review,citation manager,paraphrasing" --write
"""

from __future__ import annotations

import argparse
import json
import re
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

BASE_DIR = Path.home() / "ResearchOS"
OUTPUT_DIR = BASE_DIR / "00_search_design"

DEFAULT_SUBREDDITS = ["GradSchool", "PhD", "AskAcademia"]
DEFAULT_QUERIES = [
    "literature review overwhelmed",
    "citation manager dissertation",
    "paraphrasing sources thesis",
    "writing stuck thesis",
]

PAIN_RULES = {
    "citation_management": ["citation", "zotero", "mendeley", "endnote", "reference", "bib"],
    "reading_overload": ["overwhelmed", "too many papers", "50 tabs", "can't keep up", "stuck reading"],
    "paraphrase_synthesis": ["paraphrase", "synthesis", "summarize", "rewrite", "my own words"],
    "writing_block": ["stuck", "can't write", "writer", "blank page", "procrast"],
    "workflow_system": ["workflow", "system", "organize", "folder", "tag", "note"],
}


def fetch_reddit_search(subreddit: str, query: str, limit: int = 25) -> list[dict]:
    encoded_q = quote_plus(query)
    url = (
        f"https://www.reddit.com/r/{subreddit}/search.json"
        f"?q={encoded_q}&restrict_sr=1&sort=top&t=year&limit={limit}"
    )

    req = Request(url, headers={"User-Agent": "ResearchOS/0.1 (by /u/researchos-bot)"})
    with urlopen(req, timeout=20) as res:
        payload = json.loads(res.read().decode("utf-8"))

    posts = []
    for child in payload.get("data", {}).get("children", []):
        d = child.get("data", {})
        posts.append(
            {
                "subreddit": subreddit,
                "query": query,
                "id": d.get("id", ""),
                "title": d.get("title", "").strip(),
                "selftext": (d.get("selftext", "") or "").strip(),
                "permalink": f"https://www.reddit.com{d.get('permalink', '')}",
                "score": d.get("score", 0),
                "num_comments": d.get("num_comments", 0),
                "created_utc": d.get("created_utc", 0),
            }
        )
    return posts


def classify_post(post: dict) -> list[str]:
    text = f"{post.get('title', '')} {post.get('selftext', '')}".lower()
    labels = []
    for label, keywords in PAIN_RULES.items():
        if any(k in text for k in keywords):
            labels.append(label)
    return labels or ["uncategorized"]


def summarize_pains(posts: list[dict]) -> tuple[Counter, dict[str, list[dict]]]:
    counter = Counter()
    grouped = defaultdict(list)

    for post in posts:
        labels = classify_post(post)
        post["pain_labels"] = labels
        for label in labels:
            counter[label] += 1
            grouped[label].append(post)

    return counter, grouped


def dedupe_posts(posts: list[dict]) -> list[dict]:
    seen = set()
    deduped = []
    for p in posts:
        pid = p.get("id") or p.get("permalink")
        if pid in seen:
            continue
        seen.add(pid)
        deduped.append(p)
    return deduped


def create_markdown_report(posts: list[dict], counter: Counter, grouped: dict[str, list[dict]]) -> str:
    lines = [
        "# Reddit 대학원생 고충 리포트",
        "",
        f"> 생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"> 수집 포스트: {len(posts)}개",
        "",
        "## Pain Point 분포",
        "",
        "| category | count |",
        "|---|---:|",
    ]

    for label, cnt in counter.most_common():
        lines.append(f"| {label} | {cnt} |")

    lines.append("")
    lines.append("## 카테고리별 상위 포스트")
    lines.append("")

    for label, _ in counter.most_common():
        lines.append(f"### {label}")
        top_posts = sorted(grouped[label], key=lambda x: (x.get("score", 0), x.get("num_comments", 0)), reverse=True)[:5]
        for p in top_posts:
            snippet = re.sub(r"\s+", " ", p.get("selftext", ""))[:180]
            lines.append(
                f"- [{p.get('title', '(제목 없음)')}]({p.get('permalink')}) "
                f"(r/{p.get('subreddit')} | score {p.get('score', 0)} | comments {p.get('num_comments', 0)})"
            )
            if snippet:
                lines.append(f"  - snippet: {snippet}")
        lines.append("")

    lines.append("## ResearchOS 반영 제안")
    lines.append("")
    lines.append("- citation_management: 문단 초안 생성 시 `citation trace CSV`를 기본 생성하고, 카드별 zotero_key 누락 검사 추가")
    lines.append("- reading_overload: weekly 스크리닝 배치(20~30편)와 `high/medium` 컷오프를 고정하여 읽기 큐 제한")
    lines.append("- paraphrase_synthesis: 섹션별 paragraph bank를 먼저 만든 뒤, 문장 단위가 아니라 claim 단위로 통합")
    lines.append("- writing_block: `must-read 5편`만으로 섹션 초안 1차 생성하는 low-friction 모드 유지")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Reddit 고충 스크래핑")
    parser.add_argument("--subreddits", default=",".join(DEFAULT_SUBREDDITS))
    parser.add_argument("--queries", default=",".join(DEFAULT_QUERIES))
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    subreddits = [x.strip() for x in args.subreddits.split(",") if x.strip()]
    queries = [x.strip() for x in args.queries.split(",") if x.strip()]

    all_posts = []
    for sub in subreddits:
        for query in queries:
            try:
                posts = fetch_reddit_search(sub, query, limit=args.limit)
                all_posts.extend(posts)
                print(f"✅ r/{sub} | '{query}' | {len(posts)}개")
                time.sleep(1)
            except Exception as exc:
                print(f"⚠️ r/{sub} | '{query}' 실패: {exc}")

    all_posts = dedupe_posts(all_posts)
    counter, grouped = summarize_pains(all_posts)

    print("\n=== 요약 ===")
    print(f"포스트 수: {len(all_posts)}")
    for label, cnt in counter.most_common():
        print(f"- {label}: {cnt}")

    if args.write:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        json_path = OUTPUT_DIR / f"reddit_pain_posts_{ts}.json"
        md_path = OUTPUT_DIR / f"reddit_pain_report_{ts}.md"

        json_path.write_text(json.dumps(all_posts, ensure_ascii=False, indent=2), encoding="utf-8")
        md_path.write_text(create_markdown_report(all_posts, counter, grouped), encoding="utf-8")

        print(f"✅ 저장: {json_path}")
        print(f"✅ 저장: {md_path}")


if __name__ == "__main__":
    main()
