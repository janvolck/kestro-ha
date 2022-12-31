# SNIPPETS

## Git

### Installation

sudo apt install -y git

### Configuration

git config --global init.defaultBranch development
git config --global user.email <email>
git config --global user.name <username>



## Angular

### Installation

sudo apt install -y curl

curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash
. $HOME/.profile

nvm install 16.10
npm install -g @angular/cli


### Prepare new environment

ng new <application-name>
e.g.:
`ng new angular`


