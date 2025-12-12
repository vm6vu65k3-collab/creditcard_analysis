#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "$(date) [cron] run_clean_data.sh 執行中" >> /tmp/cron_debug.log

cd "$SCRIPT_DIR" || exit 1

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "$(date) [cron] 找不到 .venv，請先建立虛擬環境" >> /tmp/cron_debug.log
    exit 1
fi

mkdir -p logs
python -m clean_data.clean >> "$SCRIPT_DIR/logs/clean_data.log" 2>&1