#!/usr/bin/env python3
# uv: add requests beautifulsoup4
"""
Script de vérification de disponibilité de réservation pour l'observation des ours
Vérifie si le bouton "Réservez maintenant" sur la page a un lien actif (pas "#")
Si actif, envoie un email d'alerte à alistef@laposte.net
"""

import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import os
from datetime import datetime
from pathlib import Path

# Configuration
URL = "https://vacancesessipit.com/autres-activites/observation-de-lours-noir/"
EMAIL_TO = "alistef@laposte.net"
EMAIL_FROM = "alistef@laposte.net"
SMTP_SERVER = "smtp.laposte.net"
SMTP_PORT = 587

# Logging
LOG_DIR = Path.home() / "picadre"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "check_bear_booking.log"

# État - fichier pour tracker si on a déjà envoyé une alerte
STATE_FILE = LOG_DIR / ".bear_booking_sent"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def check_booking_availability():
    """
    Accède à la page et vérifie si le bouton "Réservez maintenant" a un lien actif
    
    Returns:
        tuple: (is_available: bool, href: str or None, error: str or None)
    """
    try:
        logger.info(f"Accès à {URL}")
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Chercher le bouton "Réservez maintenant"
        # Peut être un <a> ou un <button> contenant du texte similar
        button = None
        
        # Chercher un lien contenant le texte "Réservez maintenant"
        for element in soup.find_all(['a', 'button']):
            if 'Réservez maintenant' in element.get_text(strip=True):
                button = element
                break
        
        if not button:
            return False, None, "Bouton 'Réservez maintenant' non trouvé"
        
        # Si c'est un <button>, chercher le lien parent ou dans le <button>
        if button.name == 'button':
            parent_link = button.find_parent('a')
            if parent_link:
                button = parent_link
            else:
                # Peut-être que le bouton est un wrapper, chercher le lien dans le bouton
                link_in_button = button.find('a')
                if link_in_button:
                    button = link_in_button
        
        # Obtenir le href
        href = button.get('href', '#')
        logger.info(f"Bouton trouvé avec href: {href}")
        
        # Vérifier si le lien est actif (pas un "#")
        is_available = href and href != "#" and href.strip() != ""
        
        return is_available, href, None
        
    except requests.RequestException as e:
        error_msg = f"Erreur lors de l'accès à la page: {e}"
        logger.error(error_msg)
        return False, None, error_msg
    except Exception as e:
        error_msg = f"Erreur lors de l'analyse de la page: {e}"
        logger.error(error_msg)
        return False, None, error_msg


def send_email(subject, body):
    """
    Envoie un email via SMTP
    
    Args:
        subject: Sujet de l'email
        body: Corps de l'email
        
    Returns:
        bool: True si succès, False sinon
    """
    try:
        # Récupérer le mot de passe depuis la variable d'environnement
        smtp_password = os.getenv('SMTP_PASSWORD')
        if not smtp_password:
            logger.error("Variable d'environnement SMTP_PASSWORD non définie")
            return False
        
        logger.info(f"Envoi d'un email à {EMAIL_TO}")
        
        # Créer le message
        message = MIMEMultipart()
        message['From'] = EMAIL_FROM
        message['To'] = EMAIL_TO
        message['Subject'] = subject
        
        # Corps du message
        message.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Envoyer via SMTP
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(EMAIL_FROM, smtp_password)
            server.send_message(message)
        
        logger.info("Email envoyé avec succès")
        return True
        
    except smtplib.SMTPAuthenticationError:
        logger.error("Erreur SMTP: Authentification échouée (vérifier SMTP_PASSWORD)")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"Erreur SMTP: {e}")
        return False
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email: {e}")
        return False


def has_alert_been_sent():
    """Vérifie si une alerte a déjà été envoyée pour cette occurrence"""
    return STATE_FILE.exists()


def mark_alert_sent():
    """Marque qu'une alerte a été envoyée"""
    STATE_FILE.touch()


def clear_alert_sent():
    """Efface la marque d'alerte envoyée (réinitialise le système)"""
    if STATE_FILE.exists():
        STATE_FILE.unlink()


def main():
    """Fonction principale"""
    logger.info("=" * 60)
    logger.info("Vérification de disponibilité de réservation pour l'observation des ours")
    
    is_available, href, error = check_booking_availability()
    
    if error:
        logger.warning(f"Erreur: {error}")
        return
    
    if is_available:
        logger.info(f"✓ RÉSERVATION DISPONIBLE! Lien: {href}")
        
        # Vérifier si on a déjà envoyé une alerte
        if has_alert_been_sent():
            logger.info("Alerte déjà envoyée pour cette occurrence, pas d'envoi supplémentaire")
            return
        
        # Envoyer l'email
        subject = "Réservation disponible pour l'observation des ours"
        body = f"""Bonjour,

La réservation pour l'observation des ours noirs à Essipit est maintenant disponible!

Lien de réservation: {href}

Page: {URL}

Détails de l'offre Essipit:
- Visite avec guide expérimenté (1h30 à 2h)
- Observation de juin à septembre
- Tarif: 43 $/adulte, 23 $/enfant (6-17 ans)
- À 8 km de Tadoussac

Vérifiez les horaires de départ selon la période:
- 11 juin au 16 août: arrivée 18h15, départ 18h30
- 17 août au 20 septembre: arrivée 16h15, départ 16h45

Amusez-vous bien!

---
Email généré automatiquement par le script de surveillance
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        if send_email(subject, body):
            # mark_alert_sent()  on laisse la possibilité d'envoyer plusieurs alertes 
        else:
            logger.error("Impossible d'envoyer l'email")
    else:
        logger.info("✗ Réservation non disponible (lien = '#')")
        # Si les réservations redeviennent indisponibles, réinitialiser l'alerte
        clear_alert_sent()


if __name__ == "__main__":
    main()
