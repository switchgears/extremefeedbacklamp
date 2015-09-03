#!/bin/bash
cd /home/pi/extremefeedbacklamp
git remote update || true
git fetch || true
DELTAPRE=$(git rev-list HEAD...origin/master --count)
git reset --hard origin/master
DELTAPOST=$(git rev-list HEAD...origin/master --count)
if [ "$DELTAPRE" != "$DELTAPOST" ]
then
    echo "updates found ... rerunning install ..."
    sudo ln -sf /home/pi/extremefeedbacklamp/xfdlampupdate.sh /etc/cron.daily/xfdlampupdate
    sudo chmod +x /etc/cron.daily/xfdlampupdate
    sudo chown -R pi:pi /home/pi/extremefeedbacklamp
    sudo /home/pi/extremefeedbacklamp/install.sh
    sudo shutdown -r now
fi
