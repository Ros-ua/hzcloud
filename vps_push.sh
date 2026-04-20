#!/bin/bash
# ─────────────────────────────────────────────
# VPS Stats Push  |  github.com gist
# Запускается по cron, пушит статистику в Gist
# ─────────────────────────────────────────────

# ══════════════════════════════════════════════
#  ЗАПОЛНИ ЭТИ ДВЕ ПЕРЕМЕННЫЕ
# ══════════════════════════════════════════════
GITHUB_TOKEN=""   # PAT с правом gist
GIST_ID=""  # ID твоего Gist
# ══════════════════════════════════════════════

set -euo pipefail

# Определяем публичный IP сервера (используется как имя в дашборде)
SERVER_NAME=$(curl -sf --max-time 5 https://api.ipify.org \
  || curl -sf --max-time 5 https://ifconfig.me \
  || curl -sf --max-time 5 https://icanhazip.com \
  || hostname -I | awk '{print $1}')

# Определяем интерфейс
detect_iface() {
  for iface in eth0 ens3 ens18 enp1s0 venet0; do
    [ -d "/sys/class/net/$iface" ] && echo "$iface" && return
  done
  # Первый не-lo интерфейс
  ls /sys/class/net/ | grep -v '^lo$' | head -1
}

IFACE=$(detect_iface)

# vnstat JSON (месяцы)
VNSTAT_JSON=$(vnstat --json m -i "$IFACE" 2>/dev/null || echo '{}')

# Uptime
UPTIME_SEC=$(awk '{print int($1)}' /proc/uptime)
UPTIME_DAYS=$(( UPTIME_SEC / 86400 ))
UPTIME_H=$(( (UPTIME_SEC % 86400) / 3600 ))
UPTIME_M=$(( (UPTIME_SEC % 3600) / 60 ))
UPTIME="${UPTIME_DAYS}d ${UPTIME_H}h ${UPTIME_M}m"

# Load average
LOAD=$(cat /proc/loadavg | awk '{print $1","$2","$3}')

# Timestamp
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Hostname
HOST=$(hostname)

# Собираем JSON
PAYLOAD=$(cat <<JSON
{
  "server_name": "$SERVER_NAME",
  "hostname": "$HOST",
  "iface": "$IFACE",
  "uptime": "$UPTIME",
  "load": [$LOAD],
  "ts": "$TS",
  "vnstat": $VNSTAT_JSON
}
JSON
)

# Экранируем для JSON-в-JSON (содержимое файла в Gist)
ESCAPED=$(echo "$PAYLOAD" | python3 -c "
import sys, json
content = sys.stdin.read()
print(json.dumps(content))
")

# Пушим в Gist
curl -s -X PATCH \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.github.com/gists/$GIST_ID" \
  -d "{\"files\":{\"stats.json\":{\"content\":$ESCAPED}}}" \
  -o /dev/null

echo "[$TS] Pushed to gist $GIST_ID (iface: $IFACE)"
