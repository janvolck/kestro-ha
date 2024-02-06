#!/bin/bash

# DEV system preparation
sudo apt install -y i2c-tools vim libfreetype6-dev libjpeg8-dev libopenjp2-7 libsdl1.2-dev \
                   python3-dev python3-pip python3-venv \
                   apt-transport-https ca-certificates curl gnupg lsb-release nfs-common \
                   libgpiod2 libgpiod-dev git 

# Enable i2c and 1wire support on target
echo "enable i2c and 1-wire on target"
sleep 2
read

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
sudo usermod -a -G gpio $USER