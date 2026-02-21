#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd -P)"
TARGET_DIR="$HOME/ResearchOS"
ENV_FILE="$TARGET_DIR/secrets/.env"

echo "ResearchOS newbie setup"
echo "======================="
echo "Project: $PROJECT_DIR"
echo "Target : $TARGET_DIR"

if [ -e "$TARGET_DIR" ]; then
    TARGET_REAL="$(cd "$TARGET_DIR" && pwd -P)"
    if [ "$TARGET_REAL" != "$PROJECT_DIR" ]; then
        echo ""
        echo "ERROR: $TARGET_DIR already points to a different folder:"
        echo "       $TARGET_REAL"
        echo ""
        echo "Resolve first, then re-run setup:"
        echo "  1) mv \"$TARGET_DIR\" \"${TARGET_DIR}_backup_$(date +%Y%m%d)\""
        echo "  2) ln -s \"$PROJECT_DIR\" \"$TARGET_DIR\""
        exit 1
    fi
else
    ln -s "$PROJECT_DIR" "$TARGET_DIR"
    echo "Created symlink: $TARGET_DIR -> $PROJECT_DIR"
fi

mkdir -p \
    "$TARGET_DIR/00_search_design/scopus_exports" \
    "$TARGET_DIR/01_zotero_export" \
    "$TARGET_DIR/02_cards_basic" \
    "$TARGET_DIR/03_cards_detailed" \
    "$TARGET_DIR/04_index" \
    "$TARGET_DIR/06_thesis/sections" \
    "$TARGET_DIR/secrets" \
    "$TARGET_DIR/logs"

if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" <<'EOF'
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
LLM_PROVIDER=claude
EOF
    echo "Created: $ENV_FILE"
else
    echo "Exists : $ENV_FILE"
fi

chmod +x "$TARGET_DIR/scripts/"*.py "$TARGET_DIR/scripts/"*.sh || true

echo ""
echo "Installing required Python packages..."
if python3 -m pip install --user python-dotenv pyyaml tqdm pymupdf; then
    echo "Required packages installed."
else
    echo "Package installation failed."
    echo "Try manually:"
    echo "  python3 -m pip install --user python-dotenv pyyaml tqdm pymupdf"
fi

echo ""
echo "Running health check..."
bash "$TARGET_DIR/scripts/health_check.sh"

cat <<'EOF'

Setup complete.

Next manual step (important):
1) In Zotero, export My Library with Better CSL JSON
2) File path: ~/ResearchOS/01_zotero_export/library.json
3) Enable "Keep updated"

Then run:
  cd ~/ResearchOS/scripts
  python3 sync_and_analyze.py --write
  python3 generate_index.py
EOF
