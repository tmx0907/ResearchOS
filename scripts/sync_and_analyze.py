#!/usr/bin/env python3
"""
Zotero → 리서치 카드 자동 생성

사용법:
  python3 sync_and_analyze.py                    # dry-run
  python3 sync_and_analyze.py --write             # 기본 (메타데이터만, 무료)
  python3 sync_and_analyze.py --write --ai        # AI 분석 포함 (API 비용)
  python3 sync_and_analyze.py --write --ai --limit 5
"""

import json, os, sys, re, time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

try:
    import fitz
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

load_dotenv(Path.home() / "ResearchOS" / "secrets" / ".env")

ZOTERO_JSON = Path.home() / "ResearchOS" / "01_zotero_export" / "library.json"
CARDS_DIR   = Path.home() / "ResearchOS" / "02_cards_basic"
LOG_DIR     = Path.home() / "ResearchOS" / "logs"
RESEARCH_PROFILE = Path.home() / "ResearchOS" / "MY_RESEARCH.md"

CARDS_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "claude").lower()
DEFAULT_RESEARCH_KEYWORDS = [
    "anxiety", "depression", "mood", "cbt", "act", "mindfulness",
    "automation", "artificial intelligence", "technological unemployment",
    "meaning", "purpose", "identity", "existential",
    "art therapy", "creative", "well-being", "flow",
]

TAG_PREFIXES = {'topic:':'topic','m:':'method','tool:':'measurement','design:':'design','status:':'status','pop:':'population'}

def safe_filename(text, max_len=80):
    clean = re.sub(r'[\\/*?:"<>|]', '', text)
    return clean.strip().replace('  ', ' ')[:max_len]

def extract_authors(item):
    return [f"{a.get('family','')}, {a.get('given','')}" if a.get('given') else a.get('family','')
            for a in item.get('author', []) if a.get('family')]

def extract_year(item):
    parts = item.get('issued', {}).get('date-parts', [[]])
    return str(parts[0][0]) if parts and parts[0] else 'n.d.'

def extract_keywords(item):
    kw = item.get('keyword', '')
    if isinstance(kw, list): return kw
    if isinstance(kw, str) and kw: return [k.strip() for k in kw.split(',')]
    return []

def categorize_tags(keywords):
    cats = {v: [] for v in TAG_PREFIXES.values()}
    cats['other'] = []
    for kw in keywords:
        matched = False
        for prefix, cat in TAG_PREFIXES.items():
            if kw.startswith(prefix):
                cats[cat].append(kw[len(prefix):])
                matched = True; break
        if not matched: cats['other'].append(kw)
    return cats

def load_research_keywords():
    path = Path.home() / "ResearchOS" / "MY_RESEARCH.md"
    if not path.exists():
        return DEFAULT_RESEARCH_KEYWORDS
    content = path.read_text(encoding='utf-8').lower()
    keywords = set(DEFAULT_RESEARCH_KEYWORDS)
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('- '):
            item = line[2:].strip()
            main = item.split('(')[0].strip()
            for token in re.split(r'[,/→\-]+', main):
                token = token.strip()
                if len(token) > 2 and re.search(r'[a-z]', token):
                    keywords.add(token)
            if '(' in item and ')' in item:
                for sub in item[item.index('(')+1:item.index(')')].split(','):
                    sub = sub.strip()
                    if len(sub) > 2 and re.search(r'[a-z]', sub.lower()):
                        keywords.add(sub.lower())
    return sorted(keywords)

def calculate_relevance(item, research_keywords):
    if not research_keywords:
        return 0
    title = item.get('title', '').lower()
    abstract = item.get('abstract', '').lower()
    kws = [k.lower() for k in extract_keywords(item)]
    content = f"{title} {abstract} {' '.join(kws)}"

    score = 0.0
    for rk in research_keywords:
        if rk in title:
            score += 4
        elif any(rk in k for k in kws):
            score += 3
        elif rk in abstract:
            score += 1.5

    # Common evidence language receives a slight boost for methods-heavy papers.
    evidence_terms = ["meta-analysis", "systematic review", "randomized", "rct", "effect size"]
    score += sum(0.75 for term in evidence_terms if term in content)

    tags = categorize_tags(extract_keywords(item))
    if tags.get('method'):
        score += 2
    max_p = len(research_keywords) * 4 + 2
    if max_p <= 0:
        return 0
    return min(100, round((score / max_p) * 100, 1))

def call_llm(prompt, system_prompt):
    try:
        if LLM_PROVIDER == "claude":
            from anthropic import Anthropic
            client = Anthropic()
            r = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=2000,
                system=system_prompt, messages=[{"role":"user","content":prompt}])
            return r.content[0].text
        from openai import OpenAI
        client = OpenAI()
        r = client.chat.completions.create(model="gpt-4o-mini",
            messages=[{"role":"system","content":system_prompt},{"role":"user","content":prompt}],
            temperature=0.2, max_tokens=2000)
        return r.choices[0].message.content
    except ImportError as exc:
        raise RuntimeError(
            f"LLM SDK가 설치되지 않았습니다. provider={LLM_PROVIDER}"
        ) from exc

def ai_analyze(text, research_profile):
    system_prompt = "You are a psychology research assistant. Respond ONLY with valid JSON."
    prompt = f"""논문 분석 → JSON:

=== 연구 프로필 ===
{research_profile[:1500]}

=== 논문 텍스트 ===
{text[:4000]}

JSON:
{{"key_claims":["주장1","주장2","주장3"],"main_finding":"한줄요약","method_type":"RCT/meta/survey/etc","sample_size":"N=?","population":"대상","design":"between/within/etc","measurement_tools":"도구","effect_size":"효과크기","limitations":"한계","relevance_to_my_research":"연결점 2문장","reading_priority":"must-read/should-read/reference-only","priority_reason":"이유","suggested_topic_tags":["tag1","tag2"]}}"""
    try:
        raw = call_llm(prompt, system_prompt)
        cleaned = re.sub(r'^```\w*\n?|```$', '', raw.strip())
        return json.loads(cleaned)
    except Exception:
        return None

def make_card(item, ai_data=None):
    title = item.get('title', 'Untitled')
    authors = extract_authors(item)
    year = extract_year(item)
    doi = item.get('DOI', item.get('doi', ''))
    abstract = item.get('abstract', '')
    journal = item.get('container-title', '')
    keywords = extract_keywords(item)
    tags = categorize_tags(keywords)
    
    method = ai_data.get('method_type','') if ai_data else ', '.join(tags.get('method',[]))
    measurement = ai_data.get('measurement_tools','') if ai_data else ', '.join(tags.get('measurement',[]))
    population = ai_data.get('population','') if ai_data else ', '.join(tags.get('population',[]))
    design = ai_data.get('design','') if ai_data else ', '.join(tags.get('design',[]))
    sample_size = ai_data.get('sample_size','') if ai_data else ''
    effect_size = ai_data.get('effect_size','') if ai_data else ''
    key_claims = ai_data.get('key_claims',[]) if ai_data else []
    main_finding = ai_data.get('main_finding','') if ai_data else ''
    limitations = ai_data.get('limitations','') if ai_data else ''
    relevance_text = ai_data.get('relevance_to_my_research','') if ai_data else ''
    reading_priority = ai_data.get('reading_priority','to-read') if ai_data else 'to-read'
    priority_reason = ai_data.get('priority_reason','') if ai_data else ''
    
    if ai_data:
        for t in ai_data.get('suggested_topic_tags', []):
            if f"topic:{t}" not in keywords: keywords.append(f"topic:{t}")
    
    rk = load_research_keywords()
    relevance_score = calculate_relevance(item, rk)
    p_emoji = {'must-read':'🔴','should-read':'🟡','reference-only':'⚪','to-read':'📘'}.get(reading_priority,'📘')

    lines = ['---']
    lines.append(f'title: "{title}"')
    if authors:
        lines.append('authors:')
        for a in authors: lines.append(f'  - "{a}"')
    lines.append(f'year: {year}')
    if journal: lines.append(f'journal: "{journal}"')
    if doi: lines.append(f'DOI: "{doi}"')
    lines.append(f'method: "{method}"')
    lines.append(f'sample_size: "{sample_size}"')
    lines.append(f'population: "{population}"')
    lines.append(f'design: "{design}"')
    lines.append(f'measurement: "{measurement}"')
    lines.append(f'effect_size: "{effect_size}"')
    lines.append(f'relevance_score: {relevance_score}')
    lines.append(f'reading_priority: "{reading_priority}"')
    if keywords:
        lines.append('tags:')
        for k in keywords: lines.append(f'  - "{k}"')
    lines.append(f'zotero_key: "{item.get("id","")}"')
    lines.append(f'card_type: quickcard')
    lines.append(f'created: "{datetime.now().strftime("%Y-%m-%d")}"')
    lines.append(f'source: "{"ai-analyzed" if ai_data else "metadata-only"}"')
    lines.append('---')
    lines.append(f'\n# {title}\n')
    lines.append(f'{p_emoji} **Priority:** {reading_priority}')
    if priority_reason: lines.append(f'> {priority_reason}')
    lines.append(f'\n**Authors:** {"; ".join(authors)}')
    lines.append(f'**Year:** {year}')
    if journal: lines.append(f'**Journal:** {journal}')
    if doi: lines.append(f'**DOI:** https://doi.org/{doi}')
    lines.append(f'**Relevance:** {relevance_score}/100\n')
    
    lines.append('## 📊 연구 분해\n')
    lines.append('| 항목 | 내용 |')
    lines.append('|------|------|')
    lines.append(f'| **Method** | {method or "<!-- 채우기 -->"} |')
    lines.append(f'| **N** | {sample_size or "<!-- 채우기 -->"} |')
    lines.append(f'| **Population** | {population or "<!-- 채우기 -->"} |')
    lines.append(f'| **Design** | {design or "<!-- 채우기 -->"} |')
    lines.append(f'| **Measurement** | {measurement or "<!-- 채우기 -->"} |')
    lines.append(f'| **Effect Size** | {effect_size or "<!-- 채우기 -->"} |')
    
    if key_claims:
        lines.append('\n## 🎯 핵심 주장\n')
        for i, c in enumerate(key_claims, 1): lines.append(f'{i}. {c}')
    
    if main_finding:
        lines.append(f'\n## 💡 주요 발견\n\n{main_finding}')
    
    if abstract:
        lines.append(f'\n## Abstract\n\n{abstract}')
    
    lines.append('\n## 🔗 내 연구와의 연결점\n')
    lines.append(relevance_text or '<!-- 이 논문이 내 연구와 어떻게 연결되는지 메모 -->')
    
    if limitations:
        lines.append(f'\n## ⚠️ 한계점\n\n{limitations}')
    
    lines.append('\n## 📝 내 메모\n\n<!-- 논문 읽은 후 메모 -->')
    lines.append('\n## 🔗 Related\n\n<!-- [[관련카드]] -->')
    
    return '\n'.join(lines)

def main():
    write_mode = '--write' in sys.argv
    ai_mode = '--ai' in sys.argv
    limit = None
    for i, arg in enumerate(sys.argv):
        if arg == '--limit' and i+1 < len(sys.argv):
            try:
                limit = int(sys.argv[i+1])
            except ValueError:
                print("⚠️ --limit 값이 숫자가 아닙니다. 전체를 처리합니다.")
                limit = None
    
    if not ZOTERO_JSON.exists():
        print(f"❌ {ZOTERO_JSON} 없음. Zotero Auto-Export 설정 확인."); sys.exit(1)
    
    with open(ZOTERO_JSON, 'r', encoding='utf-8') as f: data = json.load(f)
    items = data if isinstance(data, list) else data.get('items', [])
    print(f"📚 Zotero: {len(items)}개")
    
    existing = {f.stem for f in CARDS_DIR.glob('*.md')}
    rk = load_research_keywords()
    
    new_items = [(item, calculate_relevance(item, rk)) for item in items
                 if safe_filename(item.get('title','Untitled')) not in existing
                 and safe_filename(item.get('title','Untitled'))]
    new_items.sort(key=lambda x: x[1], reverse=True)
    
    print(f"🆕 새 카드: {len(new_items)}개 (기존: {len(existing)}개)")
    if limit: new_items = new_items[:limit]
    if ai_mode:
        sdk_ok = True
        if LLM_PROVIDER == "claude":
            try:
                import anthropic  # noqa: F401
            except ImportError:
                sdk_ok = False
        else:
            try:
                import openai  # noqa: F401
            except ImportError:
                sdk_ok = False
        if not sdk_ok:
            print(f"⚠️ {LLM_PROVIDER} SDK 미설치로 AI 분석을 건너뜁니다. (metadata-only 모드)")
            ai_mode = False
        else:
            print(f"🤖 AI 모드 | 💰 ~${len(new_items)*0.02:.2f}")
    
    rp = RESEARCH_PROFILE.read_text(encoding='utf-8') if RESEARCH_PROFILE.exists() else ""
    created = []
    
    for i, (item, rel) in enumerate(new_items):
        title = item.get('title','Untitled')
        filename = safe_filename(title)
        filepath = CARDS_DIR / f"{filename}.md"
        
        if not write_mode:
            e = "🟢" if rel>=50 else "🟡" if rel>=20 else "⚪"
            print(f"  {e} [DRY-RUN] {filename}.md ({rel})")
            created.append(filename); continue
        
        ai_data = None
        if ai_mode:
            text = item.get('abstract', '')
            if text:
                ai_data = ai_analyze(text, rp)
                time.sleep(1)
        
        filepath.write_text(make_card(item, ai_data), encoding='utf-8')
        p = ai_data.get('reading_priority','to-read') if ai_data else 'to-read'
        e = {'must-read':'🔴','should-read':'🟡','reference-only':'⚪','to-read':'📘'}.get(p,'📘')
        print(f"  {e} [CREATED] {filename}.md ({rel})")
        created.append(filename)
    
    print(f"\n{'='*50}")
    print(f"  {'실제 생성' if write_mode else 'DRY-RUN'}: {len(created)}개")
    if not write_mode: print(f"\n💡 python3 sync_and_analyze.py --write")
    elif created: print(f"💡 python3 generate_index.py")

if __name__ == '__main__':
    main()
