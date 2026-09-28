#!/usr/bin/env python3
import hashlib
import logging
import os

from PIL import Image

logger = logging.getLogger(__name__)


def calculer_md5(filepath):
    """Calcule le hash MD5 d'un fichier"""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception:
        logger.exception("Erreur lors de la lecture de %s", filepath)
        return None


def calculer_hash_pixels(filepath):
    """Calcule un hash MD5 sur les pixels de l'image (ignore les métadonnées)"""
    try:
        with Image.open(filepath) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            pixels = img.tobytes()
            return hashlib.md5(pixels).hexdigest()
    except Image.UnidentifiedImageError:
        logger.info("Format non supporté par PIL, utilisation du hash MD5 binaire: %s", os.path.basename(filepath))
        return calculer_md5(filepath)
    except Exception:
        logger.exception("Erreur lors du calcul du hash pixels pour %s", filepath)
        return None


def formater_taille(taille_octets):
    """Formate la taille en octets en format lisible"""
    for unite in ['o', 'Ko', 'Mo', 'Go']:
        if taille_octets < 1024.0:
            return f"{taille_octets:.2f} {unite}"
        taille_octets /= 1024.0
    return f"{taille_octets:.2f} To"
