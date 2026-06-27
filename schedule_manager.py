#!/usr/bin/env python3
import json
import logging
import os
from datetime import date, timedelta

logger = logging.getLogger(__name__)

SCHEDULE_FILE = '/home/picadre/picadre/screen_schedule.json'


def load_schedule():
    """Charge les horaires depuis le fichier JSON"""
    try:
        with open(SCHEDULE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            'enabled': False,
            'on_time': '08:00',
            'off_time': '22:00'
        }


def save_schedule(schedule):
    """Sauvegarde les horaires dans le fichier JSON"""
    with open(SCHEDULE_FILE, 'w') as f:
        json.dump(schedule, f, indent=2)


def _paques(annee):
    """Dimanche de Pâques (algorithme de Butcher)."""
    a = annee % 19
    b = annee // 100
    c = annee % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mois = (h + l - 7 * m + 114) // 31
    jour = ((h + l - 7 * m + 114) % 31) + 1
    return date(annee, mois, jour)


def _jours_feries(annee):
    """Jours fériés français pour une année donnée."""
    p = _paques(annee)
    return {
        date(annee, 1, 1),
        p + timedelta(1),
        date(annee, 5, 1),
        date(annee, 5, 8),
        p + timedelta(39),
        p + timedelta(50),
        date(annee, 7, 14),
        date(annee, 8, 15),
        date(annee, 11, 1),
        date(annee, 11, 11),
        date(annee, 12, 25),
    }


def _is_jour_special(today=None):
    """Retourne True si le jour est un week-end ou un jour férié français."""
    today = today or date.today()
    return today.weekday() >= 5 or today in _jours_feries(today.year)
