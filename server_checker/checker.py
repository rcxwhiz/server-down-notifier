import coloredlogs
import logging
import time
import smtplib
import socket
import yagmail

import config_setter as cfg
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from mcstatus import MinecraftServer

coloredlogs.install(level=cfg.logging_level, ftm='%(asctime)s %(message)s')


class Checker:

	def __init__(self, email_password_in):
		logging.info('Initializing checker')

		self.email_pswd = email_password_in
		self.send_text_yagmail('It worked')

		self.player_summary = {}
		self.server = MinecraftServer(cfg.server_url)
		self.status = -cfg.check_interval
		self.server_uptime = 0
		self.server_downtime = 0
		cfg.up_text_interval *= 60
		cfg.down_text_interval *= 60
		cfg.check_interval *= 60
		self.up_loop()

	def send_text_yagmail(self, content):
		yag = yagmail.SMTP(cfg.email_address, self.email_pswd)
		yag.send(cfg.sms_gateway, 'subject', content)

	def send_text(self, content):
		email_server = smtplib.SMTP(cfg.smtp, cfg.email_port)
		email_server.starttls()
		email_server.login(cfg.email_address, self.email_pswd)

		msg = MIMEMultipart()
		# msg['From'] = cfg.email_address
		# msg['To'] = cfg.sms_gateway
		msg['Subject'] = ' Server Status\n'
		msg.attach(MIMEText(f' {content}\n', 'plain'))
		sms = msg.as_string()
		email_server.sendmail(cfg.email_address, cfg.sms_gateway, sms)
		email_server.quit()

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
		time_since_message = cfg.up_text_interval + 1
		self.server_downtime = 0

		logging.debug('Entering up_loop')
		while True:
			if not self.check_server_up():
				self.down_loop()
				return None

			if (not cfg.up_text_interval == 0) and (time_since_message > cfg.up_text_interval):
				self.send_up_message()
				time_since_message = 0
				logging.debug(f'Waiting {cfg.up_text_interval / 60:.1f} mins to send up message again')

			logging.debug(f'Waiting {cfg.check_interval / 60:.1f} mins to check server again')
			time.sleep(cfg.check_interval)
			time_since_message += cfg.check_interval
			self.server_uptime += cfg.check_interval

	def down_loop(self):
		self.player_summary = {}
		self.server_uptime = 0
		time_since_message = cfg.down_text_interval + 1

		logging.debug('Entering down loop')
		while True:
			if time_since_message > cfg.down_text_interval:
				self.send_down_message()
				time_since_message = 0
				logging.debug(f'Waiting {cfg.down_text_interval / 60:.1f} mins to send down message again')

			logging.debug(f'Waiting {cfg.check_interval / 60:.1f} mins to check server again')
			time.sleep(cfg.check_interval)
			if cfg.down_text_interval > 0:
				time_since_message += cfg.check_interval
			self.server_downtime += cfg.check_interval

			if self.check_server_up():
				self.up_loop()
				return None

	def send_up_message(self):
		logging.info(f'Server online - Uptime: {self.server_uptime / 3600:.1f} hrs')
		logging.info('Players online:')
		for player in self.player_summary.keys():
			logging.info(f'{player}: {self.player_summary[player] / 3600:.1f} hrs')
		# TODO make this send as a text

	def send_down_message(self):
		logging.warning(f'Server offline - Downtime: {self.server_downtime / 3600:.1f} hrs')
		# TODO make this send as a text
