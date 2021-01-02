import sys, os
sys.path.append('/home/pi/HomeAutomation-DNN')
import Initialize_Project as ip

logger = ip.initialize()

logger.info('Main Initialized, testing...')
print(os.getenv('Google_Nest_Username'))
