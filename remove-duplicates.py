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
    except Exception as e:
        print(f"Erreur lors de la lecture de {filepath}: {e}")
        return None

def formater_taille(taille_octets):
    """Formate la taille en octets en format lisible"""
    for unite in ['o', 'Ko', 'Mo', 'Go']:
        if taille_octets < 1024.0:
            return f"{taille_octets:.2f} {unite}"
        taille_octets /= 1024.0
    return f"{taille_octets:.2f} To"

def main():
    print("=== Détection des photos en double ===")
    print(f"Répertoire analysé: {PHOTO_DIR}\n")
    
    # Vérifier que le répertoire existe
    if not os.path.isdir(PHOTO_DIR):
        print(f"Erreur: Le répertoire '{PHOTO_DIR}' n'existe pas")
        return
    
    # Dictionnaire pour stocker les fichiers par hash
    fichiers_par_hash = defaultdict(list)
    
    print("Analyse des fichiers en cours...")
    
    # Parcourir uniquement les fichiers du répertoire (pas les sous-dossiers)
    for filename in os.listdir(PHOTO_DIR):
        filepath = os.path.join(PHOTO_DIR, filename)
        
        # Vérifier que c'est un fichier et qu'il a une extension image
        if os.path.isfile(filepath) and filename.lower().endswith(IMAGE_EXTENSIONS):
            md5_hash = calculer_md5(filepath)
            if md5_hash:
                fichiers_par_hash[md5_hash].append(filepath)
    
    if not fichiers_par_hash:
        print("Aucune photo trouvée dans le répertoire")
        return
    
    print(f"Nombre total de photos analysées: {sum(len(files) for files in fichiers_par_hash.values())}\n")
    
    # Rechercher et supprimer les doublons
    total_doublons = 0
    espace_libere = 0
    
    for md5_hash, fichiers in fichiers_par_hash.items():
        if len(fichiers) > 1:
            print(f"Doublons trouvés (MD5: {md5_hash}):")
            
            # Afficher tous les fichiers du groupe
            for f in fichiers:
                taille = os.path.getsize(f)
                print(f"  - {os.path.basename(f)} ({formater_taille(taille)})")
            
            # Garder le premier, supprimer les autres
            print(f"  ✓ Conservé: {os.path.basename(fichiers[0])}")
            
            for fichier_a_supprimer in fichiers[1:]:
                taille = os.path.getsize(fichier_a_supprimer)
                try:
                    os.remove(fichier_a_supprimer)
                    print(f"  ✗ Supprimé: {os.path.basename(fichier_a_supprimer)}")
                    total_doublons += 1
                    espace_libere += taille
                except Exception as e:
                    print(f"  ⚠ Erreur lors de la suppression de {os.path.basename(fichier_a_supprimer)}: {e}")
            
            print()
    
    # Résumé
    print("=== Résumé ===")
    print(f"Total de doublons supprimés: {total_doublons}")
    if espace_libere > 0:
        print(f"Espace disque libéré: {formater_taille(espace_libere)}")
    else:
        print("Aucun doublon trouvé!")
    
    print("\nOpération terminée!")

if __name__ == "__main__":
    main()
