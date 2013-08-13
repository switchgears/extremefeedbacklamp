#!/bin/bash

# expand image to whole sd-card
export LANG=C
sudo raspi-config --expand-rootfs

# Disable boot straight to desktop
sudo update-rc.d lightdm disable 2 2>/dev/null

# generally update
sudo apt-get update -y
sudo apt-get dist-upgrade -y
sudo apt-get autoremove -y
sudo apt-get autoclean -y
sync

# install missing bits
sudo apt-get install python-dev python-setuptools git htop mpg321 -y

# install wiringpi2
git clone https://github.com/WiringPi/WiringPi2-Python.git
cd WiringPi2-Python
sudo python setup.py install
cd ..

sync

# install xfd as startup application
sudo cp -f ./initd_switchgearsXFD /etc/init.d/switchgearsXFD
sudo cp -f ./initd_switchgearsXFD_discovery /etc/init.d/switchgearsXFD_discovery
sudo cp -f ./initd_jenkins_confirm /etc/init.d/jenkins_confirm

sudo chmod 755 /etc/init.d/switchgearsXFD
sudo chmod 755 /etc/init.d/switchgearsXFD_discovery
sudo chmod 755 /etc/init.d/jenkins_confirm

sudo chown root:root /etc/init.d/switchgearsXFD
sudo chown root:root /etc/init.d/switchgearsXFD_discovery
sudo chown root:root /etc/init.d/jenkins_confirm

sudo update-rc.d switchgearsXFD defaults
sudo update-rc.d switchgearsXFD_discovery defaults
sudo update-rc.d jenkins_confirm defaults

sync

sudo apt-get autoremove -y
sudo apt-get autoclean -y

sudo cp -f /home/pi/extremefeedbacklamp/xfdlampupdate.sh /etc/cron.daily/xfdlampupdate
sudo chmod +x /etc/cron.daily/xfdlampupdate
# if daily updates just ain't quick enough
#sudo cp -f /home/pi/extremefeedbacklamp/xfdlampupdate.sh /etc/cron.hourly/xfdlampupdate
#sudo chmod +x /etc/cron.hourly/xfdlampupdate

sync

# reboot
sudo reboot
