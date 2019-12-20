from configparser import ConfigParser
import logging
import os
import sys

# set working directory and check for config file
os.chdir(os.path.dirname(sys.argv[0]))
CONFIG_NAME = 'config.ini'
config = ConfigParser()
if not os.path.exists(os.path.join(os.getcwd(), CONFIG_NAME)):
	logging.critical(f'{CONFIG_NAME} not found in working directory. Rename config - example.ini?')
	input()
	sys.exit(0)
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

include_timestamp = config.getboolean('message', 'include_timestamp')
include_uptime = config.getboolean('message', 'include_uptime')
include_downtime = config.getboolean('message', 'include_downtime')
include_avg_ping = config.getboolean('message', 'include_avg_ping')
include_max_ping = config.getboolean('message', 'include_max_ping')
include_last_ping = config.getboolean('message', 'include_last_ping')
include_max_players = config.getboolean('message', 'include_max_players')
include_player_log = config.getboolean('message', 'include_player_log')