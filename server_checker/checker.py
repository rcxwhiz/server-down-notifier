from server_checker.checker_setup import *


class Checker:

	def __init__(self, email_password_in):
		logging.debug('Initializing checker')

		self.email_pswd = email_password_in
		self.player_summary = {}
		self.pings = []
		self.server = MinecraftServer(cfg.server_address, port=cfg.server_port)
		self.status = 0
		self.server_uptime = 0
		self.server_downtime = 0
		cfg.up_text_interval *= 60
		cfg.down_text_interval *= 60
		cfg.check_interval *= 60
		self.time_since_message = cfg.up_text_interval
		self.checker_timer = threading.Timer(1, self.up_loop)
		self.when_timer_set = 0
		self.server_up = True
		self.up_loop()

	def command(self, command):
		commands = [
			'print status',
			'text status',
			'get status',
			'next text',
			'next status',
			'debug level debug',
			'debug level info',
			'debug level warning',
			'debug level error',
			'debug level critical',
			'set status interval',
			'set up text interval',
			'set down text interval'
		]
		if command not in commands:
			logging.error(f'Command not found in {commands}')
		elif command == commands[0]:
			if self.server_up:
				self.log_up_message()
			else:
				self.log_down_message()
		elif command == commands[1]:
			if self.server_up:
				self.send_up_message()
			else:
				self.send_down_message()
		elif command == commands[2]:
			self.check_server_up()
		elif command == commands[3]:
			if self.server_up:
				number = cfg.up_text_interval - self.time_since_message - (time.time() - self.when_timer_set)
			else:
				number = cfg.down_text_interval - self.time_since_message - (time.time() - self.when_timer_set)
			logging.info(f'Next text message in {number / 60:.1f} mins')
		elif command == commands[4]:
			number = cfg.check_interval - (time.time() - self.when_timer_set)
			logging.info(f'Next contact with server in {number / 60:.1f} mins')
		elif command == commands[5]:
			logging.getLogger().setLevel(logging.DEBUG)
		elif command == commands[6]:
			logging.getLogger().setLevel(logging.INFO)
		elif command == commands[7]:
			logging.getLogger().setLevel(logging.WARNING)
		elif command == commands[8]:
			logging.getLogger().setLevel(logging.ERROR)
		elif command == commands[9]:
			logging.getLogger().setLevel(logging.CRITICAL)
		elif command == commands[10]:
			# TODO update timers here
			new_interval = float(input('New server contact interval (mins): '))
			cfg.check_interval = new_interval * 60
			logging.debug(f'New check interval: {cfg.check_interval / 60:.1f}')
		elif command == commands[11]:
			new_interval = float(input('New up text interval (mins): '))
			cfg.up_text_interval = new_interval * 60
			logging.debug(f'New up text interval: {cfg.up_text_interval / 60:.1f}')
		elif command == commands[12]:
			new_interval = float(input('New down text interval (mins): '))
			cfg.down_text_interval = new_interval * 60
			logging.debug(f'New down text interval: {cfg.down_text_interval / 60:.1f}')

	def send_text_yagmail(self, content, subject_in=''):
		yag = yagmail.SMTP(cfg.email_address, self.email_pswd)
		yag.send(cfg.sms_gateway, subject_in, content)
		format_phone = '(%s) %s-%s' % tuple(re.findall(r'\d{4}$|\d{3}', cfg.sms_gateway[:10]))
		logging.info(f'Sent text to {format_phone}')

	def check_server_up(self):
		logging.info('Contacting server')
		try:
			self.status = self.server.status(cfg.fails_required)
		except socket.timeout:
			logging.debug('Attempt to contact server timed out')
			self.server_up = False
			return False
		except socket.gaierror:
			logging.critical('Unable to resolve server address from config')
			self.server_up = False
			return False
		except OSError:
			logging.warning('The server responded but not with info')
			self.server_up = False
			return False
		logging.debug('Contact with server successful')
		self.server_up = True

		self.pings.append(self.status.latency)
		if self.status.players.sample is not None:
			current_players = []
			for player_ob in self.status.players.sample:
				current_players.append(player_ob.name)

			for player in current_players:
				if player not in self.player_summary.keys():
					self.player_summary[player] = cfg.check_interval / 2
				else:
					self.player_summary[player] += cfg.check_interval
		return True

	def up_loop(self):
		if not self.check_server_up():
			self.checker_timer.cancel()
			self.player_summary = {}
			self.pings = []
			self.server_uptime = 0
			self.time_since_message = cfg.down_text_interval

			logging.debug('Entering down loop')
			self.down_loop()
			return None

		if (not cfg.up_text_interval == 0) and (self.time_since_message >= cfg.up_text_interval):
			self.log_up_message()
			self.send_up_message()
			self.time_since_message = 0
			self.player_summary = {}
			self.pings = []
			logging.debug(f'Waiting {cfg.up_text_interval / 60:.1f} mins to send up message again')

		to_wait = cfg.check_interval
		if (cfg.up_text_interval - self.time_since_message) < cfg.check_interval:
			to_wait = cfg.up_text_interval - self.time_since_message
		logging.debug(f'Waiting {to_wait / 60:.1f} mins to check server again')
		self.time_since_message += to_wait
		self.server_uptime += to_wait
		self.when_timer_set = time.time()
		self.checker_timer = threading.Timer(to_wait, self.up_loop)
		self.checker_timer.start()

	def down_loop(self):
		if self.time_since_message >= cfg.down_text_interval:
			self.send_down_message()
			self.time_since_message = 0
			logging.debug(f'Waiting {cfg.down_text_interval / 60:.1f} mins to send down message again')

		to_wait = cfg.check_interval
		if (cfg.down_text_interval - self.time_since_message) < cfg.check_interval:
			to_wait = cfg.down_text_interval - self.time_since_message
		logging.debug(f'Waiting {to_wait / 60:.1f} mins to check server again')
		if cfg.down_text_interval > 0:
			self.time_since_message += to_wait
		self.server_downtime += to_wait
		self.when_timer_set = time.time()
		self.checker_timer = threading.Timer(to_wait, self.down_loop)
		self.checker_timer.start()

		if self.check_server_up():
			self.checker_timer.cancel()
			self.time_since_message = cfg.up_text_interval
			self.server_downtime = 0

			logging.debug('Entering up_loop')
			self.up_loop()
			return None

	def log_up_message(self):
		logging.info(f'Server {cfg.server_address} online - Uptime: {self.server_uptime / 3600:.1f} hrs')
		logging.info(f'Avg ping: {sum(self.pings) / len(self.pings):.0f} ms')
		logging.info(f'Max ping: {max(self.pings):.0f} ms')
		logging.info(f'Last ping: {self.pings[-1]:.0f} ms')
		logging.info('Players online:')
		for player in self.player_summary.keys():
			logging.info(f'{player}: {self.player_summary[player] / 3600:.1f} hrs')

	def send_up_message(self):
		message_subject = f'Server Status {cfg.server_address}: Online'
		message = f'[{datetime.now().strftime("%I:%M:%S %p")}]\r'
		message += f'Uptime: {self.server_uptime / 3600:.1f} hrs\r'
		message += f'Avg ping: {sum(self.pings) / len(self.pings):.0f} ms\r'
		message += f'Max ping: {max(self.pings):.0f} ms\r'
		message += f'Last ping: {self.pings[-1]:.0f} ms\r'
		message += 'Players online:'
		for player in self.player_summary.keys():
			message += f'\r{player}: {self.player_summary[player] / 3600:.1f} hrs'
		self.send_text_yagmail(message, message_subject)

	def log_down_message(self):
		logging.warning(f'Server {cfg.server_address} offline - Downtime: {self.server_downtime / 3600:.1f} hrs')

	def send_down_message(self):
		message_subject = f'Server {cfg.server_address} Status: Offline!'
		message = f'[{datetime.now().strftime("%I:%M:%S %p")}]\r'
		message += f'Downtime: {self.server_downtime / 3600:.1f} hrs'
		self.send_text_yagmail(message, message_subject)
