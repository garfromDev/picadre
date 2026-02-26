#!/bin/bash
# Script d'installation automatisée du moniteur de réservation d'observation des ours
# À exécuter sur la Raspberry Pi

set -e  # Arrêter en cas d'erreur

echo "================================"
echo "Installation du moniteur de réservation"
echo "================================"

# Vérifier qu'on est en root pour les opérations systemd
if [ "$EUID" -ne 0 ]; then
   echo "⚠ Certaines étapes nécessitent sudo"
fi

# Vérifier Python3
if ! command -v python3 &> /dev/null; then
    echo "✗ Python3 n'est pas installé"
    echo "Installation: sudo apt install python3 python3-pip"
    exit 1
fi
echo "✓ Python3 trouvé: $(python3 --version)"

# Vérifier que `uv` est disponible et s'en servir pour isoler les dépendances
 echo ""
 if ! command -v uv &> /dev/null; then
     echo "✗ uv n'est pas installé. Installez-le (https://docs.astral.sh/uv).
     sudo apt install python3-pip && pip3 install uv  # si nécessaire"
     exit 1
 fi
 echo "✓ uv trouvé: $(uv --version 2>/dev/null || echo '(version inconnue)')"
 
 echo ""
 echo "Déclaration des dépendances dans le script via uv..."
 # uv add --script ajoutera un en‑tête metadata dans le fichier
 SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
 uv add --script "$SCRIPT_DIR/check_bear_booking.py" requests beautifulsoup4 || true
 echo "✓ Dépendances déclarées (requests, beautifulsoup4)"

# Créer le répertoire picadre
PICADRE_DIR="$HOME/picadre"
if [ ! -d "$PICADRE_DIR" ]; then
    mkdir -p "$PICADRE_DIR"
    echo "✓ Répertoire créé: $PICADRE_DIR"
else
    echo "✓ Répertoire existe: $PICADRE_DIR"
fi

# Rendre le script exécutable sur place (pas de copie nécessaire)
 echo ""
 echo "Préparation du script..."
 SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
 chmod +x "$SCRIPT_DIR/check_bear_booking.py"
 echo "✓ Script marqué exécutable"

# Créer le fichier .env
if [ ! -f "$PICADRE_DIR/.env" ]; then
    cp "$SCRIPT_DIR/.env.example" "$PICADRE_DIR/.env"
    chmod 600 "$PICADRE_DIR/.env"
    echo "✓ Fichier .env créé (MODIFICATION REQUISE: insérer votre mot de passe)"
else
    echo "✓ Fichier .env existe déjà"
fi

# Installer les services systemd
if [ "$EUID" -eq 0 ]; then
    echo ""
    echo "Installation des services systemd..."
    
    # Adapter les chemins dans les fichiers systemd pour l'utilisateur courant
    ACTUAL_USER="${SUDO_USER:-$USER}"
    ACTUAL_HOME=$(eval echo ~$ACTUAL_USER)
    
    sed "s|/home/pi|$ACTUAL_HOME|g" "$SCRIPT_DIR/check-bear-booking.service" | \
        sed "s|User=pi|User=$ACTUAL_USER|g" > /tmp/check-bear-booking.service
    sed "s|/home/pi|$ACTUAL_HOME|g" "$SCRIPT_DIR/check-bear-booking.timer" > /tmp/check-bear-booking.timer
    
    cp /tmp/check-bear-booking.service /etc/systemd/system/
    cp /tmp/check-bear-booking.timer /etc/systemd/system/
    rm /tmp/check-bear-booking.service /tmp/check-bear-booking.timer
    
    systemctl daemon-reload
    echo "✓ Services systemd installés"
    
    # Offrir d'activer le timer
    echo ""
    echo "Voulez-vous activer le timer maintenant? (y/n)"
    read -r response
    if [[ "$response" == "y" || "$response" == "Y" ]]; then
        systemctl enable check-bear-booking.timer
        systemctl start check-bear-booking.timer
        echo "✓ Timer activé et démarré"
        echo ""
        echo "Prochaines exécutions:"
        systemctl list-timers check-bear-booking.timer
    else
        echo "Installation complète, mais timer non activé"
        echo "Pour l'activer plus tard: sudo systemctl enable --now check-bear-booking.timer"
    fi
else
    echo "⚠ Installation des services systemd ignorée (requiert sudo)"
    echo "À exécuter manuellement:"
    echo "  sudo cp check-bear-booking.service /etc/systemd/system/"
    echo "  sudo cp check-bear-booking.timer /etc/systemd/system/"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl enable --now check-bear-booking.timer"
fi

echo ""
echo "================================"
echo "✓ Installation terminée!"
echo "================================"
echo ""
echo "ÉTAPES RESTANTES:"
echo "1. Éditer le fichier: $PICADRE_DIR/.env"
echo "   → Remplacer 'votre_mot_de_passe_ici' par votre mot de passe laPoste"
echo ""
echo "2. Tester le script : (via uv run)"
echo "   cd $PICADRE_DIR && uv run check_bear_booking.py"
echo ""
echo "3. Vérifier le timer:"
echo "   sudo systemctl list-timers check-bear-booking.timer"
echo "   sudo journalctl -u check-bear-booking.service -f"
echo ""
echo "Documentation complète: $SCRIPT_DIR/INSTALLATION.md"
