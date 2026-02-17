#!/bin/bash

echo "🏥 ResearchOS 건강 체크"
echo "========================"

# 1. 폴더 구조
echo ""
echo "📁 폴더 구조:"
for dir in 00_search_design 01_zotero_export 02_cards_quick 03_cards_deep 04_index 06_thesis scripts secrets logs; do
    if [ -d ~/ResearchOS/$dir ]; then
        echo "  ✅ $dir"
    else
        echo "  ❌ $dir 없음"
    fi
done

# 2. API 키
echo ""
echo "🔑 API 키:"
if [ -f ~/ResearchOS/secrets/.env ]; then
    if grep -q "ANTHROPIC_API_KEY\|OPENAI_API_KEY" ~/ResearchOS/secrets/.env; then
        echo "  ✅ .env 파일 OK"
    else
        echo "  ⚠️  .env에 API 키 없음"
    fi
else
    echo "  ❌ .env 파일 없음"
fi

# 3. 스크립트
echo ""
echo "📝 스크립트:"
for script in sync_and_analyze.py generate_index.py ai_screener.py citation_paragraph_builder.py reddit_pain_scraper.py; do
    if [ -f ~/ResearchOS/scripts/$script ]; then
        if [ -x ~/ResearchOS/scripts/$script ]; then
            echo "  ✅ $script (실행가능)"
        else
            echo "  ⚠️  $script (권한 없음)"
        fi
    else
        echo "  ❌ $script 없음"
    fi
done

# 4. Python 패키지
echo ""
echo "📦 Python 패키지:"
if python3 -c "import anthropic" 2>/dev/null; then
    echo "  ✅ anthropic"
else
    echo "  ❌ anthropic 없음"
fi

if python3 -c "import openai" 2>/dev/null; then
    echo "  ✅ openai"
else
    echo "  ❌ openai 없음"
fi

if python3 -c "import fitz" 2>/dev/null; then
    echo "  ✅ pymupdf"
else
    echo "  ❌ pymupdf 없음"
fi

if python3 -c "from dotenv import load_dotenv" 2>/dev/null; then
    echo "  ✅ python-dotenv"
else
    echo "  ❌ python-dotenv 없음"
fi

# 5. Zotero Export
echo ""
echo "📚 Zotero:"
if [ -f ~/ResearchOS/01_zotero_export/library.json ]; then
    size=$(wc -c < ~/ResearchOS/01_zotero_export/library.json)
    if [ $size -gt 100 ]; then
        echo "  ✅ library.json ($size bytes)"
    else
        echo "  ⚠️  library.json 너무 작음"
    fi
else
    echo "  ❌ library.json 없음 → Zotero Auto-Export 설정 필요"
fi

# 6. 연구 프로필
echo ""
echo "🎯 연구 프로필:"
if [ -f ~/ResearchOS/MY_RESEARCH.md ]; then
    lines=$(wc -l < ~/ResearchOS/MY_RESEARCH.md)
    echo "  ✅ MY_RESEARCH.md ($lines lines)"
else
    echo "  ❌ MY_RESEARCH.md 없음"
fi

echo ""
echo "========================"
echo "🎯 다음 단계:"
echo "  1. Zotero에 논문 2-3개 추가"
echo "  2. cd ~/ResearchOS/scripts"
echo "  3. python3 sync_and_analyze.py --write"
echo "  4. python3 generate_index.py"
echo "  5. Obsidian으로 ~/ResearchOS 열기"
