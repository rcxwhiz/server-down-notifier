import coloredlogs
import logging
import time
import socket
import yagmail

import config_setter as cfg
from mcstatus import MinecraftServer

coloredlogs.install(level=cfg.logging_level, ftm='%(asctime)s %(message)s')


class Checker:

	def __init__(self, email_password_in):
		logging.info('Initializing checker')

		self.email_pswd = email_password_in
		self.player_summary = {}
		self.server = MinecraftServer(cfg.server_address)
		self.status = -cfg.check_interval
		self.server_uptime = 0
		self.server_downtime = 0
		cfg.up_text_interval *= 60
		cfg.down_text_interval *= 60
		cfg.check_interval *= 60
		self.up_loop()

	def send_text_yagmail(self, content, subject_in=''):
		yag = yagmail.SMTP(cfg.email_address, self.email_pswd)
		yag.send(cfg.sms_gateway, subject_in, content)

	def check_server_up(self):
		logging.info('Attempting to contact server')
		try:
			self.status = self.server.status(cfg.fails_required)
		except socket.timeout:
			logging.debug('Attempt to contact server timed out')
			return False
		except socket.gaierror:
			logging.critical('Unable to resolve server address from config')
			return False
		except OSError:
			logging.warning('There server responded but not with info')
			return False
		logging.debug('Contact with server successful')

		if self.status.players.sample is not None:
			current_players = []
			for player_ob in self.status.players.sample:
				current_players.append(player_ob.name)

			for player in current_players:
				if player not in self.player_summary.keys():
					self.player_summary[player] = cfg.check_interval / 2
				else:
					self.player_summary[player] += cfg.check_interval

		self.server_uptime += cfg.check_interval

		return True

	def up_loop(self):
		time_since_message = cfg.up_text_interval
		self.server_downtime = 0

		logging.debug('Entering up_loop')
		while True:
			if not self.check_server_up():
				self.down_loop()
				return None

			if (not cfg.up_text_interval == 0) and (time_since_message >= cfg.up_text_interval):
				self.send_up_message()
				time_since_message = 0
				logging.debug(f'Waiting {cfg.up_text_interval / 60:.1f} mins to send up message again')

			to_wait = cfg.check_interval
			if (cfg.up_text_interval - time_since_message) < cfg.check_interval:
				to_wait = cfg.up_text_interval - time_since_message
			logging.debug(f'Waiting {to_wait / 60:.1f} mins to check server again')
			time.sleep(to_wait)
			time_since_message += to_wait
			self.server_uptime += to_wait

	def down_loop(self):
		self.player_summary = {}
		self.server_uptime = 0
		time_since_message = cfg.down_text_interval

		logging.debug('Entering down loop')
		while True:
			if time_since_message >= cfg.down_text_interval:
				self.send_down_message()
				time_since_message = 0
				logging.debug(f'Waiting {cfg.down_text_interval / 60:.1f} mins to send down message again')

			to_wait = cfg.check_interval
			if (cfg.down_text_interval - time_since_message) < cfg.check_interval:
				to_wait = cfg.down_text_interval - time_since_message
			logging.debug(f'Waiting {to_wait / 60:.1f} mins to check server again')
			time.sleep(to_wait)
			if cfg.down_text_interval > 0:
				time_since_message += to_wait
			self.server_downtime += to_wait

			if self.check_server_up():
				self.up_loop()
				return None

	def send_up_message(self):
		logging.info(f'Server online - Uptime: {self.server_uptime / 3600:.1f} hrs')
		logging.info('Players online:')
		message_subject = 'Server Status - Online'
		message = f'Uptime: {self.server_uptime / 3600:.1f} hrs\rPlayers online:'
		for player in self.player_summary.keys():
			logging.info(f'{player}: {self.player_summary[player] / 3600:.1f} hrs')
			message += f'\n{player}: {self.player_summary[player] / 3600:.1f} hrs'
		self.send_text_yagmail(message, message_subject)

	def send_down_message(self):
		logging.warning(f'Server offline - Downtime: {self.server_downtime / 3600:.1f} hrs')
		self.send_text_yagmail(f'Downtime: {self.server_downtime / 3600:.1f} hrs', 'Server Status - Offline!')
