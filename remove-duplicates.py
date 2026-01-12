#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de détection et suppression de photos en double
Compare les fichiers par leur hash MD5
Généré par Claude Sonnet 4.5
"""

import os
import hashlib
from collections import defaultdict
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)
logger = logging.getLogger(__name__)

# Répertoire à analyser (à modifier selon vos besoins)
PHOTO_DIR = "/home/picadre/Pictures"

# Extensions d'images supportées
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.heic')

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

def formater_taille(taille_octets):
    """Formate la taille en octets en format lisible"""
    for unite in ['o', 'Ko', 'Mo', 'Go']:
        if taille_octets < 1024.0:
            return f"{taille_octets:.2f} {unite}"
        taille_octets /= 1024.0
    return f"{taille_octets:.2f} To"

def main():
    logger.info("=== Détection des photos en double ===")
    logger.info("Répertoire analysé: %s", PHOTO_DIR)
    
    # Vérifier que le répertoire existe
    if not os.path.isdir(PHOTO_DIR):
        logger.error("Erreur: Le répertoire '%s' n'existe pas", PHOTO_DIR)
        return
    
    # Dictionnaire pour stocker les fichiers par hash
    fichiers_par_hash = defaultdict(list)
    
    logger.info("Analyse des fichiers en cours...")
    
    # Parcourir uniquement les fichiers du répertoire (pas les sous-dossiers)
    for filename in os.listdir(PHOTO_DIR):
        filepath = os.path.join(PHOTO_DIR, filename)
        
        # Vérifier que c'est un fichier et qu'il a une extension image
        if os.path.isfile(filepath) and filename.lower().endswith(IMAGE_EXTENSIONS):
            md5_hash = calculer_md5(filepath)
            if md5_hash:
                fichiers_par_hash[md5_hash].append(filepath)
    
    if not fichiers_par_hash:
        logger.info("Aucune photo trouvée dans le répertoire")
        return
    
    logger.info("Nombre total de photos analysées: %d", sum(len(files) for files in fichiers_par_hash.values()))
    
    # Rechercher et supprimer les doublons
    total_doublons = 0
    espace_libere = 0
    
    for md5_hash, fichiers in fichiers_par_hash.items():
        if len(fichiers) > 1:
            logger.info("Doublons trouvés (MD5: %s):", md5_hash)
            
            # Afficher tous les fichiers du groupe
            for f in fichiers:
                taille = os.path.getsize(f)
                logger.info("  - %s (%s)", os.path.basename(f), formater_taille(taille))
            
            # Garder le premier, supprimer les autres
            logger.info("  ✓ Conservé: %s", os.path.basename(fichiers[0]))
            
            for fichier_a_supprimer in fichiers[1:]:
                taille = os.path.getsize(fichier_a_supprimer)
                try:
                    os.remove(fichier_a_supprimer)
                    logger.info("  ✗ Supprimé: %s", os.path.basename(fichier_a_supprimer))
                    total_doublons += 1
                    espace_libere += taille
                except Exception:
                    logger.exception("  ⚠ Erreur lors de la suppression de %s", os.path.basename(fichier_a_supprimer))
            
            logger.info("")
    
    # Résumé
    logger.info("=== Résumé ===")
    logger.info("Total de doublons supprimés: %d", total_doublons)
    if espace_libere > 0:
        logger.info("Espace disque libéré: %s", formater_taille(espace_libere))
    else:
        logger.info("Aucun doublon trouvé!")
    
    logger.info("Opération terminée!")

if __name__ == "__main__":
    main()
