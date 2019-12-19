from server_checker.checker import Checker
from config_setter import email_address, logging_level
import coloredlogs

version = 3.1
coloredlogs.DEFAULT_LOG_FORMAT = '[%(asctime)s] [%(levelname)s] %(message)s'
coloredlogs.DEFAULT_FIELD_STYLES = {
	'asctime': {'color': 'white'},
	'hostname': {'color': 'white'},
	'levelname': {'color': 'yellow', 'bold': True},
	'name': {'color': 'blue'},
	'programname': {'color': 'cyan'}
	}
coloredlogs.install(level=logging_level, datefmt='%I:%M:%S %p')
