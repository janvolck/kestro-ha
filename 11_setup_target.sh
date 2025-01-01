#!/bin/bash

# DEV system preparation
sudo apt install -y i2c-tools vim libfreetype6-dev libjpeg8-dev libopenjp2-7 libsdl1.2-dev \
                   python3-dev python3-pip python3-venv build-essential \
                   apt-transport-https ca-certificates curl gnupg lsb-release nfs-common \
                   libgpiod2 libgpiod-dev git network-manager

sudo systemctl mask systemd-networkd.socket --now
sudo systemctl mask systemd-networkd.service --now
sudo systemctl enable NetworkManager --now
sudo nmcli connection add type ethernet con-name dhcp ipv4.method auto


# Python environment
if [ ! -e kestro ]; then
  python3 -m venv kestro
fi

. kestro/bin/activate

pip3 install --upgrade pip setuptools
pip3 install Pillow netifaces
pip3 install flask flask-jsonpify flask-sqlalchemy flask-restful
pip3 install gpiod sysv_ipc


sudo addgroup gpio
sudo addgroup kestro
sudo usermod -a -G gpio $USER
sudo usermod -a -G i2c $USER
sudo usermod -a -G kestro $USER