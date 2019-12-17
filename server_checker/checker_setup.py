import coloredlogs
import datetime
import logging
import threading
import time
import socket
import re

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
		logging.debug('Initializing perfect timer')

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

	def __init__(self, address_in, port_in, yag_in):
		logging.debug('Initializing server')

		self.yag = yag_in
		self.int_server = MinecraftServer(address_in, port_in)
		self.address = address_in
		self.port = port_in

		self.update_timer = None
		self.message_timer = None
		self.current_message_interval = None
		self.last_status = None
		self.uptime = 0
		self.downtime = 0
		self.player_summary = {}
		self.pings = []

		self.send_message()
		self.loop()

	def loop(self):
		if not (self.update() == self.last_status):
			self.message_timer.cancel()
			self.send_message()
			if self.online():
				self.current_message_interval = cfg.up_text_interval
			else:
				self.current_message_interval = cfg.down_text_interval
			self.message_timer = PTimer(self.current_message_interval, self.send_message)
		self.update_timer = PTimer(cfg.check_interval, self.loop)

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
			self.pings.append({'ping': self.last_status.latency, 'time': time.time()})
			if self.last_status.players.sample is not None:
				current_players = []
				for player_ob in self.last_status.players.sample:
					current_players.append(player_ob.name)

				for player in self.player_summary.keys():
					self.player_summary[player].append({'online': player in current_players, 'time': time.time()})

				for player in current_players:
					if player not in self.player_summary.keys():
						self.player_summary[player] = {'online': True, 'time': time.time()}
		return True

	def send_message(self, console=True, text=True, update_before=True):
		if update_before:
			self.update()

		if self.online():
			next_message = cfg.up_text_interval
			if console:
				self.log_up_message()
			if text:
				message, message_subject = self.text_up_message()
				self.yag.send(cfg.sms_gateway, message, message_subject)
				format_phone = '(%s) %s-%s' % tuple(re.findall(r'\d{4}$|\d{3}', cfg.sms_gateway[:10]))
				logging.info(f'Sent text to {format_phone}')
		else:
			next_message = cfg.down_text_interval
			if console:
				self.log_down_message()
			if text:
				message, message_subject = self.text_down_message()
				self.yag.send(cfg.sms_gateway, message, message_subject)
				format_phone = '(%s) %s-%s' % tuple(re.findall(r'\d{4}$|\d{3}', cfg.sms_gateway[:10]))
				logging.info(f'Sent text to {format_phone}')

		self.player_summary = {}
		self.pings = []
		self.message_timer = PTimer(next_message, self.send_message)

	def online(self):
		return self.last_status is not False

	def get_avg_ping(self):
		total = 0
		for i in range(len(self.pings) - 1):
			total += self.pings[i]['ping'] * (self.pings[i + 1]['time'] - self.pings[i]['time'])
		return total / (self.pings[-1]['time'] - self.pings[0]['time'])

	def get_player_time(self, player):
		total = 0
		for i in range(len(self.player_summary[player]) - 1):
			if self.player_summary[player][i]['online']:
				total += self.player_summary[player][i + 1]['time'] - self.player_summary[player][i]['time']
		return total / (self.player_summary[player][-1]['time'] - self.player_summary[player][0]['time'])

	def log_up_message(self):
		logging.info(f'Server {self.address} online - Uptime: {self.uptime / 3600:.1f} hrs')
		logging.info(f'Avg ping: {self.get_avg_ping():.0f} ms')
		logging.info(f'Max ping: {max(self.pings[:][0]):.0f} ms')
		logging.info(f'Last ping: {self.pings[-1][0]:.0f} ms')
		logging.info('Players online:')
		if len(self.player_summary.keys()) == 0:
			logging.info('None')
		else:
			for player in self.player_summary.keys():
				logging.info(f'{player}: {self.get_player_time(player) / 3600:.1f} hrs')

	def log_down_message(self):
		logging.warning(f'Server {self.address} offline - Downtime: {self.downtime / 3600:.1f} hrs')

	def text_up_message(self):
		message_subject = f'Server Status {cfg.server_address}: Online'
		message = f'[{datetime.now().strftime("%I:%M:%S %p")}]\r'
		message += f'Uptime: {int(self.uptime / 86400)} days '
		message += f'{(self.uptime - self.uptime % 86400) / 3600:.1f} hrs\r'
		message += f'Avg ping: {self.get_avg_ping():.0f} ms\r'
		message += f'Max ping: {max(self.pings):.0f} ms\r'
		message += f'Last ping: {self.pings[-1]:.0f} ms\r'
		message += 'Players online:'
		if len(self.player_summary.keys()) == 0:
			message += '\rNone'
		else:
			for player in self.player_summary.keys():
				message += f'\r{player}: {self.get_player_time(player) / 3600:.1f} hrs'
		return message, message_subject

	def text_down_message(self):
		message_subject = f'Server {cfg.server_address} Status: Offline!'
		message = f'[{datetime.now().strftime("%I:%M:%S %p")}]\r'
		message += f'Downtime: {(self.downtime - self.downtime % 86400) / 3600:.1f} days '
		message += f'{self.downtime / 3600:.1f} hrs'
		return message, message_subject
