#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$BASE_DIR/setup.log"
SERVICE_DIR="$HOME/.config/systemd/user"

mkdir -p "$SERVICE_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log "Lancement de setup.sh"
cd "$BASE_DIR"

reload_needed=0
copy_unit() {
    local unit="$1"
    local src="$BASE_DIR/$unit"
    local dst="$SERVICE_DIR/$unit"

    if [ ! -f "$dst" ] || ! cmp -s "$src" "$dst"; then
        cp "$src" "$dst"
        log "Installé ou mis à jour $unit"
        reload_needed=1
    else
        log "$unit déjà présent"
    fi
}

copy_unit "upload_server.service"
copy_unit "update_code.service"
copy_unit "update_code.timer"

if [ "$reload_needed" -ne 0 ]; then
    log "Reload systemd user daemon"
    systemctl --user daemon-reload >> "$LOG_FILE" 2>&1
fi

enable_unit() {
    local unit="$1"
    local enable_args="$2"

    if systemctl --user is-enabled "$unit" >/dev/null 2>&1; then
        log "$unit déjà activé"
    else
        systemctl --user enable $enable_args "$unit" >> "$LOG_FILE" 2>&1
        log "Activation de $unit"
    fi
}

enable_unit "upload_server.service" ""
enable_unit "update_code.service" ""
enable_unit "update_code.timer" "--now"

if ! systemctl --user is-active upload_server.service >/dev/null 2>&1; then
    log "Démarrage/reprise de upload_server.service"
    systemctl --user restart upload_server.service >> "$LOG_FILE" 2>&1 || log "Échec du redémarrage de upload_server.service"
else
    log "upload_server.service est déjà actif"
fi

log "setup.sh terminé"
