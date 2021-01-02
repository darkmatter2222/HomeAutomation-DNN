import logging.handlers
import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def initialize():
    my_logger = logging.getLogger('MyLogger')
    my_logger.setLevel(logging.INFO)
    if os.name != 'nt':
        handler = logging.handlers.SysLogHandler(address='/dev/log')
        my_logger.addHandler(handler)

    my_logger.info('Initializing Path')
    target_env_path = '/home/pi/secure'  # default linux
    if os.name == 'nt':
        target_env_path = '\\\\SUSMANSERVER\\Active Server Drive\\HomeAutomation'  # Windows
    else:
        sys.path.append('/home/pi/HomeAutomation-DNN')  # add this to the path
        sys.path.append('/home/pi/secure')  # add this to the path

    my_logger.info('Initializing Environment')
    env_path = Path(target_env_path) / '.env'
    load_dotenv(dotenv_path=env_path)

    return my_logger