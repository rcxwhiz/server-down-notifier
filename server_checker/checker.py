import coloredlogs
import logging
import time
import socket

import config_setter as cfg
from mcstatus import MinecraftServer

coloredlogs.install(level=cfg.logging_level, ftm='%(asctime)s %(message)s')


class Checker:

	def __init__(self):
		self.player_summary = {}
		self.server = MinecraftServer(cfg.server_url)
		logging.info('Initializing checker')
		cfg.up_text_interval *= 60
		cfg.down_text_interval *= 60
		cfg.check_interval *= 60
		if self.check_server_up():
			self.up_loop()
		else:
			self.down_loop()

	def check_server_up(self):
		logging.debug('Attempting to contact server')
		try:
			status = self.server.status(cfg.fails_required)
		except socket.timeout:
			logging.debug('Attempt to contact server timed out')
			return False
		except socket.gaierror:
			logging.critical('Unable to resolve server address from config')
			return False
		except OSError:
			logging.info('There server responded but not with info')
			return False
		logging.debug('Contact with server successful')
		return True

	def up_loop(self):
		time_since_message = cfg.up_text_interval + 1
		uptime = 0

		logging.debug('Entering up_loop')
		while True:
			if not self.check_server_up():
				self.down_loop()
				return None

			if (not cfg.up_text_interval == 0) and (time_since_message > cfg.up_text_interval):
				self.send_up_message(uptime, self.player_summary)
				time_since_message = 0
				logging.debug(f'Waiting {cfg.up_text_interval / 60:.1f} mins to send up message again')

			# TODO use some webscraping to append to player_list

			logging.debug(f'Waiting {cfg.check_interval / 60:.1f} mins to check server again')
			time.sleep(cfg.check_interval)
			time_since_message += cfg.check_interval

	def down_loop(self):
		time_since_message = cfg.down_text_interval + 1
		downtime = 0

		logging.debug('Entering down loop')
		while True:
			if self.check_server_up():
				self.up_loop()
				return None

			if time_since_message > cfg.down_text_interval:
				self.send_down_message(downtime)
				time_since_message = 0
				logging.debug(f'Waiting {cfg.down_text_interval / 60:.1f} mins to send down message again')

			logging.debug(f'Waiting {cfg.check_interval / 60:.1f} mins to check server again')
			time.sleep(cfg.check_interval)
			if cfg.down_text_interval > 0:
				time_since_message += cfg.check_interval

	def send_up_message(self, uptime, player_list):
		logging.info("The server is up???")

	# TODO make this send as a text

	def send_down_message(self, downtime):
		logging.warning("The server is down???")
	# TODO make this send as a text
