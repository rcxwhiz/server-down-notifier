from configparser import ConfigParser

CONFIG_NAME = 'config.ini'
config = ConfigParser()
config.read(CONFIG_NAME)

status_url = config.get('setup', 'status_url')
phone_number = config.get('setup', 'status_url')
check_interval = config.getint('setup', 'check_interval')
logging_level = config.get('setup', 'logging_level')

fails_required = config.getint('preferrences', 'fails_required')
text_interval = config.getfloat('preferrences', 'text_interval')
send_succeed = config.getboolean('preferrences', 'send_succeed')
