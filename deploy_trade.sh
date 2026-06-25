#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME="trade"
APP_DIR="/var/www/trade"
VENV_DIR="/var/www/trade/venv"
SERVICE_NAME="trade"
HEALTHCHECK_URL="http://127.0.0.1/trade/"
HEALTHCHECK_HOST="fabianopolone.com.br"
REQ_FILE="/var/www/trade/requirements.txt"
MANAGE_PY="/var/www/trade/manage.py"

PIP_BIN="$VENV_DIR/bin/pip"
PYTHON_BIN="$VENV_DIR/bin/python"

log() { printf '[%s] [%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$APP_NAME" "$*"; }
die() { log "ERRO: $*"; exit 1; }

command -v git >/dev/null 2>&1 || die "git nao encontrado"
command -v curl >/dev/null 2>&1 || die "curl nao encontrado"
command -v systemctl >/dev/null 2>&1 || die "systemctl nao encontrado"

[[ -d "$APP_DIR" ]] || die "App nao encontrada em $APP_DIR"
[[ -x "$PIP_BIN" ]] || die "pip nao encontrado em $PIP_BIN"
[[ -x "$PYTHON_BIN" ]] || die "python nao encontrado em $PYTHON_BIN"
[[ -f "$MANAGE_PY" ]] || die "manage.py nao encontrado"
[[ -f "$REQ_FILE" ]] || die "requirements.txt nao encontrado"

log "Instalando dependencias"
"$PIP_BIN" install -r "$REQ_FILE"

log "Verificando Django"
"$PYTHON_BIN" "$MANAGE_PY" check

log "Aplicando migracoes"
"$PYTHON_BIN" "$MANAGE_PY" migrate --noinput

log "Coletando static"
"$PYTHON_BIN" "$MANAGE_PY" collectstatic --noinput

log "Reiniciando servico"
systemctl restart "$SERVICE_NAME"
systemctl reload nginx

log "Aguardando resposta"
sleep 2
curl -fsS --max-time 10 "$HEALTHCHECK_URL" -H "Host: $HEALTHCHECK_HOST" >/dev/null

log "Deploy concluido"
