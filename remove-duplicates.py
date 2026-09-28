#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de détection et suppression de photos en double
Compare les fichiers par leur hash MD5
Généré par Claude Sonnet 4.5
"""

import os
from collections import defaultdict
import logging

from hash_utils import calculer_md5, calculer_hash_pixels, formater_taille
from picframe_cache import supprimer_du_cache_picframe

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

# Mode de détection: 'md5' (défaut) ou 'pixels' (hash perceptuel)
DETECTION_MODE = 'pixels'


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Detecter et supprimer photos en double")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run", help="Afficher les doubles sans supprimer")
    parser.add_argument("--photo-dir", default=PHOTO_DIR, help="Répertoire à analyser")
    parser.add_argument("--mode", choices=["md5", "pixels"], default=DETECTION_MODE, help="Mode de détection du hash")
    args = parser.parse_args()

    dry_run = args.dry_run
    photo_dir = args.photo_dir
    mode = args.mode

    logger.info("=== Détection des photos en double ===")
    logger.info("Répertoire analysé: %s", photo_dir)
    logger.info("Mode de détection: %s", mode)
    logger.info("Mode dry-run: %s", dry_run)

    if not os.path.isdir(photo_dir):
        logger.error("Erreur: Le répertoire '%s' n'existe pas", photo_dir)
        return

    fichiers_par_hash = defaultdict(list)

    logger.info("Analyse des fichiers en cours...")

    for filename in os.listdir(photo_dir):
        filepath = os.path.join(photo_dir, filename)

        if os.path.isfile(filepath) and filename.lower().endswith(IMAGE_EXTENSIONS):
            if mode == 'pixels':
                hash_value = calculer_hash_pixels(filepath)
                hash_type = "pixels-md5"
            else:
                hash_value = calculer_md5(filepath)
                hash_type = "MD5"

            if hash_value:
                fichiers_par_hash[hash_value].append(filepath)

    if not fichiers_par_hash:
        logger.info("Aucune photo trouvée dans le répertoire")
        return

    logger.info("Nombre total de photos analysées: %d", sum(len(files) for files in fichiers_par_hash.values()))

    total_doublons = 0
    espace_libere = 0

    for hash_value, fichiers in fichiers_par_hash.items():
        if len(fichiers) > 1:
            logger.info("Doublons trouvés (%s: %s):", hash_type, hash_value)

            for f in fichiers:
                taille = os.path.getsize(f)
                logger.info("  - %s (%s)", os.path.basename(f), formater_taille(taille))

            logger.info("  ✓ Conservé: %s", os.path.basename(fichiers[0]))

            for fichier_a_supprimer in fichiers[1:]:
                taille = os.path.getsize(fichier_a_supprimer)
                try:
                    if dry_run:
                        logger.info("  (dry-run) Supprimer du cache : %s", os.path.basename(fichier_a_supprimer))
                        logger.info("  (dry-run) Supprimer fichier : %s", os.path.basename(fichier_a_supprimer))
                    else:
                        supprimer_du_cache_picframe(fichier_a_supprimer)
                        os.remove(fichier_a_supprimer)
                        logger.info("  ✗ Supprimé: %s", os.path.basename(fichier_a_supprimer))
                        total_doublons += 1
                        espace_libere += taille
                except Exception:
                    logger.exception("  ⚠ Erreur lors de la suppression de %s", os.path.basename(fichier_a_supprimer))

            logger.info("")

    logger.info("=== Résumé ===")
    logger.info("Total de doublons supprimés: %d", total_doublons)
    if espace_libere > 0:
        logger.info("Espace disque libéré: %s", formater_taille(espace_libere))
    else:
        logger.info("Aucun doublon trouvé!")

    logger.info("Opération terminée!")


if __name__ == "__main__":
    main()
