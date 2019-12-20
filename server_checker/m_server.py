import logging
import time
import socket
import sys

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
		self.server_info = {}
		self.server_stats = {}

		self.update_timer = None
		self.message_timer = None
		self.uptime = []
		self.downtime = []

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
			self.last_status = None
			return False
		except socket.gaierror:
			# this is usually what happens when the address is incorrect so the program exits
			logging.critical('Unable to resolve server address from config')
			input()
			sys.exit(0)
		except OSError:
			# this usualyl happens when the server is still loading or overloaded
			self.uptime = []
			self.downtime.append(time.time())
			logging.warning('The server responded but not with info')
			time.sleep(2)
			self.last_status = None
			# this retries the check a few times
			if retries < 3:
				return self.update(retries=retries + 1)
			else:
				return None

		self.uptime.append(time.time())
		self.downtime = []
		logging.debug('Contact with server successful')

		# tests if this is the first successful contact with the server
		if not self.server_info:
			self.server_info['address'] = f'{cfg.server_address}:{cfg.server_port}'
			if type(self.last_status.description) is str:
				self.server_info['description'] = self.last_status.description
			else:
				self.server_info['description'] = self.last_status.description['text']
			self.server_info['max players'] = self.last_status.players.max
			self.server_info['version'] = self.last_status.version.name
			if len(self.last_status.raw['modinfo']['modList']) > 0:
				self.server_info['version'] += f" - {len(self.last_status.raw['modinfo']['modList'])} mods"
			else:
				self.server_info['version'] += ' - Vanilla'
			# this tests to see if query is enabled and disables player logging if needed
			try:
				query = self.int_server.query()
				self.server_info['query allowed'] = True
				self.server_info['gametype'] = query.raw['gametype']
			except socket.timeout:
				self.server_info['query allowed'] = False
				if cfg.include_player_log:
					logging.error('Query is not allowed on this server so individual players will not be logged!')
					cfg.try_player_log = False
			# after the server info is initially populated it is printed
			self.print_server_info()

		# if this update is supposed to be logged info is recorded
		if log:
			if 'pings' not in self.server_stats.keys():
				self.server_stats['pings'] = [{'ping': self.last_status.latency, 'time': time.time()}]
			else:
				self.server_stats['pings'].append({'ping': self.last_status.latency, 'time': time.time()})

			if 'max online' not in self.server_stats.keys():
				self.server_stats['max online'] = self.last_status.players.online
			else:
				self.server_stats['max online'] = max(self.server_stats['max online'], self.last_status.players.online)

			if cfg.include_player_log:
				query = self.int_server.query()
				if len(query.players.names) > 0:
					current_players = []
					for player_ob in query.players.names:
						current_players.append(player_ob.name)

					if 'player summary' not in self.server_stats.keys():
						self.server_stats['player summary'] = {}

					for player in self.server_stats['player summary'].keys():
						self.server_stats['player summary'][player].append({'online': player in current_players, 'time': time.time()})

					for player in current_players:
						if player not in self.server_stats['player summary'].keys():
							self.server_stats['player summary'][player] = [{'online': True, 'time': time.time()}]

		return True

	def print_server_info(self):
		if not self.server_info:
			logging.warning('No server info has been gathered yet')
		else:
			for data in self.server_info.keys():
				logging.info(f'[SERVER INFO] {data.capitalize()}: {self.server_info[data]}')

	def send_message(self, console=True, text=True, update_before=True):
		if update_before:
			self.update()

		# creates message and subject using config
		message = []
		if self.online():
			log_title = '[SERVER ONLINE]'
			subject = f'Status {cfg.server_address}: Online'
			if cfg.include_uptime:
				uptime_msg = f'Uptime: {int((self.get_uptime() - (self.get_uptime() % 86400)) / 86400)} days '
				uptime_msg += f'{(self.get_uptime() % 86400) / 3600:.1f} hrs'
				message.append(uptime_msg)
			if cfg.include_avg_ping:
				message.append(f'Avg ping: {self.get_avg_ping():.0f} ms')
			if cfg.include_max_ping:
				message.append(f'Max ping: {self.get_max_ping():.0f} ms')
			if cfg.include_last_ping:
				message.append(f'Last ping: {self.server_stats["pings"][-1]["ping"]}')
			if cfg.include_max_players:
				message.append(f'Max players: {self.server_stats["max players"]}/{self.server_info["max players"]}')
			if cfg.include_player_log:
				message.append('Players online:')
				if not self.server_stats['player summary']:
					message.append('None')
				else:
					for player in self.server_stats['player summary'].keys():
						message.append(f'\r{player}: {self.get_player_time(player) / 3600:.1f} hrs')
		else:
			log_title = '[SERVER OFFLINE]'
			subject = f'{cfg.server_address} Status: Offline!'
			if cfg.include_downtime:
				downtime_msg = f'Downtime: {(self.get_downtime() - self.get_downtime() % 86400) / 3600:.1f} days '
				downtime_msg += f'{self.get_downtime() / 3600:.1f} hrs'
				message.append(downtime_msg)

		# sends message to log
		if console:
			for line in message:
				logging.info(f'{log_title} {line}')

		# sends message through sms gateway
		if text:
			if cfg.include_timestamp:
				message.insert(0, f'[{datetime.now().strftime("%I:%M:%S %p")}]')
			self.yag.send(cfg.sms_gateway, subject, '\r'.join(message))
			logging.info(f'Sent text to {cfg.phone_str}')

		# clears out temporary data once message is sent
		self.server_stats = {}

		# sets next timer
		if self.message_timer is not None and self.message_timer.int_timer.is_alive():
			self.message_timer.cancel()
		if self.online() and cfg.up_text_interval > 0:
			self.message_timer = PTimer(cfg.up_text_interval, self.send_message)
		if not self.online() and cfg.down_text_interval > 0:
			self.message_timer = PTimer(cfg.down_text_interval, self.send_message)

	def online(self):
		return self.last_status is not None

	def get_avg_ping(self):
		if len(self.server_stats['pings']) == 1:
			return self.server_stats['pings'][0]['ping']
		total = 0
		for i in range(len(self.server_stats['pings']) - 1):
			total += self.server_stats['pings'][i]['ping'] * (self.server_stats['pings'][i + 1]['time'] - self.server_stats['pings'][i]['time'])
		return total / (self.server_stats['pings'][-1]['time'] - self.server_stats['pings'][0]['time'])

	def get_player_time(self, player):
		if len(self.server_stats['player summary'][player]) == 1:
			return 0
		total = 0
		for i in range(len(self.server_stats['player summary'][player]) - 1):
			if self.server_stats['player summary'][player][i]['online']:
				total += self.server_stats['player summary'][player][i + 1]['time'] - self.server_stats['player summary'][player][i]['time']
		return total / (self.server_stats['player summary'][player][-1]['time'] - self.server_stats['player summary'][player][0]['time'])

	def get_max_ping(self):
		ping_vals = []
		for point in self.server_stats['pings']:
			ping_vals.append(point['ping'])
		return max(ping_vals)

	def get_uptime(self):
		return self.uptime[-1] - self.uptime[0]

	def get_downtime(self):
		return self.downtime[-1] - self.downtime[0]

	def stop(self):
		self.message_timer.delete()
		self.update_timer.delete()
