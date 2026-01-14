#!/bin/bash 

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"&& pwd)"
PY="$ROOT/.venv/bin/python"

echo "$(date) [cron] test_script.sh 執行中" >> /tmp/cron_debug.log 

if [ ! -x "$PY" ]; then 
    echo "$(date) [cron] 找不到"$PY"，請先建立虛擬環境" >> /tmp/cron_debug.log
    exit 1
fi 

mkdir -p "$ROOT/script_logs"

cd "$ROOT" || 1

"$PY" -m creditcard_analysis.clean_data.test_clean_data --source csv_url \
>> "$ROOT/script_logs/test.log" 2>&1