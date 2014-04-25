#!/bin/bash

apt-get update
apt-get install -y python-pip git
pip install pip --upgrade
pip install boto --upgrade

git clone https://github.com/adsabs/adsabs-aws /adsabs-aws
/usr/bin/python  /adsabs-aws/aws_provisioner.py --zookeeper