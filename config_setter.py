from configparser import ConfigParser

CONFIG_NAME = 'config.ini'
config = ConfigParser()
config.read(CONFIG_NAME)

server_url = config.get('setup', 'server_url')
sms_gateway = config.get('setup', 'sms_gateway')
email_address = config.get('setup', 'email_address')
smtp = config.get('setup', 'smtp')
email_port = config.get('setup', 'email_port')
check_interval = config.getfloat('setup', 'check_interval')
logging_level = config.get('setup', 'logging_level')

fails_required = config.getint('preferrences', 'fails_required')
down_text_interval = config.getfloat('preferrences', 'down_text_interval')
up_text_interval = config.getfloat('preferrences', 'up_text_interval')
