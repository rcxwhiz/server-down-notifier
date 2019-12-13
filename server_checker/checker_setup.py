import coloredlogs
import datetime
import logging
import threading
import time
import re
import socket
import yagmail

import config_setter as cfg
from mcstatus import MinecraftServer

coloredlogs.DEFAULT_LOG_FORMAT = '[%(asctime)s] [%(levelname)s] %(message)s'
coloredlogs.DEFAULT_FIELD_STYLES = {
	'asctime': {'color': 'white'},
	'hostname': {'color': 'white'},
	'levelname': {'color': 'yellow', 'bold': True},
	'name': {'color': 'blue'},
	'programname': {'color': 'cyan'}
	}
coloredlogs.install(level=cfg.logging_level, datefmt='%I:%M:%S %p')
