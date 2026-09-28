#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$BASE_DIR/update_code.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Début de la mise à jour du code" >> "$LOG_FILE"
cd "$BASE_DIR"

bash "$BASE_DIR/setup.sh" >> "$LOG_FILE" 2>&1

git fetch origin main >> "$LOG_FILE" 2>&1
if ! REMOTE=$(git rev-parse @{u} 2>/dev/null); then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Erreur: branche actuelle sans upstream configuré" >> "$LOG_FILE"
    exit 1
fi
LOCAL=$(git rev-parse @)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Le code est déjà à jour" >> "$LOG_FILE"
    exit 0
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Nouveaux changements détectés, pull origin main" >> "$LOG_FILE"
git pull origin main >> "$LOG_FILE" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Redémarrage du service upload_server" >> "$LOG_FILE"
if systemctl --user restart upload_server.service >> "$LOG_FILE" 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Service upload_server redémarré avec succès" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Échec du redémarrage du service upload_server" >> "$LOG_FILE"
    exit 1
fi
