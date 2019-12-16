import coloredlogs
import datetime
import logging
import threading
import time
import socket

import config_setter as cfg
from mcstatus import MinecraftServer
from datetime import datetime

coloredlogs.DEFAULT_LOG_FORMAT = '[%(asctime)s] [%(levelname)s] %(message)s'
coloredlogs.DEFAULT_FIELD_STYLES = {
	'asctime': {'color': 'white'},
	'hostname': {'color': 'white'},
	'levelname': {'color': 'yellow', 'bold': True},
	'name': {'color': 'blue'},
	'programname': {'color': 'cyan'}
	}
coloredlogs.install(level=cfg.logging_level, datefmt='%I:%M:%S %p')


class PTimer:

	def __init__(self, time_in, function_in, args_in=(), start=True):
		logging.debug('Creating new perfect timer')
		self.int_timer = threading.Timer(time_in, function_in, args=args_in)
		self.interval = time_in
		self.func = function_in
		self.arg = args_in
		self.time_started = None
		if start:
			self.start()

	def start(self):
		self.int_timer.start()
		self.time_started = time.time()

	def cancel(self):
		self.int_timer.cancel()

	def pause(self):
		self.int_timer.cancel()
		self.int_timer = threading.Timer(self.remaining(), self.func, self.arg)

	def remaining(self):
		return self.interval - (time.time() - self.time_started)

	def elapsed(self):
		return time.time() - self.time_started

	def new_time(self, new_time_in, go=True):
		self.cancel()
		self.int_timer = threading.Timer(new_time_in, self.func, self.arg)
		if go:
			self.start()


class MServer:

	def __init__(self, address_in, port_in):
		self.int_server = MinecraftServer(address_in, port_in)
		self.address = address_in
		self.port = port_in

		self.update_timer = None
		self.last_status = None
		self.uptime = 0
		self.downtime = 0
		self.player_summary = {}
		self.pings = []

		self.update()

	def update(self, log=True):
		logging.info(f'Contacting Server {self.address}')
		try:
			self.last_status = self.int_server.status(cfg.fails_required)
		except socket.timeout:
			self.uptime = 0
			self.downtime += cfg.check_interval
			logging.info('Attempt to contact server timed out')
			self.last_status = False
			return False
		except socket.gaierror:
			self.uptime = 0
			self.downtime += cfg.check_interval
			logging.critical('Unable to resolve server address from config')
			self.last_status = False
			return False
		except OSError:
			self.uptime = 0
			self.downtime += cfg.check_interval
			logging.warning('The server responded but not with info')
			self.last_status = False
			time.sleep(2)
			return self.update()

		self.uptime += cfg.check_interval
		self.downtime = 0
		logging.debug('Contact with server successful')

		if log:
			self.pings.append(self.last_status.latency)
			if self.last_status.players.sample is not None:
				current_players = []
				for player_ob in self.last_status.players.sample:
					current_players.append(player_ob.name)

				for player in current_players:
					if player not in self.player_summary.keys():
						self.player_summary[player] = cfg.check_interval / 2
					else:
						self.player_summary[player] += cfg.check_interval
		return True

	def send_message(self, console=True, text=True, update_before=True):
		if update_before:
			self.update()
		if console:
			if self.last_status is not False:
				self.log_up_message()
			else:
				self.log_down_message()

		if text:
			if self.last_status is not False:
				return self.text_up_message()
			else:
				return self.text_down_message()

	def online(self):
		return self.last_status is not False

	def log_up_message(self):
		logging.info(f'Server {self.address} online - Uptime: {self.uptime / 3600:.1f} hrs')
		logging.info(f'Avg ping: {sum(self.pings) / len(self.pings):.0f} ms')
		logging.info(f'Max ping: {max(self.pings):.0f} ms')
		logging.info(f'Last ping: {self.pings[-1]:.0f} ms')
		logging.info('Players online:')
		if len(self.player_summary.keys()) == 0:
			logging.info('None')
		else:
			for player in self.player_summary.keys():
				logging.info(f'{player}: {self.player_summary[player] / 3600:.1f} hrs')

	def log_down_message(self):
		logging.warning(f'Server {self.address} offline - Downtime: {self.downtime / 3600:.1f} hrs')

	def text_up_message(self):
		message_subject = f'Server Status {cfg.server_address}: Online'
		message = f'[{datetime.now().strftime("%I:%M:%S %p")}]\r'
		message += f'Uptime: {int(self.uptime / 86400)} days '
		message += f'{(self.uptime - self.uptime % 86400) / 3600:.1f} hrs\r'
		message += f'Avg ping: {sum(self.pings) / len(self.pings):.0f} ms\r'
		message += f'Max ping: {max(self.pings):.0f} ms\r'
		message += f'Last ping: {self.pings[-1]:.0f} ms\r'
		message += 'Players online:'
		if len(self.player_summary.keys()) == 0:
			message += '\rNone'
		else:
			for player in self.player_summary.keys():
				message += f'\r{player}: {self.player_summary[player] / 3600:.1f} hrs'
		return message, message_subject

	def text_down_message(self):
		message_subject = f'Server {cfg.server_address} Status: Offline!'
		message = f'[{datetime.now().strftime("%I:%M:%S %p")}]\r'
		message += f'Downtime: {(self.downtime - self.downtime % 86400) / 3600:.1f} days '
		message += f'{self.downtime / 3600:.1f} hrs'
		return message, message_subject
