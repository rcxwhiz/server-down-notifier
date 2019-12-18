import coloredlogs
import datetime
import logging
import threading
import time
import socket
import re

import config_setter as cfg
from p_timer import *
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
		self.uptime = []
		self.downtime = []
		self.player_summary = {}
		self.pings = []

		self.last_status = None
		self.send_message()
		self.previous_update = self.online()
		self.loop()

	def loop(self):
		if not (self.update() == self.previous_update):
			self.message_timer.cancel()
			self.send_message(update_before=False)
			if self.online():
				self.current_message_interval = cfg.up_text_interval
			else:
				self.current_message_interval = cfg.down_text_interval
			self.message_timer = PTimer(self.current_message_interval, self.send_message)
		self.update_timer = PTimer(cfg.check_interval, self.loop)
		self.previous_update = self.online()

	def update(self, log=True, retries=0):
		logging.info(f'Contacting Server {self.address}')
		try:
			self.last_status = self.int_server.status(cfg.fails_required)
		except socket.timeout:
			self.uptime = []
			self.downtime.append(time.time())
			logging.info('Attempt to contact server timed out')
			self.last_status = False
			return False
		except socket.gaierror:
			self.uptime = []
			self.downtime.append(time.time())
			logging.critical('Unable to resolve server address from config')
			self.last_status = False
			return False
		except OSError:
			self.uptime = []
			self.downtime.append(time.time())
			logging.warning('The server responded but not with info')
			time.sleep(2)
			self.last_status = False
			if retries < 3:
				return self.update(retries=retries + 1)
			else:
				return False

		self.uptime.append(time.time())
		self.downtime = []
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
						self.player_summary[player] = []
						self.player_summary[player].append({'online': True, 'time': time.time()})
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
				self.yag.send(cfg.sms_gateway, message_subject, message)
				format_phone = '(%s) %s-%s' % tuple(re.findall(r'\d{4}$|\d{3}', cfg.sms_gateway[:10]))
				logging.info(f'Sent text to {format_phone}')
		else:
			next_message = cfg.down_text_interval
			if console:
				self.log_down_message()
			if text:
				message, message_subject = self.text_down_message()
				self.yag.send(cfg.sms_gateway, message_subject, message)
				format_phone = '(%s) %s-%s' % tuple(re.findall(r'\d{4}$|\d{3}', cfg.sms_gateway[:10]))
				logging.info(f'Sent text to {format_phone}')

		self.player_summary = {}
		self.pings = []
		self.message_timer = PTimer(next_message, self.send_message)

	def online(self):
		return self.last_status is not False

	def get_avg_ping(self):
		if len(self.pings) == 1:
			return self.pings[0]['ping']
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

	def get_max_ping(self):
		temp_pings = []
		for point in self.pings:
			temp_pings.append(point['ping'])
		return max(temp_pings)

	def get_uptime(self):
		return self.uptime[-1] - self.uptime[0]

	def get_downtime(self):
		return self.downtime[-1] - self.downtime[0]

	def log_up_message(self):
		logging.info(f'{self.address} online - Uptime: {self.get_uptime() / 3600:.1f} hrs')
		logging.info(f'Avg ping: {self.get_avg_ping():.0f} ms')
		logging.info(f'Max ping: {self.get_max_ping():.0f} ms')
		logging.info(f'Last ping: {self.pings[-1]["ping"]:.0f} ms')
		logging.info('Players online:')
		if len(self.player_summary.keys()) == 0:
			logging.info('None')
		else:
			for player in self.player_summary.keys():
				logging.info(f'{player}: {self.get_player_time(player) / 3600:.1f} hrs')

	def log_down_message(self):
		logging.warning(f'{self.address} offline - Downtime: {self.get_downtime() / 3600:.1f} hrs')

	def text_up_message(self):
		message_subject = f'Status {cfg.server_address}: Online'
		message = f'[{datetime.now().strftime("%I:%M:%S %p")}]\r'
		message += f'Uptime: {int((self.get_uptime() - (self.get_uptime() % 86400)) / 86400)} days '
		message += f'{(self.get_uptime() % 86400) / 3600:.1f} hrs\r'
		message += f'Avg ping: {self.get_avg_ping():.0f} ms\r'
		message += f'Max ping: {self.get_max_ping():.0f} ms\r'
		message += f'Last ping: {self.pings[-1]["ping"]:.0f} ms\r'
		message += 'Players online:'
		if len(self.player_summary.keys()) == 0:
			message += '\rNone'
		else:
			for player in self.player_summary.keys():
				message += f'\r{player}: {self.get_player_time(player) / 3600:.1f} hrs'
		return message, message_subject

	def text_down_message(self):
		message_subject = f'{cfg.server_address} Status: Offline!'
		message = f'[{datetime.now().strftime("%I:%M:%S %p")}]\r'
		message += f'Downtime: {(self.get_downtime() - self.get_downtime() % 86400) / 3600:.1f} days '
		message += f'{self.get_downtime() / 3600:.1f} hrs'
		return message, message_subject
