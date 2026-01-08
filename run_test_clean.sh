#!/bin/bash 

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"&& pwd)"
PY="$ROOT/.venv/bin/python"

echo "ROOT=$ROOT"
echo "PY=$PY"

echo "$(date) [cron] run_test_clean.sh 執行中"  >> /tmp/cron_debug.log

if [ ! -x "$PY" ]; then 
    echo "$(date) [cron] 找不到"$PY"，請先建立虛擬環境" >> /tmp/cron_debug.log 
    exit || 1
fi 

mkdir -p "$ROOT/script_logs"

cd "$ROOT" || 1 

"$PY" -m creditcard_analysis.clean_data.test_clean --source csv_url \
>> "$ROOT/script_logs/clean_data.log" 2>&1