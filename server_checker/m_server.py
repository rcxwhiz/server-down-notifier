import logging
import time
import socket
import sys
import re

from p_timer import *
from mcstatus import MinecraftServer
from datetime import datetime

from server_checker.checker_setup import cfg


class MServer:

	def __init__(self, address_in, port_in, yag_in):
		logging.debug('Initializing server')

		self.yag = yag_in
		self.int_server = MinecraftServer(address_in, port_in)
		self.address = address_in
		self.port = port_in
		self.description = None
		self.max_players = None
		self.num_mods = None
		self.version = None
		self.query_allowed = None

		self.update_timer = None
		self.message_timer = None
		self.uptime = []
		self.downtime = []
		self.player_summary = {}
		self.pings = []
		self.max_online = 0

		self.last_status = None

		# send a first message
		# this will auto update the server to populate initial info
		self.send_message()

		# this uses the initial info and starts the loop
		self.previous_update = self.online()
		self.loop()

	def loop(self):
		# checks if the status of the server has changed while triggering an update
		if not (self.update() == self.previous_update):
			self.message_timer.cancel()
			# does not update before message sent because there was just an update
			self.send_message(update_before=False)
		# set update timer and previous status
		self.update_timer = PTimer(cfg.check_interval, self.loop)
		self.previous_update = self.online()

	def update(self, log=True, retries=0):
		logging.debug(f'Contacting Server {self.address}')
		try:
			self.last_status = self.int_server.status(cfg.fails_required)
		except socket.timeout:
			# this is usually what happens when the server is offline
			self.uptime = []
			self.downtime.append(time.time())
			logging.info('Attempt to contact server timed out')
			self.last_status = False
			return False
		except socket.gaierror:
			# this is usually what happens when the address is incorrect so the program exits
			logging.critical('Unable to resolve server address from config')
			sys.exit(0)
		except OSError:
			# this usualyl happens when the server is still loading or overloaded
			self.uptime = []
			self.downtime.append(time.time())
			logging.warning('The server responded but not with info')
			time.sleep(2)
			self.last_status = False
			# this retries the check a few times
			if retries < 3:
				return self.update(retries=retries + 1)
			else:
				return False

		self.uptime.append(time.time())
		self.downtime = []
		logging.debug('Contact with server successful')

		# tests if this is the first successful contact with the server
		if self.description is None:
			if type(self.last_status.description) is str:
				self.description = self.last_status.description
			else:
				self.description = self.last_status.description['text']
			self.max_players = self.last_status.players.max
			self.num_mods = len(self.last_status.raw['modinfo']['modList'])
			self.version = self.last_status.version.name
			# this tests to see if query is enabled and disables player logging if needed
			try:
				self.int_server.query()
				self.query_allowed = True
			except socket.timeout:
				self.query_allowed = False
				logging.error('Query is not allowed on this server so individual players will not be logged!')
				cfg.try_player_log = False
			# after the server info is initially populated it is printed
			self.print_server_info()

		# if this update is supposed to be logged info is recorded
		if log:
			self.pings.append({'ping': self.last_status.latency, 'time': time.time()})

			self.max_online = max(self.max_online, self.last_status.players.online)

			if cfg.try_player_log:
				query = self.int_server.query()
				if len(query.players.names) > 0:
					current_players = []
					for player_ob in query.players.names:
						current_players.append(player_ob.name)

					for player in self.player_summary.keys():
						self.player_summary[player].append({'online': player in current_players, 'time': time.time()})

					for player in current_players:
						if player not in self.player_summary.keys():
							self.player_summary[player] = []
							self.player_summary[player].append({'online': True, 'time': time.time()})

		return True

	def print_server_info(self):
		logging.info(f'[SERVER INFO] Address: {cfg.server_address}:{cfg.server_port}')
		logging.info(f'[SERVER INFO] Query allowed: {self.query_allowed}')
		logging.info(f'[SERVER INFO] Description: {self.description}')
		logging.info(f'[SERVER INFO] Max players: {self.max_players}')
		if self.num_mods > 0:
			logging.info(f'[SERVER INFO] Version: {self.version} - {self.num_mods} mods')
		else:
			logging.info(f'[SERVER INFO] Version: {self.version} - Vanilla')

	def send_message(self, console=True, text=True, update_before=True):
		if update_before:
			self.update()

		if self.online():
			if console:
				self.log_up_message()
			message, message_subject = self.text_up_message()
			next_message = cfg.up_text_interval

		else:
			if console:
				self.log_down_message()
			message, message_subject = self.text_down_message()
			next_message = cfg.up_text_interval

		if text:
			if self.message_timer.int_timer.is_alive():
				self.message_timer.cancel()
			self.yag.send(cfg.sms_gateway, message_subject, message)
			format_phone = '(%s) %s-%s' % tuple(re.findall(r'\d{4}$|\d{3}', cfg.sms_gateway[:10]))
			logging.info(f'Sent text to {format_phone}')
			if next_message > 0:
				self.message_timer = PTimer(next_message, self.send_message)
				logging.debug(f'Next text scheduled in {self.message_timer.remaining() / 60:.1f} mins')

		# clears out temporary data once message is sent
		self.player_summary = {}
		self.pings = []
		self.max_online = 0

	def online(self):
		# my janky way of returning false when the server check fails
		return self.last_status is not False

	def get_avg_ping(self):
		if len(self.pings) == 1:
			return self.pings[0]['ping']
		total = 0
		for i in range(len(self.pings) - 1):
			total += self.pings[i]['ping'] * (self.pings[i + 1]['time'] - self.pings[i]['time'])
		return total / (self.pings[-1]['time'] - self.pings[0]['time'])

	def get_player_time(self, player):
		if len(self.player_summary[player]) == 1:
			return 0
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
		logging.info(f'[SERVER ONLINE] Uptime: {self.get_uptime() / 3600:.1f} hrs')
		logging.info(f'[SERVER ONLINE] Avg ping: {self.get_avg_ping():.0f} ms')
		logging.info(f'[SERVER ONLINE] Max ping: {self.get_max_ping():.0f} ms')
		logging.info(f'[SERVER ONLINE] Last ping: {self.pings[-1]["ping"]:.0f} ms')
		logging.info(f'[SERVER ONLINE] Max players: {self.max_online}/{self.max_players}')

		if cfg.try_player_log:
			logging.info('[SERVER ONLINE] Players online:')
			if len(self.player_summary.keys()) == 0:
				logging.info('[SERVER ONLINE] None')
			else:
				for player in self.player_summary.keys():
					logging.info(f'[SERVER ONLINE] {player}: {self.get_player_time(player) / 3600:.1f} hrs')

	def log_down_message(self):
		logging.warning(f'[SERVER OFFLINE] Downtime: {self.get_downtime() / 3600:.1f} hrs')

	def text_up_message(self):
		message_subject = f'Status {cfg.server_address}: Online'
		message = f'[{datetime.now().strftime("%I:%M:%S %p")}]\r'
		message += f'Uptime: {int((self.get_uptime() - (self.get_uptime() % 86400)) / 86400)} days '
		message += f'{(self.get_uptime() % 86400) / 3600:.1f} hrs\r'
		message += f'Avg ping: {self.get_avg_ping():.0f} ms\r'
		message += f'Max ping: {self.get_max_ping():.0f} ms\r'
		message += f'Max players: {self.max_online}/{self.max_players}'

		if cfg.try_player_log:
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

	def stop(self):
		self.message_timer.delete()
		self.update_timer.delete()
