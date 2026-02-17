#!/usr/bin/env python3
"""ResearchOS 카드 인덱스 생성기."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path

CARDS_DIR = Path.home() / "ResearchOS" / "02_cards_basic"
BASE_DIR = Path.home() / "ResearchOS"


def parse_frontmatter(path: Path) -> dict:
    content = path.read_text(encoding="utf-8", errors="replace")
    data = {"filename": path.stem, "title": path.stem, "tags": []}

    if not content.startswith("---"):
        return data

    parts = content.split("---", 2)
    if len(parts) < 3:
        return data

    fm_lines = parts[1].splitlines()

    in_tags = False
    for raw in fm_lines:
        line = raw.strip()
        if not line:
            continue

        if line == "tags:":
            in_tags = True
            continue

        if in_tags:
            if line.startswith("- "):
                data["tags"].append(line[2:].strip().strip('"').strip("'"))
                continue
            in_tags = False

        if line.startswith("#") or line.startswith("- "):
            continue

        if ":" in line:
            key, _, value = line.partition(":")
            data[key.strip()] = value.strip().strip('"').strip("'")

    return data


def priority_emoji(priority: str) -> str:
    return {
        "must-read": "🔴",
        "should-read": "🟡",
        "reference-only": "⚪",
        "to-read": "📘",
    }.get(priority, "📘")


def to_float(value: str | int | float | None) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def generate_master_index(cards: list[dict]) -> None:
    lines = [
        f"# 📚 마스터 인덱스 ({len(cards)}편)",
        "",
        f"> 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "| # | P | 제목 | 연도 | 방법론 | 관련성 |",
        "|---|---|------|------|--------|--------|",
    ]

    for i, card in enumerate(cards, 1):
        title = card.get("title", card["filename"])[:55]
        link = f"[[02_cards_basic/{card['filename']}|{title}]]"
        lines.append(
            f"| {i} | {priority_emoji(card.get('reading_priority', 'to-read'))} | {link} | "
            f"{card.get('year', '?')} | {card.get('method', '?')} | {card.get('relevance_score', '0')} |"
        )

    (BASE_DIR / "INDEX_MASTER.md").write_text("\n".join(lines), encoding="utf-8")


def generate_topic_index(cards: list[dict]) -> None:
    topic_map = defaultdict(list)
    for card in cards:
        for tag in card.get("tags", []):
            if tag.lower().startswith("topic:"):
                topic_map[tag.split(":", 1)[1].strip()].append(card)

    axes = {
        "🧠 Anxiety & Depression": ["anxiety", "depression", "mood", "cbt", "worry", "panic", "gad"],
        "🤖 AI & Existential": ["ai", "automation", "meaning", "purpose", "identity", "existential", "unemployment"],
        "🎨 Art & Mental Health": ["art", "therapy", "creative", "music", "expressive", "aesthetic", "flow"],
    }

    lines = ["# 🏷️ 주제별 인덱스", ""]
    used_topics = set()
    axis_fallback = {axis: [] for axis in axes}

    for axis, keywords in axes.items():
        # No topic tags: infer basic grouping from title/method text.
        for card in cards:
            haystack = " ".join(
                [
                    str(card.get("title", "")).lower(),
                    str(card.get("method", "")).lower(),
                    " ".join([t.lower() for t in card.get("tags", [])]),
                ]
            )
            if any(k in haystack for k in keywords):
                if card not in axis_fallback[axis]:
                    axis_fallback[axis].append(card)

        matches = {
            topic: topic_cards
            for topic, topic_cards in topic_map.items()
            if any(k in topic.lower() for k in keywords)
        }
        if not matches:
            continue

        lines.append(f"## {axis}")
        lines.append("")

        for topic, topic_cards in sorted(matches.items()):
            used_topics.add(topic)
            lines.append(f"### {topic} ({len(topic_cards)}편)")
            for card in sorted(topic_cards, key=lambda x: to_float(x.get("relevance_score")), reverse=True):
                lines.append(
                    f"- {priority_emoji(card.get('reading_priority', 'to-read'))} "
                    f"[[02_cards_basic/{card['filename']}|{card.get('title', card['filename'])[:60]}]]"
                )
            lines.append("")

    remaining = {topic: topic_cards for topic, topic_cards in topic_map.items() if topic not in used_topics}
    if remaining:
        lines.append("## 📂 Other")
        lines.append("")
        for topic, topic_cards in sorted(remaining.items()):
            lines.append(f"### {topic} ({len(topic_cards)}편)")
            for card in sorted(topic_cards, key=lambda x: to_float(x.get("relevance_score")), reverse=True):
                lines.append(f"- [[02_cards_basic/{card['filename']}|{card.get('title', card['filename'])[:60]}]]")
            lines.append("")

    if not topic_map:
        lines.append("## 자동 추론 분류 (topic 태그 없음)")
        lines.append("")
        for axis, inferred_cards in axis_fallback.items():
            if not inferred_cards:
                continue
            lines.append(f"### {axis} ({len(inferred_cards)}편)")
            for card in sorted(inferred_cards, key=lambda x: to_float(x.get("relevance_score")), reverse=True):
                lines.append(
                    f"- {priority_emoji(card.get('reading_priority', 'to-read'))} "
                    f"[[02_cards_basic/{card['filename']}|{card.get('title', card['filename'])[:60]}]]"
                )
            lines.append("")

    (BASE_DIR / "INDEX_TOPIC.md").write_text("\n".join(lines), encoding="utf-8")


def generate_priority_index(cards: list[dict]) -> None:
    grouped = defaultdict(list)
    for card in cards:
        grouped[card.get("reading_priority", "to-read")].append(card)

    lines = [
        "# 📖 읽기 우선순위",
        "",
        "| P | 편수 |",
        "|--|------|",
        f"| 🔴 Must | {len(grouped.get('must-read', []))} |",
        f"| 🟡 Should | {len(grouped.get('should-read', []))} |",
        f"| 📘 To-read | {len(grouped.get('to-read', []))} |",
        f"| ⚪ Ref | {len(grouped.get('reference-only', []))} |",
        "",
    ]

    for priority, emoji, label in [
        ("must-read", "🔴", "Must-Read"),
        ("should-read", "🟡", "Should-Read"),
        ("to-read", "📘", "To-Read"),
        ("reference-only", "⚪", "Reference-Only"),
    ]:
        items = sorted(grouped.get(priority, []), key=lambda x: to_float(x.get("relevance_score")), reverse=True)
        if not items:
            continue
        lines.append(f"## {emoji} {label}")
        lines.append("")
        for card in items:
            lines.append(
                f"- [ ] [[02_cards_basic/{card['filename']}|{card.get('title', card['filename'])[:60]}]] "
                f"({card.get('year', '?')})"
            )
        lines.append("")

    (BASE_DIR / "INDEX_PRIORITY.md").write_text("\n".join(lines), encoding="utf-8")


def generate_dataview() -> None:
    content = """# 📊 비교 테이블 (Dataview)

```dataview
TABLE year AS \"Year\", method AS \"Method\", measurement AS \"Tools\", sample_size AS \"N\", effect_size AS \"ES\", reading_priority AS \"P\", relevance_score AS \"Rel\"
FROM \"02_cards_basic\"
SORT relevance_score DESC
```

## 🔴 Must-Read

```dataview
TABLE year AS \"Year\", journal AS \"Journal\", method AS \"Method\"
FROM \"02_cards_basic\"
WHERE reading_priority = \"must-read\"
SORT relevance_score DESC
```
"""
    (BASE_DIR / "COMPARE_DATAVIEW.md").write_text(content, encoding="utf-8")


def main() -> None:
    cards = [parse_frontmatter(path) for path in sorted(CARDS_DIR.glob("*.md"))]

    if not cards:
        print("카드 없음")
        return

    cards = sorted(cards, key=lambda x: to_float(x.get("relevance_score")), reverse=True)

    generate_master_index(cards)
    generate_topic_index(cards)
    generate_priority_index(cards)
    generate_dataview()

    print(f"✅ INDEX_MASTER.md ({len(cards)}편)")
    print("✅ INDEX_TOPIC.md")
    print("✅ INDEX_PRIORITY.md")
    print("✅ COMPARE_DATAVIEW.md")


if __name__ == "__main__":
    main()
