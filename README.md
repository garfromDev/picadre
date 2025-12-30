# picadre
Utilities for Raspberry based picframe picture viewer

## requirements
sudo apt install imagemagick

## démarage automatique de picframe réalisé par 

## démarage automatique de upload_server
ajout du service : cp upload_server.service ~/.config/systemd/user/upload_server.service
activation du service :
systemctl --user daemon-reload
systemctl --user enable upload_server.service

pour ajouter des images depuis son téléphone
réalisé par un service systemd (systemctl)
pour voir les logs : journalctl --user -u upload_server -f

## redimensionnement des images 
quotidien par crontab

## supression des doublons
quotidien par crontab

## mise à jour du code
quotidien par git pull sur main via crontab

