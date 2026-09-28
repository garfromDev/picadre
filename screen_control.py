#!/usr/bin/env python3
import logging
import os
import subprocess

logger = logging.getLogger(__name__)


def control_screen(action):
    """Contrôle l'écran (on/off)"""
    env = os.environ.copy()
    env['WAYLAND_DISPLAY'] = 'wayland-0'
    env['XDG_RUNTIME_DIR'] = f'/run/user/{os.getuid()}'
    try:
        if action == 'on':
            # ne marche pas à 60hz. Il faut faire wlr-randr pour voir les modes disponibles
            cmd = ['wlr-randr', '--output', 'HDMI-A-1', '--on', '--mode', '1920x1200@59.950001']
        else:
            cmd = ['wlr-randr', '--output', 'HDMI-A-1', '--off']

        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        if result.returncode == 0:
            logger.info("✓ Écran %s", action.upper())
            return True
        else:
            logger.error("✗ Erreur écran %s: %s", action, result.stderr)
            return False
    except Exception:
        logger.exception("✗ Exception écran %s", action)
        return False
