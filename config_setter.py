from configparser import ConfigParser

CONFIG_NAME = 'config.ini'
config = ConfigParser()
config.read(CONFIG_NAME)

status_url = config.get('setup', 'status_url')
phone_number = config.get('setup', 'status_url')
check_interval = config.getfloat('setup', 'check_interval')
logging_level = config.get('setup', 'logging_level')

fails_required = config.getint('preferrences', 'fails_required')
down_text_interval = config.getfloat('preferrences', 'down_text_interval')
up_text_interval = config.getfloat('preferrences', 'up_text_interval')
