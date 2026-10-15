const MAX_UPLOAD_SIZE = window.uploadConfig?.maxUploadSize ?? 0;
const MAX_UPLOAD_SIZE_MB = window.uploadConfig?.maxUploadSizeMb ?? 0;
let selectedFiles = [];

function isHeicFile(file) {
    return /\.(heic|heif)$/i.test(file.name) || /hei[cf]/i.test(file.type);
}

async function convertHeicToJpeg(file) {
    const url = URL.createObjectURL(file);
    let canvas;

    try {
        const image = new Image();
        image.src = url;
        await image.decode();

        const scale = Math.min(1, 2560 / Math.max(image.naturalWidth, image.naturalHeight));
        canvas = document.createElement('canvas');
        canvas.width = Math.round(image.naturalWidth * scale);
        canvas.height = Math.round(image.naturalHeight * scale);

        const context = canvas.getContext('2d');
        if (!context) {
            throw new Error('Impossible de créer le contexte de dessin');
        }
        context.drawImage(image, 0, 0, canvas.width, canvas.height);

        const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.88));
        if (!blob) {
            throw new Error('La création du JPEG a échoué');
        }
        return blob;
    } finally {
        if (canvas) {
            canvas.width = 0;
            canvas.height = 0;
        }
        URL.revokeObjectURL(url);
    }
}

function formatExifDate(value) {
    if (value instanceof Date) {
        const pad = number => String(number).padStart(2, '0');
        return `${value.getFullYear()}:${pad(value.getMonth() + 1)}:${pad(value.getDate())} ` +
            `${pad(value.getHours())}:${pad(value.getMinutes())}:${pad(value.getSeconds())}`;
    }
    return typeof value === 'string' ? value : null;
}

async function readExifMetadata(file) {
    const metadata = {};
    try {
        const tags = await exifr.parse(file, {
            reviveValues: false
        });
        if (tags) {
            metadata.make = tags.Make;
            metadata.model = tags.Model;
            metadata.date = formatExifDate(tags.DateTimeOriginal);
        }

        const gps = await exifr.gps(file);
        if (gps && Number.isFinite(gps.latitude) && Number.isFinite(gps.longitude)) {
            metadata.latitude = gps.latitude;
            metadata.longitude = gps.longitude;
        }
        return { metadata, error: null };
    } catch (error) {
        console.warn(`Lecture des métadonnées EXIF impossible pour ${file.name}:`, error);
        return { metadata, error };
    }
}

function blobToDataUrl(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            if (typeof reader.result === 'string') {
                resolve(reader.result);
            } else {
                reject(new Error('Lecture du JPEG impossible'));
            }
        };
        reader.onerror = () => reject(reader.error || new Error('Lecture du JPEG impossible'));
        reader.readAsDataURL(blob);
    });
}

async function addExifMetadata(blob, metadata) {
    const zeroth = {};
    const exif = {};
    const gps = {};

    if (metadata.make) zeroth[piexif.ImageIFD.Make] = metadata.make;
    if (metadata.model) zeroth[piexif.ImageIFD.Model] = metadata.model;
    if (metadata.date) {
        zeroth[piexif.ImageIFD.DateTime] = metadata.date;
        exif[piexif.ExifIFD.DateTimeOriginal] = metadata.date;
        exif[piexif.ExifIFD.DateTimeDigitized] = metadata.date;
    }
    if (metadata.latitude != null && metadata.longitude != null) {
        gps[piexif.GPSIFD.GPSLatitudeRef] = metadata.latitude < 0 ? 'S' : 'N';
        gps[piexif.GPSIFD.GPSLatitude] = piexif.GPSHelper.degToDmsRational(Math.abs(metadata.latitude));
        gps[piexif.GPSIFD.GPSLongitudeRef] = metadata.longitude < 0 ? 'W' : 'E';
        gps[piexif.GPSIFD.GPSLongitude] = piexif.GPSHelper.degToDmsRational(Math.abs(metadata.longitude));
    }

    if (!Object.keys(zeroth).length && !Object.keys(gps).length) {
        return blob;
    }

    const exifBytes = piexif.dump({ '0th': zeroth, Exif: exif, GPS: gps });
    const jpegWithExif = piexif.insert(exifBytes, await blobToDataUrl(blob));
    return await (await fetch(jpegWithExif)).blob();
}

async function prepareUploadFile(file) {
    if (!isHeicFile(file)) {
        return { file, conversionError: null, metadataError: null };
    }

    const { metadata, error: metadataError } = await readExifMetadata(file);
    try {
        const blob = await convertHeicToJpeg(file);
        let jpeg = blob;
        let exifError = metadataError;
        try {
            jpeg = await addExifMetadata(blob, metadata);
        } catch (error) {
            console.warn(`Réinjection des métadonnées EXIF impossible pour ${file.name}:`, error);
            exifError = error;
        }

        const baseName = file.name.replace(/\.[^.]+$/, '') || 'photo';
        return {
            file: new File([jpeg], `${baseName}.jpg`, {
                type: 'image/jpeg',
                lastModified: file.lastModified
            }),
            conversionError: null,
            metadataError: exifError
        };
    } catch (error) {
        console.warn(`Conversion HEIC impossible pour ${file.name}; envoi du fichier original:`, error);
        return { file, conversionError: error, metadataError: null };
    }
}

function clearMessage(elementId) {
    const message = document.getElementById(elementId);
    if (!message) return;
    message.textContent = '';
    message.className = 'message';
    message.style.display = 'none';
}

function validateFiles(files) {
    if (files.length === 0) {
        clearMessage('uploadMessage');
        return true;
    }

    const totalSize = files.reduce((sum, file) => sum + file.size, 0);
    const oversizedFile = files.find(file => file.size > MAX_UPLOAD_SIZE);

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

function validateSelectedFiles() {
    return validateFiles(selectedFiles.filter(file => !isHeicFile(file)));
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

    const uploadBtn = document.getElementById('uploadBtn');
    uploadBtn.disabled = true;
    uploadBtn.textContent = '⏳ Préparation des photos...';
    clearMessage('uploadMessage');

    let stage = 'préparation';
    try {
        const preparedResults = [];
        for (const file of selectedFiles) {
            preparedResults.push(await prepareUploadFile(file));
        }

        const preparedFiles = preparedResults.map(result => result.file);
        if (!validateFiles(preparedFiles)) {
            return;
        }

        const formData = new FormData();
        preparedFiles.forEach(file => formData.append('files', file));

        stage = 'envoi';
        uploadBtn.textContent = '⏳ Envoi en cours...';
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
            const conversionFallbacks = preparedResults
                .filter(item => item.conversionError)
                .map(item => item.file.name);
            const metadataFailures = preparedResults
                .filter(item => item.metadataError)
                .map(item => item.file.name);
            let message = `✅ ${result.uploaded} photo(s) envoyée(s) !`;
            if (conversionFallbacks.length) {
                message += ` Conversion HEIC impossible pour ${conversionFallbacks.join(', ')}; fichier(s) original(aux) envoyé(s).`;
            }
            if (metadataFailures.length) {
                message += ` Métadonnées EXIF non conservées pour ${metadataFailures.join(', ')}.`;
            }
            showMessage('uploadMessage', message, conversionFallbacks.length || metadataFailures.length ? 'warning' : 'success');
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
        console.error(`Erreur pendant la ${stage} des photos:`, error);
        showMessage(
            'uploadMessage',
            stage === 'préparation' ? '❌ Erreur pendant la préparation des photos' : '❌ Erreur de connexion',
            'error'
        );
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
        const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/') || isHeicFile(f));
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
