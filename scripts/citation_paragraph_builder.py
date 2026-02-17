#!/usr/bin/env python3
"""카드에서 Lit Review용 문단 초안 + 인용 매칭 파일 생성."""

from __future__ import annotations

import argparse
import csv
import re
from datetime import datetime
from pathlib import Path

BASE_DIR = Path.home() / "ResearchOS"
CARDS_DIR = BASE_DIR / "02_cards_basic"
SECTIONS_DIR = BASE_DIR / "06_thesis" / "sections"


def parse_frontmatter(content: str) -> dict:
    data = {"authors_list": []}
    if not content.startswith("---"):
        return data
    parts = content.split("---", 2)
    if len(parts) < 3:
        return data

    fm_lines = parts[1].splitlines()
    in_tags = False
    in_authors = False
    tags = []
    for raw in fm_lines:
        line = raw.strip()
        if not line:
            continue

        if line == "authors:":
            in_authors = True
            continue

        if in_authors:
            if line.startswith("- "):
                data["authors_list"].append(line[2:].strip().strip('"').strip("'"))
                continue
            in_authors = False

        if line == "tags:":
            in_tags = True
            continue

        if in_tags:
            if line.startswith("- "):
                tags.append(line[2:].strip().strip('"').strip("'"))
                continue
            in_tags = False

        if ":" in line and not line.startswith("#") and not line.startswith("-"):
            key, _, value = line.partition(":")
            data[key.strip()] = value.strip().strip('"').strip("'")

    data["tags"] = tags
    return data


def extract_section_text(content: str, heading: str) -> str:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(content)
    if not match:
        return ""

    start = match.end()
    rest = content[start:]
    next_heading = re.search(r"\n##\s+", rest)
    if next_heading:
        rest = rest[: next_heading.start()]
    return rest.strip()


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    return [p.strip() for p in parts if len(p.strip()) >= 35]


def sentence_score(sentence: str, focus_terms: list[str]) -> float:
    s = sentence.lower()
    score = 0.0

    evidence_terms = [
        "meta-analysis", "systematic review", "randomized", "rct", "effect", "95% ci", "odds ratio", "n=", "sample",
    ]
    score += sum(1.0 for term in evidence_terms if term in s)

    score += sum(1.5 for term in focus_terms if term and term in s)

    if any(ch.isdigit() for ch in sentence):
        score += 0.5

    return score


def pick_evidence_sentences(abstract: str, focus_terms: list[str], max_sentences: int = 2) -> list[str]:
    sentences = split_sentences(abstract)
    ranked = sorted(sentences, key=lambda x: sentence_score(x, focus_terms), reverse=True)
    return ranked[:max_sentences]


def first_author(authors_raw: str) -> str:
    if not authors_raw:
        return "Unknown"
    first = authors_raw.split(";")[0].strip()
    if "," in first:
        return first.split(",", 1)[0].strip()
    if " " in first:
        return first.split(" ")[-1].strip()
    return first


def first_author_from_list(authors_list: list[str]) -> str:
    if not authors_list:
        return "Unknown"
    first = authors_list[0].strip()
    if "," in first:
        return first.split(",", 1)[0].strip()
    if " " in first:
        return first.split(" ")[-1].strip()
    return first


def format_author_apa(author: str) -> str:
    # Input examples: "Cuijpers, Pim", "Pim Cuijpers"
    author = author.strip()
    if not author:
        return ""
    if "," in author:
        family, given = [x.strip() for x in author.split(",", 1)]
    else:
        parts = author.split()
        if len(parts) == 1:
            return parts[0]
        family = parts[-1]
        given = " ".join(parts[:-1])

    initials = []
    for token in re.split(r"[\s\-]+", given):
        token = token.strip()
        if not token:
            continue
        initials.append(f"{token[0].upper()}.")
    if initials:
        return f"{family}, {' '.join(initials)}"
    return family


def format_authors_apa(authors_list: list[str]) -> str:
    formatted = [format_author_apa(a) for a in authors_list if a.strip()]
    formatted = [a for a in formatted if a]
    if not formatted:
        return "Unknown"
    if len(formatted) == 1:
        return formatted[0]
    if len(formatted) == 2:
        return f"{formatted[0]}, & {formatted[1]}"
    return f"{', '.join(formatted[:-1])}, & {formatted[-1]}"


def format_apa_reference(card: dict) -> str:
    authors = format_authors_apa(card.get("authors_list", []))
    year = card.get("year", "n.d.")
    title = card.get("title", "").strip() or "Untitled"
    journal = card.get("journal", "").strip()
    volume = card.get("volume", "").strip()
    issue = card.get("issue", "").strip()
    pages = card.get("pages", "").strip()
    doi = card.get("doi", "").strip()

    ref = f"{authors} ({year}). {title}."

    journal_part = ""
    if journal:
        journal_part = journal
        if volume:
            journal_part += f", {volume}"
            if issue:
                journal_part += f"({issue})"
        if pages:
            journal_part += f", {pages}"
        journal_part += "."

    if journal_part:
        ref += f" {journal_part}"
    if doi:
        ref += f" https://doi.org/{doi}" if not doi.startswith("http") else f" {doi}"
    return ref


def build_claim_template(title: str, evidence: list[str]) -> str:
    if not evidence:
        return f"선행연구는 {title}에서 다룬 주제가 정신건강 결과와 유의하게 연결될 수 있음을 시사했다."

    key = evidence[0]
    if "meta-analysis" in key.lower() or "systematic" in key.lower():
        return "메타분석/체계적 문헌고찰 근거를 보면 해당 변인은 우울·불안 관련 결과와 일관된 연관을 보인다."
    if "random" in key.lower() or "rct" in key.lower():
        return "실험 연구 근거에서 해당 개입이 정신건강 지표를 개선할 가능성이 보고되었다."
    return "선행연구 결과를 종합하면 해당 변인은 정신건강 결과에 의미 있는 설명력을 가진다."


def load_cards() -> list[dict]:
    cards = []
    for path in sorted(CARDS_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(content)
        abstract = extract_section_text(content, "Abstract")
        cards.append(
            {
                "path": path,
                "title": fm.get("title", path.stem),
                "year": fm.get("year", "n.d."),
                "authors": fm.get("authors", ""),
                "authors_list": fm.get("authors_list", []),
                "zotero_key": fm.get("zotero_key", ""),
                "doi": fm.get("DOI", fm.get("doi", "")),
                "journal": fm.get("journal", ""),
                "volume": fm.get("volume", ""),
                "issue": fm.get("issue", ""),
                "pages": fm.get("page", fm.get("pages", "")),
                "priority": fm.get("reading_priority", "to-read"),
                "relevance": float(fm.get("relevance_score", 0) or 0),
                "abstract": abstract,
                "tags": fm.get("tags", []),
            }
        )
    return cards


def parse_focus_terms(raw: str) -> list[str]:
    if not raw:
        return []
    return [x.strip().lower() for x in raw.split(",") if x.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="문단 초안 + 인용 매칭 생성")
    parser.add_argument("--focus", default="", help="쉼표로 구분한 초점 키워드 (예: meaning,purpose,art therapy)")
    parser.add_argument("--max", type=int, default=12, help="생성할 최대 문단 개수")
    parser.add_argument("--section", default="lit_review", help="출력 파일 섹션 이름")
    parser.add_argument("--min-relevance", type=float, default=0.0, help="최소 relevance 점수")
    args = parser.parse_args()

    focus_terms = parse_focus_terms(args.focus)
    cards = load_cards()
    if not cards:
        print("❌ 카드가 없습니다. 먼저 sync_and_analyze.py를 실행하세요.")
        return

    cards = [c for c in cards if c["relevance"] >= args.min_relevance]
    cards = sorted(cards, key=lambda x: (x["priority"] == "must-read", x["relevance"]), reverse=True)

    selected = []
    for card in cards:
        evidence = pick_evidence_sentences(card["abstract"], focus_terms)
        if not evidence and not card["abstract"]:
            continue
        selected.append((card, evidence))
        if len(selected) >= args.max:
            break

    if not selected:
        print("❌ 조건에 맞는 카드가 없습니다. --min-relevance 값을 낮춰보세요.")
        return

    SECTIONS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    md_path = SECTIONS_DIR / f"PARAGRAPH_BANK_{args.section}_{timestamp}.md"
    csv_path = BASE_DIR / "06_thesis" / f"CITATION_TRACE_{args.section}_{timestamp}.csv"

    md_lines = [
        f"# Paragraph Bank ({args.section})",
        "",
        f"> 생성시각: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"> focus terms: {', '.join(focus_terms) if focus_terms else '(none)'}",
        "",
        "아래 문단은 초안이다. 원문/PDF를 확인한 뒤 최종 문장으로 확정하세요.",
        "",
    ]

    csv_rows = []

    for idx, (card, evidence) in enumerate(selected, 1):
        author = first_author_from_list(card["authors_list"])
        if author == "Unknown":
            author = first_author(card["authors"])
        citation = f"[@{card['zotero_key']}]" if card["zotero_key"] else f"({author}, {card['year']})"
        apa_reference = format_apa_reference(card)
        claim = build_claim_template(card["title"], evidence)

        paragraph = (
            f"{claim} 특히 {author} ({card['year']})의 결과는 해당 메커니즘이 "
            f"정신건강 지표와 연결될 수 있음을 보여준다 {citation}."
        )

        md_lines.append(f"## {idx}. {card['title']}")
        md_lines.append("")
        md_lines.append(f"- Draft Paragraph: {paragraph}")
        md_lines.append(f"- Citation: {citation}")
        md_lines.append(f"- APA Reference: {apa_reference}")
        if card["doi"]:
            md_lines.append(f"- DOI: https://doi.org/{card['doi']}")
        md_lines.append(f"- Source Card: [[02_cards_basic/{card['path'].stem}]]")
        md_lines.append("- Evidence Snippets:")
        if evidence:
            for ev in evidence:
                md_lines.append(f"  - {ev}")
        else:
            md_lines.append("  - (Abstract 없음: 카드 본문 메모 확인 필요)")
        md_lines.append("- Verification: 숫자/효과크기/방향성 원문 확인 필요")
        md_lines.append("")

        csv_rows.append(
            {
                "paragraph_id": idx,
                "title": card["title"],
                "citation": citation,
                "zotero_key": card["zotero_key"],
                "year": card["year"],
                "relevance_score": card["relevance"],
                "draft_paragraph": paragraph,
                "apa_reference": apa_reference,
                "evidence_snippet_1": evidence[0] if len(evidence) >= 1 else "",
                "evidence_snippet_2": evidence[1] if len(evidence) >= 2 else "",
                "source_card": f"02_cards_basic/{card['path'].name}",
            }
        )

    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"✅ 문단 초안: {md_path}")
    print(f"✅ 인용 트레이스: {csv_path}")
    print("다음: 생성된 문단에서 표현을 다듬고, 원문 PDF 기준으로 숫자/방향성을 검증하세요.")


if __name__ == "__main__":
    main()
