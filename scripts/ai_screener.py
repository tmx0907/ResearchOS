#!/usr/bin/env python3
"""
AI 스크리닝 — Scopus/DB export CSV를 읽어서 관련 논문만 필터링

사용법:
  python3 ai_screener.py ~/ResearchOS/00_search_design/scopus_exports/export.csv
  python3 ai_screener.py export.csv --write     # 결과 저장
"""

import csv
import json
import os
import sys
import re
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(Path.home() / "ResearchOS" / "secrets" / ".env")

RESEARCH_PROFILE = Path.home() / "ResearchOS" / "MY_RESEARCH.md"
OUTPUT_DIR = Path.home() / "ResearchOS" / "00_search_design"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "claude").lower()
DEFAULT_KEYWORDS = [
    "anxiety", "depression", "mood", "mental health",
    "art therapy", "creative", "meaning", "purpose",
    "identity", "automation", "artificial intelligence",
]

def call_llm(prompt, system_prompt):
    if LLM_PROVIDER == "claude":
        from anthropic import Anthropic
        client = Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    else:
        from openai import OpenAI
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":system_prompt},{"role":"user","content":prompt}],
            temperature=0.2, max_tokens=2000
        )
        return response.choices[0].message.content

def llm_sdk_available():
    if LLM_PROVIDER == "claude":
        try:
            import anthropic  # noqa: F401
            return True
        except ImportError:
            return False
    try:
        import openai  # noqa: F401
        return True
    except ImportError:
        return False

def extract_profile_keywords(research_profile):
    kws = set(DEFAULT_KEYWORDS)
    for line in research_profile.lower().splitlines():
        line = line.strip()
        if line.startswith("- "):
            for token in re.split(r"[,/→()\\-]+", line[2:]):
                token = token.strip()
                if len(token) > 2 and re.search(r"[a-z]", token):
                    kws.add(token)
    return sorted(kws)

def rule_based_screen(papers_batch, research_profile):
    keywords = extract_profile_keywords(research_profile)
    results = []
    for i, p in enumerate(papers_batch, 1):
        title = p.get("title", "").lower()
        abstract = p.get("abstract", "").lower()
        content = f"{title} {abstract}"
        hits = sum(1 for kw in keywords if kw in content)

        if hits >= 6:
            rel = "high"
        elif hits >= 3:
            rel = "medium"
        elif hits >= 1:
            rel = "low"
        else:
            rel = "irrelevant"

        counter_terms = ["no effect", "null finding", "not significant", "ineffective", "mixed evidence"]
        is_counter = any(t in content for t in counter_terms)

        if any(t in content for t in ["art", "creative", "music", "therapy"]):
            section = "예술/정신건강"
        elif any(t in content for t in ["ai", "automation", "unemployment", "purpose", "meaning"]):
            section = "AI/실존"
        elif any(t in content for t in ["anxiety", "depression", "cbt", "mindfulness"]):
            section = "우울/불안"
        else:
            section = "교차점"

        results.append(
            {
                "index": i,
                "relevance": rel,
                "reason": f"키워드 매칭 {hits}개 기반 룰베이스 분류",
                "section_fit": section,
                "is_counterargument": is_counter,
            }
        )
    return results

def load_csv(csv_path):
    """Scopus/DB export CSV 읽기"""
    papers = []
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Scopus 형식: Title, Authors, Abstract, Year, Source title, DOI
            # 다른 DB도 비슷한 필드를 가짐
            paper = {
                'title': row.get('Title', row.get('title', row.get('TI', ''))),
                'authors': row.get('Authors', row.get('authors', row.get('AU', ''))),
                'abstract': row.get('Abstract', row.get('abstract', row.get('AB', ''))),
                'year': row.get('Year', row.get('year', row.get('PY', ''))),
                'journal': row.get('Source title', row.get('journal', row.get('SO', ''))),
                'doi': row.get('DOI', row.get('doi', row.get('DI', ''))),
            }
            if paper['title']:  # 제목이 있는 것만
                papers.append(paper)
    
    return papers

def screen_batch(papers_batch, research_profile, use_llm=True):
    """논문 배치를 AI로 스크리닝"""
    if not use_llm:
        return rule_based_screen(papers_batch, research_profile)
    
    papers_text = ""
    for i, p in enumerate(papers_batch):
        papers_text += f"\n[{i+1}] {p['title']}\n"
        if p['abstract']:
            papers_text += f"    Abstract: {p['abstract'][:300]}\n"
    
    system_prompt = """You are a research screening assistant for a psychology graduate student.
Evaluate papers for relevance. Respond ONLY with valid JSON. No backticks, no markdown."""

    prompt = f"""내 연구 프로필:
{research_profile[:2000]}

아래 논문들을 스크리닝해주세요.
각 논문에 대해 관련성을 판단하고 JSON으로 응답:

{papers_text}

JSON 형식 (배열):
[
  {{
    "index": 1,
    "relevance": "high/medium/low/irrelevant",
    "reason": "관련 이유 한 줄 (한국어)",
    "section_fit": "어느 Lit Review 섹션에 맞는지 (예: AI/실존, 우울/의미, 예술/정신건강, 교차점)",
    "is_counterargument": false
  }},
  ...
]"""

    try:
        raw = call_llm(prompt, system_prompt)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r'^```\w*\n?', '', cleaned)
            cleaned = re.sub(r'\n?```$', '', cleaned)
        return json.loads(cleaned)
    except Exception:
        return None

def main():
    if len(sys.argv) < 2:
        print("사용법: python3 ai_screener.py export.csv [--write]")
        sys.exit(1)
    
    csv_path = Path(sys.argv[1]).expanduser()
    write_mode = '--write' in sys.argv
    
    if not csv_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {csv_path}")
        sys.exit(1)
    
    papers = load_csv(csv_path)
    print(f"📄 CSV에서 {len(papers)}편 로드")
    
    research_profile = ""
    if RESEARCH_PROFILE.exists():
        research_profile = RESEARCH_PROFILE.read_text(encoding='utf-8')

    use_llm = llm_sdk_available()
    if not use_llm:
        print(f"⚠️ {LLM_PROVIDER} SDK 미설치: 룰베이스 스크리닝으로 대체합니다.")
    
    # 배치 처리 (10개씩)
    batch_size = 10
    all_results = []
    
    for i in range(0, len(papers), batch_size):
        batch = papers[i:i+batch_size]
        print(f"\n🤖 스크리닝 중: {i+1}-{min(i+batch_size, len(papers))} / {len(papers)}")
        
        results = screen_batch(batch, research_profile, use_llm=use_llm)
        
        if results:
            for r in results:
                idx = r.get('index', 0) - 1
                if 0 <= idx < len(batch):
                    batch[idx]['relevance'] = r.get('relevance', 'unknown')
                    batch[idx]['reason'] = r.get('reason', '')
                    batch[idx]['section_fit'] = r.get('section_fit', '')
                    batch[idx]['is_counterargument'] = r.get('is_counterargument', False)
            all_results.extend(batch)
        else:
            print("  ⚠️  배치 파싱 실패")
            all_results.extend(batch)
        
        time.sleep(1)
    
    # 결과 분류
    high = [p for p in all_results if p.get('relevance') == 'high']
    medium = [p for p in all_results if p.get('relevance') == 'medium']
    low = [p for p in all_results if p.get('relevance') == 'low']
    irrelevant = [p for p in all_results if p.get('relevance') == 'irrelevant']
    counter = [p for p in all_results if p.get('is_counterargument')]
    
    print(f"\n{'='*50}")
    print(f"📊 스크리닝 결과:")
    print(f"  🟢 High:       {len(high)}편 → Zotero에 추가")
    print(f"  🟡 Medium:     {len(medium)}편 → 초록 한번 더 확인")
    print(f"  ⚪ Low:        {len(low)}편 → 나중에 필요하면")
    print(f"  ❌ Irrelevant: {len(irrelevant)}편 → 무시")
    print(f"  ⚔️  반론:       {len(counter)}편 → 반드시 포함")
    print(f"{'='*50}")
    
    # 결과 저장
    if write_mode:
        # 마크다운 보고서
        lines = []
        lines.append(f"# 🔍 AI 스크리닝 결과")
        lines.append(f"\n> 원본: {csv_path.name}")
        lines.append(f"> 총 {len(all_results)}편 중 관련 {len(high) + len(medium)}편")
        lines.append(f"> 날짜: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("")
        
        lines.append("## 🟢 High Relevance — Zotero에 추가하세요")
        lines.append("")
        for p in high:
            lines.append(f"### {p['title']}")
            lines.append(f"- **Authors:** {p.get('authors', '?')}")
            lines.append(f"- **Year:** {p.get('year', '?')}")
            lines.append(f"- **Journal:** {p.get('journal', '?')}")
            if p.get('doi'):
                lines.append(f"- **DOI:** https://doi.org/{p['doi']}")
            lines.append(f"- **이유:** {p.get('reason', '')}")
            lines.append(f"- **섹션:** {p.get('section_fit', '')}")
            if p.get('is_counterargument'):
                lines.append(f"- ⚔️ **반론 논문**")
            lines.append("")
        
        lines.append("## 🟡 Medium Relevance — 초록 확인 후 판단")
        lines.append("")
        for p in medium:
            lines.append(f"- **{p['title']}** ({p.get('year','?')}) — {p.get('reason','')}")
        lines.append("")
        
        lines.append("## ⚔️ 반론 논문 — 반드시 포함")
        lines.append("")
        for p in counter:
            lines.append(f"- **{p['title']}** ({p.get('year','?')}) — {p.get('reason','')}")
        lines.append("")
        
        output_file = OUTPUT_DIR / f"screening_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        output_file.write_text('\n'.join(lines), encoding='utf-8')
        print(f"\n📋 결과 저장: {output_file}")
        
        # JSON도 저장
        json_file = OUTPUT_DIR / f"screening_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        json_file.write_text(json.dumps(all_results, ensure_ascii=False, indent=2), encoding='utf-8')
    
    else:
        print(f"\n💡 결과 저장: python3 ai_screener.py {csv_path} --write")
    
    print(f"\n다음 단계:")
    print(f"  1. 🟢 High 논문을 Zotero에 추가")
    print(f"  2. 🟡 Medium 초록 확인 → 필요한 것만 추가")
    print(f"  3. ⚔️ 반론 논문 반드시 추가")
    print(f"  4. python3 sync_and_analyze.py --write  (카드 생성)")

if __name__ == '__main__':
    main()
