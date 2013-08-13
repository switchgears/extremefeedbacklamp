#!/bin/bash
cd /home/pi/extremefeedbacklamp
git fetch
DELTAPRE=$(git rev-list HEAD...origin/master --count)
git reset --hard origin/master
DELTAPOST=$(git rev-list HEAD...origin/master --count)
if [ "$DELTAPRE" != "$DELTAPOST" ]
then
    echo "update found and applied succesfully, rebooting"
    sudo cp -f /home/pi/extremefeedbacklamp/xfdlampupdate.sh /etc/cron.daily/xfdlampupdate
    sudo chmod +x /etc/cron.daily/xfdlampupdate
    #sudo cp -f /home/pi/extremefeedbacklamp/xfdlampupdate.sh /etc/cron.hourly/xfdlampupdate
    #sudo chmod +x /etc/cron.hourly/xfdlampupdate
    sudo shutdown -r now
fi
