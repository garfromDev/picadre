#!/usr/bin/env python3
"""
Serveur d'upload simple pour cadre photo Raspberry Pi
Usage: python3 photo_upload.py
Accès depuis Android: http://IP_DU_PI:8000

Généré par Claude Sonnet 4.5
"""

from flask import Flask, render_template_string, request, jsonify
import os
import json
import subprocess
from datetime import datetime
from werkzeug.utils import secure_filename
from threading import Thread
import time

# Configuration
UPLOAD_FOLDER = '/home/picadre/picadre/Picture' 
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'heic'}
SCHEDULE_FILE = '/home/picadre/picadre/screen_schedule.json'  # Fichier de configuration horaires
PORT = 8000

# Créer le dossier s'il n'existe pas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 12 * 1024 * 1024  # Limite à 12MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_schedule():
    """Charge les horaires depuis le fichier JSON"""
    try:
        with open(SCHEDULE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Valeurs par défaut
        return {
            'enabled': False,
            'on_time': '08:00',
            'off_time': '22:00'
        }

def save_schedule(schedule):
    """Sauvegarde les horaires dans le fichier JSON"""
    with open(SCHEDULE_FILE, 'w') as f:
        json.dump(schedule, f, indent=2)

def control_screen(action):
    """Contrôle l'écran (on/off)"""
    try:
        if action == 'on':
            cmd = ['wlr-randr', '--output', 'HDMI-A-1', '--on', '--mode', '1920x1080@60']
        else:  # off
            cmd = ['wlr-randr', '--output', 'HDMI-A-1', '--off']
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Écran {action.upper()}")
            return True
        else:
            print(f"✗ Erreur écran {action}: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Exception écran {action}: {e}")
        return False

def schedule_monitor():
    """Thread qui surveille les horaires et contrôle l'écran"""
    print("🕐 Moniteur d'horaires démarré")
    last_check = None
    
    while True:
        try:
            schedule = load_schedule()
            
            if schedule['enabled']:
                now = datetime.now()
                current_time = now.strftime('%H:%M')
                
                # Vérifier seulement une fois par minute
                if current_time != last_check:
                    last_check = current_time
                    
                    if current_time == schedule['on_time']:
                        print(f"⏰ Heure d'allumage atteinte: {current_time}")
                        control_screen('on')
                    elif current_time == schedule['off_time']:
                        print(f"⏰ Heure d'extinction atteinte: {current_time}")
                        control_screen('off')
            
            time.sleep(30)  # Vérifier toutes les 30 secondes
        except Exception as e:
            print(f"✗ Erreur moniteur: {e}")
            time.sleep(60)

# Template HTML avec interface simple et moderne
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📸 Upload Photos</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .nav-tabs {
            display: flex;
            gap: 10px;
            max-width: 500px;
            margin: 0 auto 20px;
            background: rgba(255,255,255,0.2);
            padding: 10px;
            border-radius: 15px;
        }
        .nav-tab {
            flex: 1;
            padding: 12px;
            background: rgba(255,255,255,0.3);
            border: none;
            border-radius: 10px;
            color: white;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        .nav-tab.active {
            background: white;
            color: #667eea;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 500px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            margin: 0 auto;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
            text-align: center;
        }
        .subtitle {
            color: #666;
            text-align: center;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 15px;
            padding: 40px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            background: #f8f9ff;
        }
        .upload-area:hover {
            border-color: #764ba2;
            background: #f0f2ff;
        }
        .upload-area.dragover {
            border-color: #764ba2;
            background: #e8ebff;
            transform: scale(1.02);
        }
        .upload-icon {
            font-size: 60px;
            margin-bottom: 15px;
        }
        input[type="file"] {
            display: none;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            border-radius: 25px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            width: 100%;
            margin-top: 20px;
            transition: transform 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .btn-small {
            padding: 10px 20px;
            font-size: 14px;
            width: auto;
            display: inline-block;
        }
        .message {
            margin-top: 20px;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            font-weight: bold;
            display: none;
        }
        .success {
            background: #d4edda;
            color: #155724;
            display: block;
        }
        .error {
            background: #f8d7da;
            color: #721c24;
            display: block;
        }
        .file-list {
            margin-top: 20px;
            max-height: 200px;
            overflow-y: auto;
        }
        .file-item {
            background: #f8f9ff;
            padding: 10px;
            margin: 5px 0;
            border-radius: 8px;
            font-size: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .file-name {
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .file-size {
            color: #666;
            font-size: 12px;
            margin-left: 10px;
        }
        .stats {
            text-align: center;
            margin-top: 20px;
            color: #666;
            font-size: 14px;
        }
        
        /* Styles pour l'onglet horaires */
        .schedule-section {
            margin-bottom: 30px;
        }
        .toggle-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #f8f9ff;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
        }
        .toggle-label {
            font-weight: bold;
            color: #333;
        }
        .toggle-switch {
            position: relative;
            width: 60px;
            height: 30px;
        }
        .toggle-switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: .4s;
            border-radius: 30px;
        }
        .slider:before {
            position: absolute;
            content: "";
            height: 22px;
            width: 22px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }
        input:checked + .slider {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        input:checked + .slider:before {
            transform: translateX(30px);
        }
        .time-setting {
            background: #f8f9ff;
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 15px;
        }
        .time-label {
            display: block;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }
        .time-input {
            width: 100%;
            padding: 12px;
            border: 2px solid #667eea;
            border-radius: 10px;
            font-size: 16px;
            font-family: monospace;
        }
        .screen-status {
            text-align: center;
            padding: 15px;
            background: #f8f9ff;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .screen-status-indicator {
            font-size: 24px;
            margin-bottom: 5px;
        }
        .btn-group {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        .btn-group button {
            flex: 1;
        }
    </style>
</head>
<body>
    <div class="nav-tabs">
        <button class="nav-tab active" onclick="switchTab('upload')">📤 Upload</button>
        <button class="nav-tab" onclick="switchTab('schedule')">⏰ Horaires</button>
    </div>

    <div class="container">
        <!-- Onglet Upload -->
        <div id="uploadTab" class="tab-content active">
            <h1>📸 Cadre Photo</h1>
            <p class="subtitle">Ajoutez vos photos au cadre</p>
            
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="upload-area" id="uploadArea">
                    <div class="upload-icon">📁</div>
                    <p><strong>Cliquez ici</strong> ou glissez vos photos</p>
                    <p style="font-size: 12px; color: #999; margin-top: 10px;">
                        JPG, PNG, GIF, WEBP • Max 50MB
                    </p>
                </div>
                <input type="file" id="fileInput" name="files" multiple accept="image/*">
                <button type="submit" class="btn" id="uploadBtn">📤 Envoyer les photos</button>
            </form>
            
            <div id="fileList" class="file-list"></div>
            <div id="uploadMessage" class="message"></div>
            <div class="stats">
                <p>📊 <span id="photoCount">{{ photo_count }}</span> photos dans le cadre</p>
            </div>
        </div>

        <!-- Onglet Horaires -->
        <div id="scheduleTab" class="tab-content">
            <h1>⏰ Horaires Écran</h1>
            <p class="subtitle">Allumage et extinction automatiques</p>
            
            <div class="screen-status">
                <div class="screen-status-indicator" id="screenStatus">🔲</div>
                <div id="screenStatusText">État inconnu</div>
            </div>
            
            <div class="toggle-container">
                <span class="toggle-label">Programmation automatique</span>
                <label class="toggle-switch">
                    <input type="checkbox" id="scheduleEnabled">
                    <span class="slider"></span>
                </label>
            </div>
            
            <div class="schedule-section">
                <div class="time-setting">
                    <label class="time-label">🌅 Heure d'allumage</label>
                    <input type="time" id="onTime" class="time-input" value="{{ schedule.on_time }}">
                </div>
                
                <div class="time-setting">
                    <label class="time-label">🌙 Heure d'extinction</label>
                    <input type="time" id="offTime" class="time-input" value="{{ schedule.off_time }}">
                </div>
                
                <button class="btn" onclick="saveSchedule()">💾 Sauvegarder les horaires</button>
            </div>
            
            <div class="schedule-section">
                <p style="text-align: center; color: #666; margin-bottom: 15px; font-weight: bold;">
                    Contrôle manuel
                </p>
                <div class="btn-group">
                    <button class="btn btn-small" onclick="controlScreen('on')">🟢 Allumer</button>
                    <button class="btn btn-small" onclick="controlScreen('off')">🔴 Éteindre</button>
                </div>
            </div>
            
            <div id="scheduleMessage" class="message"></div>
        </div>
    </div>

    <script>
        // Variables globales
        let selectedFiles = [];
        
        // Charger les horaires au démarrage
        loadSchedule();

        // ===== GESTION DES ONGLETS =====
        function switchTab(tab) {
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            
            if (tab === 'upload') {
                document.querySelector('.nav-tab:nth-child(1)').classList.add('active');
                document.getElementById('uploadTab').classList.add('active');
            } else {
                document.querySelector('.nav-tab:nth-child(2)').classList.add('active');
                document.getElementById('scheduleTab').classList.add('active');
                loadSchedule(); // Recharger les horaires
            }
        }

        // ===== UPLOAD DE PHOTOS =====
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const uploadForm = document.getElementById('uploadForm');
        const uploadBtn = document.getElementById('uploadBtn');
        const uploadMessage = document.getElementById('uploadMessage');
        const fileList = document.getElementById('fileList');

        uploadArea.addEventListener('click', () => fileInput.click());

        fileInput.addEventListener('change', (e) => {
            selectedFiles = Array.from(e.target.files);
            displayFileList();
        });

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'));
            selectedFiles = files;
            displayFileList();
        });

        function displayFileList() {
            if (selectedFiles.length === 0) {
                fileList.innerHTML = '';
                return;
            }
            
            fileList.innerHTML = selectedFiles.map(file => `
                <div class="file-item">
                    <span class="file-name">📷 ${file.name}</span>
                    <span class="file-size">${formatFileSize(file.size)}</span>
                </div>
            `).join('');
        }

        function formatFileSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        }

        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (selectedFiles.length === 0) {
                showMessage('uploadMessage', 'Veuillez sélectionner au moins une photo', 'error');
                return;
            }

            const formData = new FormData();
            selectedFiles.forEach(file => formData.append('files', file));

            uploadBtn.disabled = true;
            uploadBtn.textContent = '⏳ Envoi en cours...';
            uploadMessage.className = 'message';
            uploadMessage.style.display = 'none';

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (response.ok) {
                    showMessage('uploadMessage', `✅ ${result.uploaded} photo(s) envoyée(s) !`, 'success');
                    selectedFiles = [];
                    fileInput.value = '';
                    fileList.innerHTML = '';
                    document.getElementById('photoCount').textContent = result.total_photos;
                } else {
                    showMessage('uploadMessage', `❌ Erreur: ${result.error}`, 'error');
                }
            } catch (error) {
                showMessage('uploadMessage', '❌ Erreur de connexion', 'error');
            } finally {
                uploadBtn.disabled = false;
                uploadBtn.textContent = '📤 Envoyer les photos';
            }
        });

        // ===== GESTION DES HORAIRES =====
        async function loadSchedule() {
            try {
                const response = await fetch('/schedule');
                const schedule = await response.json();
                
                document.getElementById('scheduleEnabled').checked = schedule.enabled;
                document.getElementById('onTime').value = schedule.on_time;
                document.getElementById('offTime').value = schedule.off_time;
            } catch (error) {
                console.error('Erreur chargement horaires:', error);
            }
        }

        async function saveSchedule() {
            const schedule = {
                enabled: document.getElementById('scheduleEnabled').checked,
                on_time: document.getElementById('onTime').value,
                off_time: document.getElementById('offTime').value
            };

            try {
                const response = await fetch('/schedule', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(schedule)
                });

                const result = await response.json();

                if (response.ok) {
                    showMessage('scheduleMessage', '✅ Horaires sauvegardés !', 'success');
                } else {
                    showMessage('scheduleMessage', '❌ Erreur sauvegarde', 'error');
                }
            } catch (error) {
                showMessage('scheduleMessage', '❌ Erreur de connexion', 'error');
            }
        }

        async function controlScreen(action) {
            try {
                const response = await fetch('/screen', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action })
                });

                const result = await response.json();

                if (response.ok) {
                    const emoji = action === 'on' ? '🟢' : '🔴';
                    const text = action === 'on' ? 'allumé' : 'éteint';
                    showMessage('scheduleMessage', `${emoji} Écran ${text}`, 'success');
                    updateScreenStatus(action);
                } else {
                    showMessage('scheduleMessage', `❌ ${result.error}`, 'error');
                }
            } catch (error) {
                showMessage('scheduleMessage', '❌ Erreur de connexion', 'error');
            }
        }

        function updateScreenStatus(status) {
            const statusDiv = document.getElementById('screenStatus');
            const textDiv = document.getElementById('screenStatusText');
            
            if (status === 'on') {
                statusDiv.textContent = '🟢';
                textDiv.textContent = 'Écran allumé';
            } else {
                statusDiv.textContent = '🔴';
                textDiv.textContent = 'Écran éteint';
            }
        }

        function showMessage(elementId, text, type) {
            const message = document.getElementById(elementId);
            message.textContent = text;
            message.className = `message ${type}`;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    photo_count = len([f for f in os.listdir(UPLOAD_FOLDER) 
                       if allowed_file(f)])
    schedule = load_schedule()
    return render_template_string(HTML_TEMPLATE, 
                                 photo_count=photo_count,
                                 schedule=schedule)

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({'error': 'Aucun fichier trouvé'}), 400
    
    files = request.files.getlist('files')
    uploaded_count = 0
    
    for file in files:
        if file and file.filename and allowed_file(file.filename):
            # Nom de fichier sécurisé avec timestamp pour éviter les doublons
            filename = secure_filename(file.filename)
            name, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{name}_{timestamp}{ext}"
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)
            uploaded_count += 1
            print(f"✓ Photo sauvegardée: {unique_filename}")
    
    # Compter le total de photos
    total_photos = len([f for f in os.listdir(UPLOAD_FOLDER) 
                        if allowed_file(f)])
    
    return jsonify({
        'success': True,
        'uploaded': uploaded_count,
        'total_photos': total_photos
    })

@app.route('/schedule', methods=['GET', 'POST'])
def schedule():
    if request.method == 'GET':
        return jsonify(load_schedule())
    else:  # POST
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

if __name__ == '__main__':
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    # Démarrer le moniteur d'horaires dans un thread séparé
    monitor_thread = Thread(target=schedule_monitor, daemon=True)
    monitor_thread.start()
    
    print("\n" + "="*50)
    print("🚀 Serveur d'upload de photos démarré !")
    print("="*50)
    print(f"📁 Dossier de sauvegarde: {UPLOAD_FOLDER}")
    print(f"🌐 Accès depuis votre Android:")
    print(f"   → http://{local_ip}:{PORT}")
    print(f"   → http://localhost:{PORT} (sur le Pi)")
    print(f"⏰ Moniteur d'horaires: Actif")
    print("="*50)
    print("Appuyez sur Ctrl+C pour arrêter\n")
    
    app.run(host='0.0.0.0', port=PORT, debug=False)