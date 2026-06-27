#!/usr/bin/env python3
"""
Serveur d'upload simple pour cadre photo Raspberry Pi
Usage: python3 upload_server.py
Accès depuis Android: http://IP_DU_PI:8000

Généré par Claude Sonnet 4.5
"""

from flask import Flask, render_template, request, jsonify
import os
import json
from datetime import datetime
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename
from threading import Thread, Event
import time
import logging

from schedule_manager import load_schedule, save_schedule, _is_jour_special
from screen_control import control_screen

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
)
logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = '/home/picadre/Pictures'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'heic'}
PORT = 8000

# MQTT defaults (can be overridden via env vars)
MQTT_BROKER = os.environ.get('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.environ.get('MQTT_PORT', '1883'))
MQTT_DEVICE_ID = os.environ.get('MQTT_DEVICE_ID', 'picframe')

# Créer le dossier s'il n'existe pas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

MAX_UPLOAD_SIZE_MB = 12
MAX_UPLOAD_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_SIZE


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def schedule_monitor():
    """Thread qui surveille les horaires et contrôle l'écran."""
    logger.info("🕐 Moniteur d'horaires démarré")
    last_check = None

    while True:
        try:
            now = datetime.now()
            current_time = now.strftime('%H:%M')

            if current_time != last_check:
                last_check = current_time

                schedule = load_schedule()
                if schedule['enabled']:
                    if current_time == schedule['on_time']:
                        logger.info("⏰ Allumage programmé: %s", current_time)
                        control_screen('on')
                    elif current_time == schedule['off_time']:
                        logger.info("⏰ Extinction programmée: %s", current_time)
                        control_screen('off')

                if _is_jour_special():
                    if current_time == '09:00':
                        logger.info("⏰ Allumage week-end/férié")
                        control_screen('on')
                    elif current_time == '23:00':
                        logger.info("⏰ Extinction week-end/férié")
                        control_screen('off')

            time.sleep(30)
        except Exception:
            logger.exception("✗ Erreur moniteur")
            time.sleep(60)


@app.route('/')
def index():
    photo_count = len([f for f in os.listdir(UPLOAD_FOLDER) if allowed_file(f)])
    schedule = load_schedule()
    return render_template('upload.html',
                           photo_count=photo_count,
                           schedule=schedule,
                           max_upload_size_mb=MAX_UPLOAD_SIZE_MB,
                           max_upload_size=MAX_UPLOAD_SIZE)


@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({'error': 'Aucun fichier trouvé'}), 400

    files = request.files.getlist('files')
    uploaded_count = 0

    for file in files:
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            name, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{name}_{timestamp}{ext}"

            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            uploaded_count += 1
            logger.info("✓ Photo sauvegardée: %s", unique_filename)

    total_photos = len([f for f in os.listdir(UPLOAD_FOLDER) if allowed_file(f)])

    return jsonify({
        'success': True,
        'uploaded': uploaded_count,
        'total_photos': total_photos
    })


@app.errorhandler(RequestEntityTooLarge)
def handle_request_entity_too_large(error):
    return jsonify({
        'error': f'Taille des images trop grande. Maximum {MAX_UPLOAD_SIZE_MB} MB.',
    }), 413


@app.route('/schedule', methods=['GET', 'POST'])
def schedule():
    if request.method == 'GET':
        return jsonify(load_schedule())
    else:
        try:
            schedule_data = request.json
            save_schedule(schedule_data)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 400


@app.route('/screen', methods=['POST'])
def screen():
    try:
        action = request.json.get('action')
        if action not in ['on', 'off']:
            return jsonify({'error': 'Action invalide'}), 400

        success = control_screen(action)
        if success:
            return jsonify({'success': True, 'action': action})
        else:
            return jsonify({'error': 'Échec du contrôle écran'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/mqtt_image', methods=['GET'])
def mqtt_image():
    """Récupère les attributs de l'image actuellement affichée via MQTT.
    Lit le topic Home Assistant créé par pictureFrame:
    homeassistant/sensor/{device_id}_image/attributes
    Les variables d'environnement suivantes contrôlent la connexion :
    MQTT_BROKER, MQTT_PORT, MQTT_DEVICE_ID
    """
    try:
        import paho.mqtt.client as mqtt
    except Exception:
        return jsonify({'error': 'paho-mqtt non installé'}), 500

    broker = os.environ.get('MQTT_BROKER', MQTT_BROKER)
    port = int(os.environ.get('MQTT_PORT', MQTT_PORT))
    device = os.environ.get('MQTT_DEVICE_ID', MQTT_DEVICE_ID)
    topic = f"homeassistant/sensor/{device}_image/attributes"

    event = Event()
    payload_holder = {'payload': None}

    def on_message(client, userdata, message):
        try:
            payload = message.payload.decode('utf-8')
            payload_holder['payload'] = json.loads(payload)
        except Exception:
            payload_holder['payload'] = message.payload.decode('utf-8')
        event.set()

    try:
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    except Exception:
        client = mqtt.Client()
    client.on_message = on_message
    try:
        client.connect(broker, port, 60)
    except Exception as e:
        return jsonify({'error': f'Erreur connexion MQTT: {e}'}), 500

    client.subscribe(topic, qos=0)
    client.loop_start()
    event.wait(2)
    client.loop_stop()
    try:
        client.disconnect()
    except Exception:
        pass

    if payload_holder['payload'] is None:
        return jsonify({'error': 'Pas de message MQTT reçu (vérifier broker/topic/device id)'}), 404

    return jsonify({'attributes': payload_holder['payload']})


if __name__ == '__main__':
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    monitor_thread = Thread(target=schedule_monitor, daemon=True)
    monitor_thread.start()

    logger.info("\n" + "="*50)
    logger.info("🚀 Serveur d'upload de photos démarré !")
    logger.info("="*50)
    logger.info("📁 Dossier de sauvegarde: %s", UPLOAD_FOLDER)
    logger.info("🌐 Accès depuis votre Android:")
    logger.info("   → http://%s:%d", local_ip, PORT)
    logger.info("   → http://localhost:%d (sur le Pi)", PORT)
    logger.info("⏰ Moniteur d'horaires: Actif")
    logger.info("="*50)
    logger.info("Appuyez sur Ctrl+C pour arrêter\n")

    app.run(host='0.0.0.0', port=PORT, debug=False)
