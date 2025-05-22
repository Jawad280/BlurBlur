#!/bin/sh
apt-get update && apt-get install -y libgl1-mesa-glx

exec python app.py