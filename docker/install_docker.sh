# Condor Installation
# https://docs.docker.com/engine/installation/linux/ubuntu/
sudo apt-get update
sudo apt-get -y remove docker docker-engine
sudo apt-get -y install \
    linux-modules-extra-$(uname -r) \
    linux-image-extra-virtual
sudo apt-get -y install \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
sudo apt-get update
sudo apt-get -y install docker-ce
sudo usermod -aG docker $(whoami)
