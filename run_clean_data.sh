#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_PARENT="$(dirname "$SCRIPT_DIR")"

echo "$(date) [cron] run_clean_data.sh 執行中" >> /tmp/cron_debug.log

# 確認 venv 存在（用 python 直呼叫，不依賴 source）
PY="$SCRIPT_DIR/.venv/bin/python"
if [ ! -x "$PY" ]; then
  echo "$(date) [cron] 找不到 $PY，請先建立虛擬環境" >> /tmp/cron_debug.log
  exit 1
fi

#-p建立父層
mkdir -p "$SCRIPT_DIR/logs"

# 關鍵：在 creditcard_analysis 的上一層執行 -m
cd "$PROJECT_PARENT" || exit 1

"$PY" -m creditcard_analysis.clean_data.clean --source csv_url \
  >> "$SCRIPT_DIR/logs/clean_data.log" 2>&1