#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script d'analyse détaillée de deux images pour identifier les différences
"""

import os
import hashlib
import subprocess
from PIL import Image
import sys

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

def analyser_images(file1, file2):
    print("=== Analyse détaillée des deux images ===")
    print(f"Fichier 1: {file1}")
    print(f"Fichier 2: {file2}")
    print()

    # Vérifier l'existence des fichiers
    if not os.path.exists(file1):
        print(f"Erreur: {file1} n'existe pas")
        return
    if not os.path.exists(file2):
        print(f"Erreur: {file2} n'existe pas")
        return

    # Taille des fichiers
    taille1 = os.path.getsize(file1)
    taille2 = os.path.getsize(file2)
    print(f"Taille fichier 1: {taille1} octets")
    print(f"Taille fichier 2: {taille2} octets")
    print(f"Différence de taille: {abs(taille1 - taille2)} octets")
    print()

    # Hash MD5
    md5_1 = calculer_md5(file1)
    md5_2 = calculer_md5(file2)
    print(f"MD5 fichier 1: {md5_1}")
    print(f"MD5 fichier 2: {md5_2}")
    print(f"Hash identiques: {md5_1 == md5_2}")
    print()

    # Analyse avec PIL
    try:
        img1 = Image.open(file1)
        img2 = Image.open(file2)

        print("=== Propriétés des images ===")
        print(f"Format 1: {img1.format}")
        print(f"Format 2: {img2.format}")
        print(f"Mode 1: {img1.mode}")
        print(f"Mode 2: {img2.mode}")
        print(f"Taille 1: {img1.size}")
        print(f"Taille 2: {img2.size}")
        print()

        # Vérifier si les pixels sont identiques
        if img1.size == img2.size and img1.mode == img2.mode:
            pixels_identiques = list(img1.getdata()) == list(img2.getdata())
            print(f"Pixels identiques: {pixels_identiques}")
        else:
            print("Les images ont des dimensions ou modes différents")

        # Métadonnées EXIF
        print("\n=== Métadonnées ===")
        exif1 = img1.info if hasattr(img1, 'info') else {}
        exif2 = img2.info if hasattr(img2, 'info') else {}

        print(f"Métadonnées 1: {exif1}")
        print(f"Métadonnées 2: {exif2}")
        print(f"Métadonnées identiques: {exif1 == exif2}")

        img1.close()
        img2.close()

    except Exception as e:
        print(f"Erreur lors de l'analyse PIL: {e}")

    # Analyse binaire détaillée
    print("\n=== Analyse binaire ===")
    try:
        with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
            data1 = f1.read()
            data2 = f2.read()

            if data1 == data2:
                print("Les fichiers sont identiques au niveau binaire")
            else:
                # Trouver les premières différences
                min_len = min(len(data1), len(data2))
                diff_pos = None
                for i in range(min_len):
                    if data1[i] != data2[i]:
                        diff_pos = i
                        break

                if diff_pos is not None:
                    print(f"Première différence à la position {diff_pos}")
                    print(f"Octet fichier 1: 0x{data1[diff_pos]:02x} ({data1[diff_pos]})")
                    print(f"Octet fichier 2: 0x{data2[diff_pos]:02x} ({data2[diff_pos]})")

                    # Afficher le contexte autour de la différence
                    start = max(0, diff_pos - 10)
                    end = min(min_len, diff_pos + 10)
                    print(f"Contexte fichier 1: {data1[start:end].hex()}")
                    print(f"Contexte fichier 2: {data2[start:end].hex()}")

                if len(data1) != len(data2):
                    print(f"Longueurs différentes: {len(data1)} vs {len(data2)}")

    except Exception as e:
        print(f"Erreur lors de l'analyse binaire: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python analyse_images.py <fichier1> <fichier2>")
        sys.exit(1)

    analyser_images(sys.argv[1], sys.argv[2])