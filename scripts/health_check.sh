#!/bin/bash
set -euo pipefail

BASE_DIR="$HOME/ResearchOS"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRENT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🏥 ResearchOS health check"
echo "=========================="
echo "Base path: $BASE_DIR"

if [ "$CURRENT_ROOT" != "$BASE_DIR" ]; then
    echo ""
    echo "⚠️  현재 실행 위치는 $CURRENT_ROOT 입니다."
    echo "   코드 기본 경로는 $BASE_DIR 이므로, symlink 또는 표준 경로 사용을 권장합니다."
fi

echo ""
echo "📁 Folder structure:"
for dir in 00_search_design 01_zotero_export 02_cards_basic 03_cards_detailed 04_index 06_thesis scripts secrets logs; do
    if [ -d "$BASE_DIR/$dir" ]; then
        echo "  ✅ $dir"
    else
        echo "  ❌ $dir missing"
    fi
done

echo ""
echo "🔑 API keys (.env):"
if [ -f "$BASE_DIR/secrets/.env" ]; then
    if grep -q "ANTHROPIC_API_KEY\|OPENAI_API_KEY" "$BASE_DIR/secrets/.env"; then
        echo "  ✅ .env exists"
    else
        echo "  ⚠️  .env exists, but API key lines are missing"
    fi
else
    echo "  ❌ $BASE_DIR/secrets/.env missing"
fi

echo ""
echo "📝 Core scripts:"
for script in sync_and_analyze.py generate_index.py ai_screener.py citation_paragraph_builder.py track_progress.py run_sync.sh; do
    if [ -f "$BASE_DIR/scripts/$script" ]; then
        if [ -x "$BASE_DIR/scripts/$script" ]; then
            echo "  ✅ $script"
        else
            echo "  ⚠️  $script exists but is not executable"
        fi
    else
        echo "  ❌ $script missing"
    fi
done

echo ""
echo "📦 Python packages:"
if python3 -c "import fitz" 2>/dev/null; then
    echo "  ✅ pymupdf"
else
    echo "  ❌ pymupdf"
fi

if python3 -c "from dotenv import load_dotenv" 2>/dev/null; then
    echo "  ✅ python-dotenv"
else
    echo "  ❌ python-dotenv"
fi

if python3 -c "import anthropic" 2>/dev/null; then
    echo "  ✅ anthropic (optional)"
else
    echo "  ⚪ anthropic not installed (optional)"
fi

if python3 -c "import openai" 2>/dev/null; then
    echo "  ✅ openai (optional)"
else
    echo "  ⚪ openai not installed (optional)"
fi

echo ""
echo "📚 Zotero export:"
if [ -f "$BASE_DIR/01_zotero_export/library.json" ]; then
    size=$(wc -c < "$BASE_DIR/01_zotero_export/library.json")
    if [ "$size" -gt 100 ]; then
        echo "  ✅ library.json ($size bytes)"
    else
        echo "  ⚠️  library.json exists but too small"
    fi
else
    echo "  ❌ library.json missing (set Zotero auto-export)"
fi

echo ""
echo "🎯 Research profile:"
if [ -f "$BASE_DIR/MY_RESEARCH.md" ]; then
    lines=$(wc -l < "$BASE_DIR/MY_RESEARCH.md")
    echo "  ✅ MY_RESEARCH.md ($lines lines)"
else
    echo "  ❌ MY_RESEARCH.md missing"
fi

echo ""
echo "=========================="
echo "Next steps:"
echo "  1) Add 2-3 papers to Zotero"
echo "  2) cd ~/ResearchOS/scripts"
echo "  3) python3 sync_and_analyze.py --write"
echo "  4) python3 generate_index.py"
echo "  5) Open ~/ResearchOS in Obsidian"
