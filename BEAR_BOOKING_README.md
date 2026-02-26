# Moniteur de Réservation d'Observation des Ours

Moniteur automatisé pour vérifier la disponibilité de réservation pour l'observation des ours noirs à Essipit. S'exécute quotidiennement à 17h sur une Raspberry Pi et envoie un email d'alerte quand la réservation devient disponible.

## Fonctionnalités

- ✅ Vérifie quotidiennement à 17h la disponibilité sur https://vacancesessipit.com/autres-activites/observation-de-lours-noir/
- ✅ Détecte si le bouton "Réservez maintenant" a un lien actif (pas `#`)
- ✅ Envoie un email d'alerte à alistef@laposte.net quand la réservation devient disponible
-    Évite les emails doublons (une alerte par occurrence de disponibilité)
- ✅ Logs détaillés pour chaque exécution
- ✅ Pas de dépendances lourdes (requests + BeautifulSoup uniquement)
- ✅ Dépendances isolées et gestionnées via `uv` (déjà installé sur la Raspberry Pi)

## Fichiers

- **check_bear_booking.py** - Script principal
- **check-bear-booking.service** - Service systemd
- **check-bear-booking.timer** - Timer systemd (exécution quotidienne à 17h)
- **.env.example** - Template de configuration (copier en `.env` et remplir)
- **install.sh** - Script d'installation automatisée
- **INSTALLATION.md** - Guide d'installation détaillé

## Installation rapide

```bash
# Sur la Raspberry Pi:
cd ~/picadre
# le script utilise uv pour gérer les dépendances (requests, beautifulsoup4)
sudo bash install.sh

# Puis éditer le fichier .env avec votre mot de passe laPoste:
nano ~/.env

# Vérifier que tout fonctionne:
sudo systemctl status check-bear-booking.timer
# (le service lance le script avec `uv run`)
```

## Configuration requise

- **Email**: alistef@laposte.net
- **Serveur SMTP**: smtp.laposte.net:587
- **Mot de passe**: À fournir dans le fichier `.env`
- **Heure d'exécution**: 17:00 quotidiennement (configurable)

## Logs

- **Systemd journal**: `journalctl -u check-bear-booking.service -f`
- **Fichier log**: `~/picadre/check_bear_booking.log`

## Gestion

```bash
# Voir le statut
sudo systemctl status check-bear-booking.timer

# Voir les prochaines exécutions
sudo systemctl list-timers check-bear-booking.timer

# Arrêter temporairement
sudo systemctl stop check-bear-booking.timer

# Redémarrer
sudo systemctl restart check-bear-booking.timer

# Arrêter définitivement (sans démarrage au redémarrage)
sudo systemctl disable check-bear-booking.timer
```

## Dépannage

- Voir `INSTALLATION.md` pour le dépannage complet
- Script teste accessible avec `~/picadre/check_bear_booking.py`
- Les logs indiquent exactement où sont les problèmes

## Réinitialisation

Si vous avez reçu l'email et voulez être alerté à nouveau:
```bash
rm ~/.bear_booking_sent
```

Cela réinitialise le système de suivi d'alerte.
