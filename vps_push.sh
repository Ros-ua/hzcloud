#!/bin/bash
# ─────────────────────────────────────────────
# VPS Stats Push  |  github.com gist
# Запускается по cron, пушит статистику в Gist
# ─────────────────────────────────────────────

set -euo pipefail

# ── Конфиг ───────────────────────────────────
# Токен и Gist ID хранятся в /opt/vps-monitor.conf
# Создай его один раз: nano /opt/vps-monitor.conf
# Содержимое:
#   GITHUB_TOKEN="ghp_xxxx"
#   GIST_ID="xxxx"
GITHUB_TOKEN=""
GIST_ID=""

CONFIG_FILE="${VPS_MONITOR_CONF:-/opt/vps-monitor.conf}"
if [ -f "$CONFIG_FILE" ]; then
  # shellcheck source=/dev/null
  source "$CONFIG_FILE"
fi

if [ -z "$GITHUB_TOKEN" ] || [ -z "$GIST_ID" ]; then
  echo "ERROR: GITHUB_TOKEN и GIST_ID не заданы."
  echo "Создай файл $CONFIG_FILE с содержимым:"
  echo '  GITHUB_TOKEN="ghp_xxxx"'
  echo '  GIST_ID="xxxx"'
  exit 1
fi

# ── Публичный IP ──────────────────────────────
SERVER_NAME=$(
  curl -sf --max-time 5 https://api.ipify.org    ||
  curl -sf --max-time 5 https://ifconfig.me      ||
  curl -sf --max-time 5 https://icanhazip.com    ||
  ip route get 1.1.1.1 2>/dev/null | awk '{print $7; exit}' ||
  hostname -I | awk '{print $1}'
)

# ── Сетевой интерфейс ─────────────────────────
detect_iface() {
  local iface
  iface=$(ip route show default 2>/dev/null | awk '/default/{print $5; exit}')
  [ -n "$iface" ] && echo "$iface" && return
  for iface in eth0 eth1 ens3 ens18 enp1s0 enp3s0 eno1 venet0 bond0; do
    [ -d "/sys/class/net/$iface" ] && echo "$iface" && return
  done
  ls /sys/class/net/ | grep -v '^lo$' | head -1
}

IFACE=$(detect_iface)

# ── vnstat ────────────────────────────────────
VNSTAT_MONTHLY=$(vnstat --json m -i "$IFACE" 2>/dev/null || echo '{}')
VNSTAT_DAILY=$(  vnstat --json d -i "$IFACE" 2>/dev/null || echo '{}')

# Дата начала мониторинга — через аргумент, безопасно
VNSTAT_SINCE=$(python3 -c "
import json, sys
try:
    d = json.loads(sys.argv[1])
    c = d['interfaces'][0]['created']['date']
    print('{:04d}-{:02d}-{:02d}'.format(c['year'], c['month'], c['day']))
except Exception:
    print('')
" "$VNSTAT_MONTHLY" 2>/dev/null || echo "")

# ── Uptime ────────────────────────────────────
UPTIME_SEC=$(awk '{print int($1)}' /proc/uptime)
UPTIME_PRETTY="$(( UPTIME_SEC/86400 ))d $(( (UPTIME_SEC%86400)/3600 ))h $(( (UPTIME_SEC%3600)/60 ))m"

# ── Load average ──────────────────────────────
LOAD=$(awk '{print $1","$2","$3}' /proc/loadavg)

# ── RAM (байты) ───────────────────────────────
RAM_TOTAL=$(awk '/^MemTotal/{print $2*1024}'     /proc/meminfo)
RAM_AVAIL=$(awk '/^MemAvailable/{print $2*1024}' /proc/meminfo)
RAM_USED=$(( RAM_TOTAL - RAM_AVAIL ))

# ── Диск / (байты) ────────────────────────────
DISK_TOTAL=$(df -B1 / | awk 'NR==2{print $2}')
DISK_USED=$( df -B1 / | awk 'NR==2{print $3}')

# ── CPU usage (замер через /proc/stat за 0.5с) ─
CPU1=$(awk '/^cpu /{print $2,$3,$4,$5,$6,$7,$8}' /proc/stat)
sleep 0.5
CPU2=$(awk '/^cpu /{print $2,$3,$4,$5,$6,$7,$8}' /proc/stat)
CPU_USED=$(python3 -c "
a=[int(x) for x in '${CPU1}'.split()]
b=[int(x) for x in '${CPU2}'.split()]
dt=sum(b)-sum(a)
print(round(100*(dt-(b[3]-a[3]))/dt,1) if dt>0 else 0)
")

# ── CPU температура ───────────────────────────
CPU_TEMP=""
for zone in /sys/class/thermal/thermal_zone*/temp; do
  [ -f "$zone" ] || continue
  t=$(cat "$zone" 2>/dev/null || echo 0)
  CPU_TEMP=$(awk "BEGIN{printf \"%.1f\", $t/1000}")
  break
done

# ── TCP соединения ────────────────────────────
CONN_ESTAB=$(ss -tn state established 2>/dev/null | tail -n +2 | wc -l || echo 0)

# ── Процессы ──────────────────────────────────
PROC_COUNT=$(ps -e --no-headers 2>/dev/null | wc -l || echo 0)

# ── Hostname + timestamp ──────────────────────
HOST=$(hostname)
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ── Сборка JSON ───────────────────────────────
python3 -c "
import json, sys

payload = {
    'server_name': '$SERVER_NAME',
    'hostname':    '$HOST',
    'iface':       '$IFACE',
    'uptime':      '$UPTIME_PRETTY',
    'uptime_sec':  int('$UPTIME_SEC'),
    'load':        [float(x) for x in '$LOAD'.split(',')],
    'ts':          '$TS',
    'since':       '$VNSTAT_SINCE',
    'ram': {
        'total': int('$RAM_TOTAL'),
        'used':  int('$RAM_USED'),
    },
    'disk': {
        'total': int('$DISK_TOTAL'),
        'used':  int('$DISK_USED'),
    },
    'cpu': {
        'used_pct': float('$CPU_USED'),
        'temp_c':   float('$CPU_TEMP') if '$CPU_TEMP' else None,
    },
    'conns': int('$CONN_ESTAB'),
    'procs': int('$PROC_COUNT'),
    'vnstat_monthly': json.loads(sys.argv[1]),
    'vnstat_daily':   json.loads(sys.argv[2]),
}

outer = json.dumps({'files': {'stats.json': {'content': json.dumps(payload)}}})
print(outer)
" "$VNSTAT_MONTHLY" "$VNSTAT_DAILY" > /tmp/vps_gist_payload.json

# ── Пуш в Gist ────────────────────────────────
curl -s -X PATCH \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.github.com/gists/$GIST_ID" \
  --data-binary @/tmp/vps_gist_payload.json \
  -o /dev/null

rm -f /tmp/vps_gist_payload.json

echo "[$TS] Pushed to gist $GIST_ID (iface: $IFACE, uptime: $UPTIME_PRETTY, since: $VNSTAT_SINCE)"
