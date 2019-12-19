from configparser import ConfigParser
import os
import sys

# set working directory
os.chdir(os.path.dirname(sys.argv[0]))
CONFIG_NAME = 'config.ini'
config = ConfigParser()
config.read(os.path.join(os.getcwd(), CONFIG_NAME))

# all units get converted to seconds
server_address = config.get('setup', 'server_address')
server_port = config.getint('setup', 'server_port')
sms_gateway = config.get('setup', 'sms_gateway')
email_address = config.get('setup', 'email_address')
check_interval = config.getfloat('setup', 'check_interval') * 60
logging_level = config.get('setup', 'logging_level')

fails_required = config.getint('preferrences', 'fails_required')
down_text_interval = config.getfloat('preferrences', 'down_text_interval') * 60
up_text_interval = config.getfloat('preferrences', 'up_text_interval') * 60
try_player_log = config.getboolean('preferrences', 'try_player_log')
