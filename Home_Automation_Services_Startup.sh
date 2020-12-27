cd /home/pi/HomeAutomation-DNN
/usr/bin/python3 Services/PubSub_Nest_Subscriber.py &
/usr/bin/python3 Services/OAuth_Token_Refresh_Engine.py &
/usr/bin/python3 Services/Device_Metadata_Updater.py