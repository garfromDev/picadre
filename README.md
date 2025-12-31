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

## Fonctionnement sur une Pi Zero 2W
Du fait de la mémoire limitée à 512Mo, il faut éviter les crash par memory error
- limiterla taille des images (check_resize quotidien)
- utiliser un swap compressé en mémoire pour augmenter la ram disponible 
```
sudo apt update
sudo apt install zram-tools

# Configurer zram
echo "ALGO=lz4" | sudo tee -a /etc/default/zramswap
echo "PERCENT=50" | sudo tee -a /etc/default/zramswap

# Redémarrer le service
sudo systemctl restart zramswap
```

========
## dev
### vérification serveur mqtt
le serveur se configure dans la section mqtt: de picframe_data/config/
sudo apt update && sudo apt install mosquitto mosquitto-clients pour installer le broker mqtt
pour tester, il faut sudo apt install mosquitto-clients pour avoir les commandes
export BROKER=localhost
export DEVICE=picframe
