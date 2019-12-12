import config_setter as cfg
import logging
import coloredlogs
coloredlogs.install(level=cfg.logging_level, ftm='%(asctime)s %(levelname)s %message)s')


class Checker:

	def __init__(self):
		logging.info('Initializing checker')
