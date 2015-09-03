#!/bin/bash

cd /home/pi/extremefeedbacklamp || exit

MYPWD=$(pwd)
git clone https://github.com/WiringPi/WiringPi2-Python.git || true
cd WiringPi2-Python
git fetch
sudo git clean -fxd
git reset --hard origin/master

# roll back commits one at a time until WiringPi builds and installs
sudo python setup.py install
WIRINGRET=$?
while [ $WIRINGRET -ne 0 ]
do
  git reset --hard HEAD~1
  sudo git clean -fxd
  sudo python setup.py install
  WIRINGRET=$?
done

cd $MYPWD
sync
