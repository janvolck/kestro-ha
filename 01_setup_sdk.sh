#!/bin/bash

# DEV system preparation
sudo apt install -y python3-dev python3-pip python3-venv curl git

# Git environment
git config --global init.defaultBranch development
git config --global user.email "janvolck@gmail.com"
git config --global user.name "Jan Volckaert"

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
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash
. $HOME/.profile

nvm install 16.10
npm install -g @angular/cli
