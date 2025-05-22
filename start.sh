#!/bin/sh
apt-get update && apt-get install -y libgl1

pip install -r requirements.txt