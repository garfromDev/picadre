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
from PIL import Image
import imagehash
import sqlite3
from pathlib import Path

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
DETECTION_MODE = 'pixels'  # Changé pour utiliser le hash perceptuel par défaut

# Répertoires possibles du cache picframe
POSSIBLE_CACHE_PATHS = [
    "/home/picadre/.picframe/picframe.db",
    "/home/picadre/.cache/picframe/picframe.db",
    os.path.expanduser("~/.picframe/picframe.db"),
    os.path.expanduser("~/.cache/picframe/picframe.db"),
]

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

def calculer_hash_pixels(filepath):
    """Calcule un hash basé uniquement sur les pixels de l'image (ignore les métadonnées)"""
    try:
        with Image.open(filepath) as img:
            # Convertir en RGB si nécessaire pour normaliser
            if img.mode != 'RGB':
                img = img.convert('RGB')
            # Calculer le hash perceptuel (aHash - Average Hash)
            return str(imagehash.average_hash(img))
    except Exception:
        logger.exception("Erreur lors du calcul du hash pixels pour %s", filepath)
        return None

def calculer_hash_md5_pixels(filepath):
    """Calcule un hash MD5 basé uniquement sur les données de pixels brutes"""
    try:
        with Image.open(filepath) as img:
            # Convertir en RGB pour normaliser
            if img.mode != 'RGB':
                img = img.convert('RGB')
            # Obtenir les données de pixels brutes
            pixels = img.tobytes()
            return hashlib.md5(pixels).hexdigest()
    except Exception:
        logger.exception("Erreur lors du calcul du hash MD5 pixels pour %s", filepath)
        return None

def trouver_db_picframe():
    """Trouve le chemin de la base de données picframe"""
    for db_path in POSSIBLE_CACHE_PATHS:
        if os.path.exists(db_path):
            return db_path
    return None

def supprimer_du_cache_picframe(filepath):
    """Supprime une image du cache SQLite de picframe"""
    db_path = trouver_db_picframe()
    if not db_path:
        logger.warning("Base de données picframe non trouvée")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Normaliser le chemin du fichier
        filepath = os.path.abspath(filepath)
        
        # Récupérer le dossier et le nom du fichier
        folder_path = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        name_without_ext = os.path.splitext(filename)[0]
        ext = os.path.splitext(filename)[1][1:] if '.' in filename else ''
        
        # Chercher le folder_id
        cursor.execute(
            "SELECT folder_id FROM folder WHERE name = ?",
            (folder_path,)
        )
        folder_result = cursor.fetchone()
        
        if not folder_result:
            logger.debug("Dossier %s non trouvé dans le cache", folder_path)
            conn.close()
            return False
        
        folder_id = folder_result[0]
        
        # Chercher le file_id
        cursor.execute(
            "SELECT file_id FROM file WHERE folder_id = ? AND basename = ? AND extension = ?",
            (folder_id, name_without_ext, ext)
        )
        file_result = cursor.fetchone()
        
        if not file_result:
            logger.debug("Fichier %s non trouvé dans le cache", filename)
            conn.close()
            return False
        
        file_id = file_result[0]
        
        # Supprimer les métadonnées associées (les triggers supprimeront aussi les données)
        cursor.execute("DELETE FROM meta WHERE file_id = ?", (file_id,))
        
        # Supprimer l'entrée du fichier
        cursor.execute("DELETE FROM file WHERE file_id = ?", (file_id,))
        
        conn.commit()
        conn.close()
        
        logger.info("  ✓ Entrée supprimée du cache picframe: %s", filename)
        return True
        
    except sqlite3.Error as e:
        logger.error("Erreur lors de l'accès au cache picframe: %s", e)
        return False
    except Exception as e:
        logger.exception("Erreur inattendue lors de la suppression du cache: %s", e)
        return False

def main():
    logger.info("=== Détection des photos en double ===")
    logger.info("Répertoire analysé: %s", PHOTO_DIR)
    logger.info("Mode de détection: %s", DETECTION_MODE)
    
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
            if DETECTION_MODE == 'pixels':
                hash_value = calculer_hash_pixels(filepath)
                hash_type = "pHash"
            else:  # mode 'md5' (par défaut)
                hash_value = calculer_md5(filepath)
                hash_type = "MD5"
            
            if hash_value:
                fichiers_par_hash[hash_value].append(filepath)
    
    if not fichiers_par_hash:
        logger.info("Aucune photo trouvée dans le répertoire")
        return
    
    logger.info("Nombre total de photos analysées: %d", sum(len(files) for files in fichiers_par_hash.values()))
    
    # Rechercher et supprimer les doublons
    total_doublons = 0
    espace_libere = 0
    
    for hash_value, fichiers in fichiers_par_hash.items():
        if len(fichiers) > 1:
            logger.info("Doublons trouvés (%s: %s):", hash_type, hash_value)
            
            # Afficher tous les fichiers du groupe
            for f in fichiers:
                taille = os.path.getsize(f)
                logger.info("  - %s (%s)", os.path.basename(f), formater_taille(taille))
            
            # Garder le premier, supprimer les autres
            logger.info("  ✓ Conservé: %s", os.path.basename(fichiers[0]))
            
            for fichier_a_supprimer in fichiers[1:]:
                taille = os.path.getsize(fichier_a_supprimer)
                try:
                    # Supprimer du cache picframe avant de supprimer le fichier
                    supprimer_du_cache_picframe(fichier_a_supprimer)
                    
                    # Supprimer le fichier
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
