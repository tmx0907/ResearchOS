#!/usr/bin/env python3
"""
축별 논문 수집 진행도 추적
"""

import json
from pathlib import Path
from collections import defaultdict

CARDS_DIR = Path.home() / "ResearchOS" / "02_cards_basic"

# 목표 설정
GOALS = {
    "🧠 Anxiety & Depression": {
        "target": 15,
        "tags": ["T:Anxiety", "T:Depression", "T:GAD", "T:MDD"],
        "priority": "⭐⭐⭐",
        "breakdown": {"review/meta": 5, "empirical": 10}
    },
    "🤖 AI & Existential": {
        "target": 15,
        "tags": ["T:AI", "T:Technostress", "T:Meaning", "T:Identity"],
        "priority": "⭐⭐⭐",
        "breakdown": {"theory": 5, "empirical": 10}
    },
    "🎨 Art & Mental Health": {
        "target": 10,
        "tags": ["T:Art", "T:Creativity"],
        "priority": "⭐⭐",
        "breakdown": {"review/meta": 3, "empirical": 7}
    },
    "🔗 Cross-cutting": {
        "target": 10,
        "tags": ["multiple"],
        "priority": "⭐⭐⭐⭐",
        "breakdown": {}
    }
}

def parse_frontmatter(filepath):
    """카드에서 태그 추출"""
    content = filepath.read_text(encoding='utf-8')
    if not content.startswith('---'):
        return []
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        return []
    
    tags = []
    in_tags = False
    for line in parts[1].split('\n'):
        line = line.strip()
        if line == 'tags:':
            in_tags = True
            continue
        if in_tags:
            if line.startswith('- '):
                tag = line[2:].strip().strip('"')
                tags.append(tag)
            elif not line.startswith('-'):
                break
    return tags

def categorize_paper(tags):
    """논문을 축별로 분류"""
    axes = []
    
    # Anxiety & Depression
    if any(t in tags for t in ["T:Anxiety", "T:Depression", "T:GAD", "T:MDD"]):
        axes.append("🧠 Anxiety & Depression")
    
    # AI & Existential
    if any(t in tags for t in ["T:AI", "T:Technostress", "T:Meaning", "T:Identity"]):
        axes.append("🤖 AI & Existential")
    
    # Art & Mental Health
    if any(t in tags for t in ["T:Art", "T:Creativity"]):
        axes.append("🎨 Art & Mental Health")
    
    # Cross-cutting (2개 이상 축)
    if len(axes) >= 2:
        axes.append("🔗 Cross-cutting")
    
    return axes

def get_paper_type(tags):
    """논문 타입 구분"""
    if "M:Meta-analysis" in tags:
        return "review/meta"
    if "M:RCT" in tags or "M:Longitudinal" in tags or "M:Cross-sectional" in tags:
        return "empirical"
    if "R:Theory" in tags:
        return "theory"
    return "other"

def main():
    papers = list(CARDS_DIR.glob("*.md"))
    
    # 축별 카운트
    axis_counts = defaultdict(lambda: {"total": 0, "by_type": defaultdict(int), "papers": []})
    
    for paper in papers:
        tags = parse_frontmatter(paper)
        axes = categorize_paper(tags)
        paper_type = get_paper_type(tags)
        
        for axis in axes:
            axis_counts[axis]["total"] += 1
            axis_counts[axis]["by_type"][paper_type] += 1
            axis_counts[axis]["papers"].append(paper.stem)
    
    # 출력
    print("\n📊 ResearchOS 진행도 추적")
    print("=" * 60)
    
    for axis, goal in GOALS.items():
        current = axis_counts[axis]["total"]
        target = goal["target"]
        progress = (current / target * 100) if target > 0 else 0
        
        print(f"\n{axis}")
        print(f"  목표: {target}편 | 현재: {current}편 | 진행률: {progress:.1f}%")
        print(f"  우선순위: {goal['priority']}")
        
        # 진행 바
        bar_length = 30
        filled = int(bar_length * current / target) if target > 0 else 0
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"  [{bar}] {current}/{target}")
        
        # 타입별 분포
        if goal["breakdown"]:
            print(f"\n  세부 목표:")
            for ptype, ptarget in goal["breakdown"].items():
                pcurrent = axis_counts[axis]["by_type"].get(ptype, 0)
                print(f"    {ptype}: {pcurrent}/{ptarget}편")
    
    print("\n" + "=" * 60)
    print(f"📚 전체: {len(papers)}편")
    print("\n💡 다음 단계:")
    
    # 추천
    for axis, goal in GOALS.items():
        current = axis_counts[axis]["total"]
        if current < goal["target"]:
            needed = goal["target"] - current
            print(f"  {axis}: {needed}편 더 필요 ({goal['priority']})")

if __name__ == '__main__':
    main()
