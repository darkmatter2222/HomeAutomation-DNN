sudo systemctl stop pubsub.service
cd /home/pi/HomeAutomation-DNN
git reset --hard
git pull
sudo systemctl start pubsub.service
sudo journalctl -u pubsub.service -f -n 20
