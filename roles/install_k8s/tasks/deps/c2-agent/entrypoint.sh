#!/bin/sh
set -e

CALLBACK_HOST="${C2_CALLBACK_HOST:-127.0.0.1}"
CALLBACK_PORT="${C2_CALLBACK_PORT:-80}"
INTERVAL="${C2_CALLBACK_INTERVAL:-60}"
JITTER="${C2_CALLBACK_JITTER:-20}"

CALLBACK_URL="http://${CALLBACK_HOST}:${CALLBACK_PORT}/login"

echo "[*] C2 agent starting"
echo "[*] Callback target: ${CALLBACK_URL}"
echo "[*] Interval: ${INTERVAL}s  Jitter: +${JITTER}s"

while true; do
    curl -sf \
        -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
        -H "Accept: application/json" \
        --connect-timeout 10 \
        --max-time 30 \
        "${CALLBACK_URL}" > /dev/null 2>&1 || true

    JITTER_VAL=$(awk -v j="${JITTER}" 'BEGIN { srand(); printf "%d", rand() * j }')
    SLEEP_TIME=$(( INTERVAL + JITTER_VAL ))
    echo "[*] Sleeping ${SLEEP_TIME}s"
    sleep "${SLEEP_TIME}"
done
