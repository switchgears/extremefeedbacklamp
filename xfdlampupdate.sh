#!/bin/bash
cd /home/pi/extremefeedbacklamp
git remote update
DELTAPRE=$(git rev-list HEAD...origin/master --count)
git reset --hard origin/master
DELTAPOST=$(git rev-list HEAD...origin/master --count)
if [ "$DELTAPRE" != "$DELTAPOST" ]
then
    echo "update found and applied succesfully, rebooting"
    sudo cp -f /home/pi/extremefeedbacklamp/xfdlampupdate.sh /etc/cron.daily/xfdlampupdate
    sudo chmod +x /etc/cron.daily/xfdlampupdate
    sudo chown -R pi:pi /home/pi/extremefeedbacklamp
    #sudo cp -f /home/pi/extremefeedbacklamp/xfdlampupdate.sh /etc/cron.hourly/xfdlampupdate
    #sudo chmod +x /etc/cron.hourly/xfdlampupdate
    sudo shutdown -r now
fi
