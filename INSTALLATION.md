# Installation du script de surveillance de réservation d'observation des ours

## Prérequis

### Python 3 et uv
```bash
sudo apt update
sudo apt install python3 python3-pip
# uv est déjà installé sur la Raspberry Pi; sinon installez-le via pip ou curl:
#   pip3 install uv
#   curl -LsSf https://astral.sh/uv/install.sh | sh
``` 

Les dépendances du script seront gérées automatiquement par uv (`requests` et `beautifulsoup4`).

### Créer le répertoire picadre (si pas encore fait)
```bash
mkdir -p ~/picadre
```

## Installation sur la Raspberry Pi

### 1. Préparer le script et l'environnement
```bash
# Créer le répertoire si nécessaire
mkdir -p ~/picadre

# Copier la configuration env et la modifier
cp .env.example ~/picadre/.env
nano ~/picadre/.env
# → Remplacer `votre_mot_de_passe_ici` par votre mot de passe laPoste

chmod 600 ~/picadre/.env  # Protéger le fichier de mot de passe

# Rendre le script exécutable (il reste dans le dossier courant)
chmod +x ./check_bear_booking.py

# Déclarer les dépendances avec uv
uv add --script ./check_bear_booking.py requests beautifulsoup4
```

### 2. Installer le service systemd
Le service utilise `uv run` pour lancer le script dans un environnement isolé, donc uv doit être présent dans le `PATH` du service (le fichier fourni s'en charge déjà).
```bash
# Copier les fichiers systemd
sudo cp check-bear-booking.service /etc/systemd/system/
sudo cp check-bear-booking.timer /etc/systemd/system/

# Recharger systemd
sudo systemctl daemon-reload

# Activer le timer (il restera actif au redémarrage)
sudo systemctl enable check-bear-booking.timer

# Démarrer le timer
sudo systemctl start check-bear-booking.timer
```

### 3. Vérifier que tout fonctionne
```bash
# Voir le statut du timer
sudo systemctl status check-bear-booking.timer

# Voir les prochaines exécutions
sudo systemctl list-timers check-bear-booking.timer

# Voir les logs récents
sudo journalctl -u check-bear-booking.service -n 50 -f

# Tester manuellement le script (avec uv)
cd ~/picadre
uv run check_bear_booking.py
```

## Configuration

### Changer l'email de destination
Modifier la ligne `EMAIL_TO` dans `check_bear_booking.py`

### Changer l'heure d'exécution
Modifier la ligne `OnCalendar` dans `check-bear-booking.timer`
Exemples:
- `*-*-* 17:00:00` → Tous les jours à 17h
- `*-*-* 09:00:00` → Tous les jours à 9h
- `Mon,Wed,Fri *-*-* 17:00:00` → Lundi, mercredi, vendredi à 17h

## Gestion du service

### Vérifier le statut
```bash
sudo systemctl status check-bear-booking.timer
sudo systemctl status check-bear-booking.service
```

### Voir les logs
```bash
# Logs du timer
sudo journalctl -u check-bear-booking.timer -n 20

# Logs du service (exécutions)
sudo journalctl -u check-bear-booking.service -n 50

# Logs en temps réel
sudo journalctl -u check-bear-booking.service -f
```

### Désactiver le service
```bash
sudo systemctl stop check-bear-booking.timer
sudo systemctl disable check-bear-booking.timer
```

### Réactiver le service
```bash
sudo systemctl start check-bear-booking.timer
```

### Redémarrer le service après modification
```bash
sudo systemctl daemon-reload
sudo systemctl restart check-bear-booking.timer
```

## Fichiers de log

Les logs sont disponibles dans deux endroits:
1. **Journal systemd**: `journalctl -u check-bear-booking.service`
2. **Fichier log**: `~/picadre/check_bear_booking.log`

## Réinitialisation de l'alerte

Si vous avez reçu l'email et que vous voulez le recevoir à nouveau (si la réservation redevient indisponible puis disponible):
```bash
rm ~/picadre/.bear_booking_sent
```

## Vérification du mot de passe SMTP

Pour tester votre configuration SMTP:
```bash
python3 -c "
import smtplib
import os
try:
    smtp_password = os.getenv('SMTP_PASSWORD')
    with smtplib.SMTP('smtp.laposte.net', 587, timeout=10) as server:
        server.starttls()
        server.login('alistef@laposte.net', smtp_password)
    print('✓ Connexion SMTP réussie!')
except Exception as e:
    print(f'✗ Erreur: {e}')
"
```
(Attention: source d'abord le fichier .env avec `export $(cat ~/picadre/.env | xargs)`)

## Dépannage

### Le timer ne s'exécute pas
```bash
# Vérifier que le timer est actif
sudo systemctl list-timers

# Vérifier les logs
sudo journalctl -u check-bear-booking.timer -n 20
```

### Pas d'email reçu
1. Vérifier le mot de passe dans ~/.env
2. Vérifier les logs: `journalctl -u check-bear-booking.service`
3. Tester manuellement le script

### Script ne trouve pas le bouton
Le HTML de la page peut avoir changé. Exécuter le script manuellement pour voir le message d'erreur exact et m'en informer.
