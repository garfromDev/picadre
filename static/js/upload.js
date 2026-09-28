const MAX_UPLOAD_SIZE = window.uploadConfig?.maxUploadSize ?? 0;
const MAX_UPLOAD_SIZE_MB = window.uploadConfig?.maxUploadSizeMb ?? 0;
let selectedFiles = [];

function clearMessage(elementId) {
    const message = document.getElementById(elementId);
    if (!message) return;
    message.textContent = '';
    message.className = 'message';
    message.style.display = 'none';
}

function validateSelectedFiles() {
    if (selectedFiles.length === 0) {
        clearMessage('uploadMessage');
        return true;
    }

    const totalSize = selectedFiles.reduce((sum, file) => sum + file.size, 0);
    const oversizedFile = selectedFiles.find(file => file.size > MAX_UPLOAD_SIZE);

    if (oversizedFile) {
        showMessage('uploadMessage', `❌ Le fichier ${oversizedFile.name} dépasse la limite de ${MAX_UPLOAD_SIZE_MB} MB.`, 'error');
        return false;
    }

    if (totalSize > MAX_UPLOAD_SIZE) {
        showMessage('uploadMessage', `❌ Taille totale des images trop grande (max ${MAX_UPLOAD_SIZE_MB} MB).`, 'error');
        return false;
    }

    clearMessage('uploadMessage');
    return true;
}

function switchTab(tab) {
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));

    if (tab === 'upload') {
        document.querySelector('.nav-tab:nth-child(1)').classList.add('active');
        document.getElementById('uploadTab').classList.add('active');
    } else {
        document.querySelector('.nav-tab:nth-child(2)').classList.add('active');
        document.getElementById('scheduleTab').classList.add('active');
        loadSchedule();
    }
}

function displayFileList() {
    const fileList = document.getElementById('fileList');

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

async function handleUploadSubmit(event) {
    event.preventDefault();

    if (selectedFiles.length === 0) {
        showMessage('uploadMessage', 'Veuillez sélectionner au moins une photo', 'error');
        return;
    }

    if (!validateSelectedFiles()) {
        return;
    }

    const formData = new FormData();
    selectedFiles.forEach(file => formData.append('files', file));

    const uploadBtn = document.getElementById('uploadBtn');
    uploadBtn.disabled = true;
    uploadBtn.textContent = '⏳ Envoi en cours...';
    clearMessage('uploadMessage');

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        let result = null;
        try {
            result = await response.json();
        } catch (err) {
            result = { error: 'Réponse invalide du serveur' };
        }

        if (response.ok) {
            showMessage('uploadMessage', `✅ ${result.uploaded} photo(s) envoyée(s) !`, 'success');
            selectedFiles = [];
            document.getElementById('fileInput').value = '';
            document.getElementById('fileList').innerHTML = '';
            document.getElementById('photoCount').textContent = result.total_photos;
        } else if (response.status === 413) {
            showMessage('uploadMessage', `❌ Taille des images trop grande. Limite ${MAX_UPLOAD_SIZE_MB} MB.`, 'error');
        } else {
            showMessage('uploadMessage', `❌ Erreur: ${result.error || 'Erreur serveur'}`, 'error');
        }
    } catch (error) {
        showMessage('uploadMessage', '❌ Erreur de connexion', 'error');
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = '📤 Envoyer les photos';
    }
}

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

function setupUploadArea() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const uploadForm = document.getElementById('uploadForm');

    uploadArea.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
        selectedFiles = Array.from(e.target.files);
        displayFileList();
        validateSelectedFiles();
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
        validateSelectedFiles();
    });

    uploadForm.addEventListener('submit', handleUploadSubmit);

    document.getElementById('showImageAttrsBtn').addEventListener('click', async () => {
        const btn = document.getElementById('showImageAttrsBtn');
        const pre = document.getElementById('imageAttrs');
        btn.disabled = true;
        btn.textContent = '⏳ Chargement...';
        pre.style.display = 'none';
        pre.textContent = '';
        try {
            const res = await fetch('/mqtt_image');
            if (!res.ok) {
                const err = await res.json();
                showMessage('uploadMessage', '❌ ' + (err.error || 'Erreur MQTT'), 'error');
            } else {
                const data = await res.json();
                pre.textContent = JSON.stringify(data.attributes, null, 2);
                pre.style.display = 'block';
                showMessage('uploadMessage', '✅ Attributs reçus', 'success');
            }
        } catch (e) {
            showMessage('uploadMessage', '❌ Erreur de connexion MQTT', 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = '🛈 Voir l\'image affichée';
        }
    });
}

function renderErrorStatus(data) {
    const button = document.getElementById('errorButton');
    const details = document.getElementById('errorDetails');

    if (!data.has_error) {
        button.textContent = '✅';
        button.title = 'Aucune erreur récente détectée';
        button.dataset.errorText = 'Aucune erreur récente enregistrée.';
        details.style.display = 'none';
        return;
    }

    button.textContent = '⚠️';
    button.title = 'Cliquez pour afficher la dernière erreur';
    button.dataset.errorText = data.last_error || 'Erreur non disponible.';
}

function toggleErrorDetails() {
    const button = document.getElementById('errorButton');
    const details = document.getElementById('errorDetails');

    if (details.style.display === 'block') {
        details.style.display = 'none';
        return;
    }

    details.textContent = button.dataset.errorText || 'Aucune erreur enregistrée.';
    details.style.display = 'block';
}

async function fetchErrorStatus() {
    try {
        const response = await fetch('/error_status');
        if (!response.ok) {
            return;
        }
        const data = await response.json();
        renderErrorStatus(data);
    } catch (error) {
        console.error('Erreur chargement status erreur:', error);
    }
}

window.addEventListener('DOMContentLoaded', () => {
    setupUploadArea();
    loadSchedule();
    fetchErrorStatus();
    document.getElementById('errorButton').addEventListener('click', toggleErrorDetails);
    setInterval(fetchErrorStatus, 60000);
});
