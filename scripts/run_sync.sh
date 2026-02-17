#!/bin/bash
# ============================================================
# ResearchOS 자동 동기화 스크립트
# - library.json 변경 감지 시 sync_and_analyze.py 실행
# - debounce (30초) + md5 해시 체크로 불필요한 실행 방지
# ============================================================

set -euo pipefail

# ── 설정 ──────────────────────────────────────────────────────
PYTHON="/usr/bin/python3"
BASE_DIR="$HOME/ResearchOS"
SCRIPTS_DIR="$BASE_DIR/scripts"
EXPORT_FILE="$BASE_DIR/01_zotero_export/My Library.json"
LIBRARY="$BASE_DIR/01_zotero_export/library.json"
LOG_DIR="$BASE_DIR/logs"
STATE_DIR="$BASE_DIR/logs/.state"

DEBOUNCE_SEC=30
LAST_RUN_FILE="$STATE_DIR/last_run"
LAST_HASH_FILE="$STATE_DIR/last_hash"

# ── 디렉토리 준비 ────────────────────────────────────────────
mkdir -p "$LOG_DIR" "$STATE_DIR"

# ── 로그 설정 ────────────────────────────────────────────────
LOG_FILE="$LOG_DIR/sync_$(date +%Y%m%d).log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# ── 1) debounce 체크 ─────────────────────────────────────────
if [[ -f "$LAST_RUN_FILE" ]]; then
    last_run=$(cat "$LAST_RUN_FILE")
    now=$(date +%s)
    elapsed=$(( now - last_run ))
    if (( elapsed < DEBOUNCE_SEC )); then
        log "SKIP: debounce — 마지막 실행 ${elapsed}초 전 (< ${DEBOUNCE_SEC}초)"
        exit 0
    fi
fi

# ── 2) My Library.json → library.json 복사 ───────────────────
if [[ -f "$EXPORT_FILE" ]]; then
    cp "$EXPORT_FILE" "$LIBRARY"
    log "COPY: My Library.json → library.json"
elif [[ ! -f "$LIBRARY" ]]; then
    log "ERROR: library.json 파일 없음"
    exit 1
fi

# ── 3) md5 해시 체크 ─────────────────────────────────────────
current_hash=$(md5 -q "$LIBRARY")

if [[ -f "$LAST_HASH_FILE" ]]; then
    last_hash=$(cat "$LAST_HASH_FILE")
    if [[ "$current_hash" == "$last_hash" ]]; then
        log "SKIP: 변경없음 — md5 동일 ($current_hash)"
        # debounce 타이머는 갱신 (연속 호출 방지)
        date +%s > "$LAST_RUN_FILE"
        exit 0
    fi
fi

# ── 4) 실행 (scripts 디렉토리에서 실행해야 정상 동작) ────────
cd "$SCRIPTS_DIR"

log "START: 변경 감지됨 (hash: $current_hash)"

# 4-1) 카드 생성
log "실행: python3 sync_and_analyze.py --write"
if "$PYTHON" sync_and_analyze.py --write >> "$LOG_FILE" 2>&1; then
    log "SUCCESS: sync_and_analyze.py 완료"
else
    exit_code=$?
    log "FAIL: sync_and_analyze.py 종료코드=$exit_code"
fi

# 4-2) 인덱스 생성
log "실행: python3 generate_index.py"
if "$PYTHON" generate_index.py >> "$LOG_FILE" 2>&1; then
    log "SUCCESS: generate_index.py 완료"
else
    exit_code=$?
    log "FAIL: generate_index.py 종료코드=$exit_code"
fi

# 4-3) thesis-coach 연동 (선택적, 실패해도 OK)
log "실행: python3 sync_to_thesis_coach.py"
if "$PYTHON" sync_to_thesis_coach.py >> "$LOG_FILE" 2>&1; then
    log "SUCCESS: sync_to_thesis_coach.py 완료"
else
    log "INFO: sync_to_thesis_coach.py 스킵 (thesis-coach 미실행 또는 오류)"
fi

# ── 5) 상태 저장 ─────────────────────────────────────────────
date +%s > "$LAST_RUN_FILE"
echo "$current_hash" > "$LAST_HASH_FILE"

log "DONE"
