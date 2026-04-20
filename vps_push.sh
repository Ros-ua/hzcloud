#!/bin/bash
# ─────────────────────────────────────────────
# VPS Stats Push  |  github.com gist
# Запускается по cron, пушит статистику в Gist
# ─────────────────────────────────────────────

# ══════════════════════════════════════════════
#  ЗАПОЛНИ ЭТИ ДВЕ ПЕРЕМЕННЫЕ
# ══════════════════════════════════════════════
GITHUB_TOKEN="ghp_XXXXXXXXXXXXXXXXXXXXX"   # PAT с правом gist
GIST_ID="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # ID твоего Gist
# ══════════════════════════════════════════════

set -euo pipefail

# Публичный IP сервера
SERVER_NAME=$(curl -sf --max-time 5 https://api.ipify.org \
  || curl -sf --max-time 5 https://ifconfig.me \
  || curl -sf --max-time 5 https://icanhazip.com \
  || hostname -I | awk '{print $1}')

# Определяем интерфейс
detect_iface() {
  for iface in eth0 ens3 ens18 enp1s0 venet0; do
    [ -d "/sys/class/net/$iface" ] && echo "$iface" && return
  done
  ls /sys/class/net/ | grep -v '^lo$' | head -1
}

IFACE=$(detect_iface)

# vnstat — месяцы и дни отдельно
VNSTAT_MONTHLY=$(vnstat --json m -i "$IFACE" 2>/dev/null || echo '{}')
VNSTAT_DAILY=$(  vnstat --json d -i "$IFACE" 2>/dev/null || echo '{}')

# Дата начала мониторинга (когда vnstat начал считать этот интерфейс)
VNSTAT_SINCE=$(python3 -c "
import json, sys
try:
    d = json.loads('$VNSTAT_MONTHLY'.replace(\"'\", '\"'))
    iface = d['interfaces'][0]
    c = iface['created']['date']
    print('{:04d}-{:02d}-{:02d}'.format(c['year'], c['month'], c['day']))
except:
    print('')
" 2>/dev/null || echo "")

# Uptime
UPTIME_SEC=$(awk '{print int($1)}' /proc/uptime)
UPTIME_DAYS=$(( UPTIME_SEC / 86400 ))
UPTIME_H=$(( (UPTIME_SEC % 86400) / 3600 ))
UPTIME_M=$(( (UPTIME_SEC % 3600) / 60 ))
UPTIME="${UPTIME_DAYS}d ${UPTIME_H}h ${UPTIME_M}m"

# Load average
LOAD=$(awk '{print $1","$2","$3}' /proc/loadavg)

# Timestamp
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Hostname
HOST=$(hostname)

# Собираем итоговый JSON через python3 — безопасно экранирует всё
python3 -c "
import json, sys

payload = {
    'server_name': '$SERVER_NAME',
    'hostname':    '$HOST',
    'iface':       '$IFACE',
    'uptime':      '$UPTIME',
    'load':        [float(x) for x in '$LOAD'.split(',')],
    'ts':          '$TS',
    'since':       '$VNSTAT_SINCE',
    'vnstat_monthly': json.loads(sys.argv[1]),
    'vnstat_daily':   json.loads(sys.argv[2]),
}

outer = json.dumps({'files': {'stats.json': {'content': json.dumps(payload)}}})
print(outer)
" "$VNSTAT_MONTHLY" "$VNSTAT_DAILY" > /tmp/vps_gist_payload.json

# Пушим в Gist
curl -s -X PATCH \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.github.com/gists/$GIST_ID" \
  --data-binary @/tmp/vps_gist_payload.json \
  -o /dev/null

rm -f /tmp/vps_gist_payload.json

echo "[$TS] Pushed to gist $GIST_ID (iface: $IFACE, since: $VNSTAT_SINCE)"
