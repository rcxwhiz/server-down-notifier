import coloredlogs
import logging
import time

import config_setter as cfg

coloredlogs.install(level=cfg.logging_level, ftm='%(asctime)s %(levelname)s %message)s')


class Checker:

	def __init__(self):
		logging.info('Initializing checker')
		if self.check_server_up():
			self.up_loop()
		else:
			self.down_loop()

	def check_server_up(self):
		# TODO this is going to use webscraping to get the server status
		return True

	def up_loop(self):
		player_list = []
		time_since_message = cfg.up_text_interval + 1
		uptime = 0

		while True:
			if not self.check_server_up():
				self.down_loop()
				return None

			if (not cfg.up_text_interval == 0) and (time_since_message > cfg.up_text_interval):
				self.send_up_message(uptime, player_list)
				time_since_message = 0

			# TODO use some webscraping to append to player_list

			time.sleep(cfg.check_interval * 60)
			time_since_message += cfg.check_interval / 60

	def down_loop(self):
		time_since_message = cfg.down_text_interval + 1
		downtime = 0

		while True:
			if self.check_server_up():
				self.up_loop()
				return None

			if time_since_message > cfg.down_text_interval:
				self.send_down_message(downtime)
				time_since_message = 0

			time.sleep(cfg.check_interval * 60)
			if cfg.down_text_interval > 0:
				time_since_message += cfg.check_interval / 60

	def send_up_message(self, uptime, player_list):
		logging.warning("The server is up???")
		# TODO make this send as a text

	def send_down_message(self, downtime):
		logging.warning("The server is down???")
		# TODO make this send as a text
