#!/bin/bash

echo "Install poetry"
curl -sSL https://install.python-poetry.org | python3 -
export PATH="~/.local/bin:$PATH"
source ~/.bashrc
poetry shell
poetry install

echo "INSTALL DOCKER"
sudo apt-get update
yes Y | sudo apt-get install \
    ca-certificates \
    curl \
    gnupg
yes Y | sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
yes Y | sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
echo "DONE INSTALL DOCKER"

echo "Start download GPT4All model"
dir="./models/"
if [[ ! -e $dir ]]; then
    mkdir $dir
elif [[ ! -d $dir ]]; then
    echo "$dir already exists but is not a directory" 1>&2
fi
wget https://gpt4all.io/models/ggml-gpt4all-j-v1.3-groovy.bin -P $dir
echo "Done download GPT4ALL in $dir"