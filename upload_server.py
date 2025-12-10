#!/usr/bin/env python3
"""
Serveur d'upload simple pour cadre photo Raspberry Pi
Usage: python3 photo_upload.py
Accès depuis Android: http://IP_DU_PI:8000
Généré par Claude Sonnet 4.5
"""

from flask import Flask, render_template_string, request, jsonify
import os
from datetime import datetime
from werkzeug.utils import secure_filename

# Configuration
UPLOAD_FOLDER = '/home/picadre/Pictures'  # Modifiez ce chemin selon votre répertoire
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'heic'}
PORT = 8000

# Créer le dossier s'il n'existe pas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 12 * 1024 * 1024  # Limite à 12MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            max-width: 500px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
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
    </style>
</head>
<body>
    <div class="container">
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
        <div id="message" class="message"></div>
        <div class="stats">
            <p>📊 <span id="photoCount">{{ photo_count }}</span> photos dans le cadre</p>
        </div>
    </div>

    <script>
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const uploadForm = document.getElementById('uploadForm');
        const uploadBtn = document.getElementById('uploadBtn');
        const message = document.getElementById('message');
        const fileList = document.getElementById('fileList');

        let selectedFiles = [];

        // Clic sur la zone d'upload
        uploadArea.addEventListener('click', () => fileInput.click());

        // Sélection de fichiers
        fileInput.addEventListener('change', (e) => {
            selectedFiles = Array.from(e.target.files);
            displayFileList();
        });

        // Drag & Drop
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

        // Upload
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (selectedFiles.length === 0) {
                showMessage('Veuillez sélectionner au moins une photo', 'error');
                return;
            }

            const formData = new FormData();
            selectedFiles.forEach(file => formData.append('files', file));

            uploadBtn.disabled = true;
            uploadBtn.textContent = '⏳ Envoi en cours...';
            message.className = 'message';
            message.style.display = 'none';

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (response.ok) {
                    showMessage(`✅ ${result.uploaded} photo(s) envoyée(s) !`, 'success');
                    selectedFiles = [];
                    fileInput.value = '';
                    fileList.innerHTML = '';
                    
                    // Mettre à jour le compteur
                    document.getElementById('photoCount').textContent = result.total_photos;
                } else {
                    showMessage(`❌ Erreur: ${result.error}`, 'error');
                }
            } catch (error) {
                showMessage('❌ Erreur de connexion', 'error');
            } finally {
                uploadBtn.disabled = false;
                uploadBtn.textContent = '📤 Envoyer les photos';
            }
        });

        function showMessage(text, type) {
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
    return render_template_string(HTML_TEMPLATE, photo_count=photo_count)

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

if __name__ == '__main__':
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print("\n" + "="*50)
    print("🚀 Serveur d'upload de photos démarré !")
    print("="*50)
    print(f"📁 Dossier de sauvegarde: {UPLOAD_FOLDER}")
    print(f"🌐 Accès depuis votre Android:")
    print(f"   → http://{local_ip}:{PORT}")
    print(f"   → http://localhost:{PORT} (sur le Pi)")
    print("="*50)
    print("Appuyez sur Ctrl+C pour arrêter\n")
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
