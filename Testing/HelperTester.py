import Helpers.Exception_Handling.Exception_Handling as eh

import logging.handlers
import sys, os

my_logger = logging.getLogger('MyLogger')
my_logger.setLevel(logging.INFO)
if os.name != 'nt':
    handler = logging.handlers.SysLogHandler(address='/dev/log')
    my_logger.addHandler(handler)

my_logger.info('Initializing .env')
target_image_root = '/home/pi/neural/HomeAutomation-DNN/images'
target_env_path = '/home/pi/secure'  # default linux
if os.name == 'nt':
    target_env_path = '\\\\SUSMANSERVER\\Active Server Drive\\HomeAutomation' # Windows
    target_image_root = '../../testing'
else:
    sys.path.append('/home/pi/HomeAutomation-DNN')  # add this to the path
    sys.path.append('/home/pi/secure')  # add this to the path
    sys.path.append('/home/pi/Helpers')  # add this to the path
    sys.path.append('/home/pi/Helpers/Exception_Handling')  # add this to the path


eh.test('If you are seeing this, it worked')