import coloredlogs
import logging
import time

import config_setter as cfg

coloredlogs.install(level=cfg.logging_level, ftm='%(asctime)s %(levelname)s %message)s')


class Checker:

	def __init__(self):
		logging.info('Initializing checker')
		self.failed = False
		self.up_loop()

	def up_loop(self):
		time_since_message = 0
		while True:
			time.sleep(cfg.check_interval * 60)
			time_since_message += cfg.check_interval / 60
			if not cfg.up_text_interval == 0 and time_since_message > cfg.up_text_interval:
				self.send_up_message()

	def send_up_message(self):
		logging.warning("I'm supposed to make this text me with info")
