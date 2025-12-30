# picadre
Utilities for Raspberry based picframe picture viewer

## requirements
sudo apt install imagemagick

## démarage automatique de picframe réalisé par 

## démarage automatique de upload_server
pour ajouter des images depuis son téléphone
réalisé par un service systemd (systemctl)
pour voir les logs : sudo journactl -u upload_server -f

## redimensionnement des images 
quotidien par crontab

## supression des doublons
quotidien par crontab

## mise à jour du code
quotidien par git pull sur main via crontab

========
## dev
### vérification serveur mqtt
le serveur se configure dans la section mqtt: de picframe_data/config/
sudo apt update && sudo apt install mosquitto mosquitto-clients pour installer le broker mqtt
pour tester, il faut sudo apt install mosquitto-clients pour avoir les commandes
export BROKER=localhost
export DEVICE=picframe
