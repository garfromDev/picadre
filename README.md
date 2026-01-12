# picadre
Utilities for Raspberry based picframe picture viewer

## Préparation. de la carte
installer un raspbian sur la carte
flasher l'image de sauvegarde sur la carte

## Ajout clef ssh si manquante (normalement fournie par l'image)
ssh-keygen -t ed25519 -C "garfromdev@gmail.com"
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
Puis ajout de la clef ssh dans github pour cloner le repo picadre
Penser à faire 
git config --global user.email "garfromdev@gmail.com"
git config --global user.name "garfromDev"

## backup sur le NAS
créer le fichier picadre/rsync.pwd contenant le mdp pour lasynchro NAS
il faut restreindre les droits du fichier rsync.pwd : chmod 600 rsync.pwd
Le mdp est dans le trousseau du mac sous 192.168.1.25

## requirements
sudo apt install imagemagick

## démarage automatique de picframe réalisé par 

## démarage automatique de upload_server
ajout du service : cp upload_server.service ~/.config/systemd/user/upload_server.service
activation du service :
systemctl --user daemon-reload
systemctl --user enable upload_server.service

pour ajouter des images depuis son téléphone, se connecter à http://cadrephoto:8000

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
controle à distance mqtt

installation du broker mqtt et des outils de test: 

````
sudo apt install mosquitto mosquitto-clients
sudo systemctl enable --now mosquitto
````

le client (picframe) se configure dans la section mqtt: de picframe_data/config/
````
mqtt:
  use_mqtt: True                          # default=False. Set True true, to enable mqtt
  server: "localhost"                     # No defaults for server
  port: 1883                              # default=8883 for tls, 1883 else (tls must be "" then !!!!!)
  login: "picadre"                        # your mqtt user
  password: ""                            # password for mqtt user
  tls: ""                                 # filename including path to your ca.crt. If not used, must be set to "" !!!!
  device_id: "picframe"                   # default="picframe" unique id of device. change if there is more than one PictureFrame
  device_url: ""   
  ````
upload_server sera aussi un client connecté au broker, la communication antre upload_server et picframe se fait à travers le broker mqtt

pour tester, il faut sudo apt install mosquitto-clients pour avoir les commandes mosquitto_pub et mosquitto_sub
````
export BROKER=localhost
export DEVICE=picframe
mosquitto_pub -h $BROKER -t "homeassistant/sensor/picframe_image/attributes" -m '{"filename":"IMG_001.jpg"}' -r
mosquitto_sub -h $BROKER -C 1 -t "homeassistant/sensor/${DEVICE}_image/attributes" -v
# doit retourner homeassistant/sensor/picframe_image/attributes {"filename":"IMG_001.jpg"}
````

## dépannage tailscale
`````
sudo systemctl stop tailscaled
sudo mv /var/lib/tailscale/tailscaled.state /var/lib/tailscale/tailscaled.state.backup 2>/dev/null
sudo systemctl start tailscaled
`````
