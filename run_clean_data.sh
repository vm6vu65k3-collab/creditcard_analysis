#!/bin/bash 

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"&& pwd)"
PY="$ROOT/.venv/bin/python"

echo "$(date) [cron] run_clean_data.sh 執行中" >> /tmp/cron_debug.log

if [ ! -x "$PY" ]; then
    echo "$(date) [cron] 找不到"$PY"，請先建立虛擬環境" >> /tmp/cron_debug_log
    exit 1
fi 

mkdir -p "$ROOT/logs"

cd "$ROOT" || 1

"$PY" -m creditcard_analysis.clean_data.clean --source csv_url \
>> "$ROOT/logs/clean_data.log" 2>&1

