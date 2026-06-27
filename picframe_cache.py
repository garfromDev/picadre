#!/usr/bin/env python3
import logging
import os
import sqlite3

logger = logging.getLogger(__name__)

POSSIBLE_CACHE_PATHS = [
    "/home/picadre/.picframe/picframe.db",
    "/home/picadre/.cache/picframe/picframe.db",
    os.path.expanduser("~/.picframe/picframe.db"),
    os.path.expanduser("~/.cache/picframe/picframe.db"),
]


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

    filepath = os.path.abspath(filepath)
    folder_path = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    name_without_ext = os.path.splitext(filename)[0]
    ext = os.path.splitext(filename)[1][1:] if '.' in filename else ''

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT folder_id FROM folder WHERE name = ?", (folder_path,))
            folder_result = cursor.fetchone()
            if not folder_result:
                logger.debug("Dossier %s non trouvé dans le cache", folder_path)
                return False

            cursor.execute(
                "SELECT file_id FROM file WHERE folder_id = ? AND basename = ? AND extension = ?",
                (folder_result[0], name_without_ext, ext)
            )
            file_result = cursor.fetchone()
            if not file_result:
                logger.debug("Fichier %s non trouvé dans le cache", filename)
                return False

            cursor.execute("DELETE FROM meta WHERE file_id = ?", (file_result[0],))
            cursor.execute("DELETE FROM file WHERE file_id = ?", (file_result[0],))

        logger.info("  ✓ Entrée supprimée du cache picframe: %s", filename)
        return True

    except sqlite3.Error as e:
        logger.error("Erreur lors de l'accès au cache picframe: %s", e)
        return False
    except Exception as e:
        logger.exception("Erreur inattendue lors de la suppression du cache: %s", e)
        return False
