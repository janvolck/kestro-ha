#!/bin/bash

# DEV system preparation
sudo apt install -y i2c-tools vim libfreetype6-dev libjpeg8-dev libopenjp2-7 libsdl1.2-dev \
                   python-dev python3-dev python3-pip python3-venv python3-pil \
                   apt-transport-https ca-certificates curl gnupg lsb-release

curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
. $HOME/.profile

# Enable i2c support via sudo raspi-config 
echo "enable i2c and 1-wire support in raspi-config"
sleep 2
sudo raspi-config

# Python environment
if [ ! -e venv ]; then
  python3 -m venv venv
fi

. venv/bin/activate

pip3 install --upgrade pip setuptools
pip3 install pigpio
pip3 install Pillow netifaces
pip3 install flask flask-jsonpify flask-sqlalchemy flask-restful

# Node.js environment
nvm install v14.18.1
npm install -g @angular/cli

