extremefeedbacklamp
===================

Raspberry pi based eXtreme Feedback Device

Welcome to the amazing world of EXTREME Feedback

Brought to you by Switch-Gears ApS (switch-gears.dk)

To install on a blank 4GB SD card first download a fresh 
Debian image from http://www.raspberrypi.org/downloads

use dd to flash the card, on my machine this command gets the job done,
but read some documentation first :)

    sudo dd bs=4M if=./2013-07-26-wheezy-raspbian.img of=/dev/mmcblk0

log in via ssh (uname:pi, pw:raspberry)

install git: 

    sudo apt-get install git

clone the project:

    git clone https://github.com/switchgears/extremefeedbacklamp.git

Switch to the extremefeedbacklamp directory and run sudo ./install.sh
This operation can take a fairly long time... and when it's done
your XFD is ready to go

In case of problems please don't hesitate to contact Switch-Gears via:
info@switch-gears.dk
