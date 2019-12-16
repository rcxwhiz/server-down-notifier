import re
import yagmail

from server_checker.checker_setup import *


class Checker:

	def __init__(self, email_password_in):
		logging.debug('Initializing checker')

		self.yag = yagmail.SMTP(cfg.email_address, email_password_in)
		self.server = MServer(cfg.server_address, cfg.server_port)
		self.text_timer = None
		self.send_text_yagmail()

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
			'set down text interval',
			'stop'
		]

		if command not in commands:
			logging.error(f'Command not found in {commands}')

		elif command == commands[0]:
			if self.server_up:
				if len(self.pings) == 0:
					self.check_server_up()
				self.log_up_message()
			else:
				self.log_down_message()

		elif command == commands[1]:
			if self.server_up:
				self.send_up_message()
			else:
				self.send_down_message()

		elif command == commands[2]:
			self.check_server_up(logg=False)

		elif command == commands[3]:
			if self.server_up:
				number = cfg.up_text_interval - (time.time() - self.when_text_sent)
			else:
				number = cfg.down_text_interval - (time.time() - self.when_text_sent)
			logging.info(f'Next text message in {number / 60:.1f} mins')

		elif command == commands[4]:
			# number = cfg.check_interval - (time.time() - self.when_timer_set)
			logging.info(f'Next contact with server in {self.checker_timer.remaining() / 60:.1f} mins')

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
			cfg.check_interval = float(input('New server contact interval (mins): ')) * 60

			self.checker_timer.new_time(cfg.check_interval)

			# self.checker_timer.cancel()
			#
			# to_wait = cfg.check_interval
			# if (cfg.up_text_interval - self.time_since_message) < cfg.check_interval:
			# 	to_wait = cfg.up_text_interval - self.time_since_message
			# if self.server_up:
			# 	self.server_uptime += to_wait
			# 	self.checker_timer = threading.Timer(to_wait, self.up_loop)
			# else:
			# 	self.server_downtime += to_wait
			# 	self.checker_timer = threading.Timer(to_wait, self.down_loop)
			# self.time_since_message += to_wait
			# self.when_timer_set = time.time()
			# self.checker_timer.start()

			self.command('next status')

		elif command == commands[11]:
			cfg.up_text_interval = float(input('New up text interval (mins): ')) * 60
			if self.server_up:
				self.time_since_message = 0
			self.command('next text')

		elif command == commands[12]:
			cfg.down_text_interval = float(input('New down text interval (mins): ')) * 60
			if not self.server_up:
				self.time_since_message = 0
			self.command('next text')

		elif command == commands[13]:
			self.checker_timer.cancel()

	def send_text_yagmail(self):
		content, subject_in = self.server.send_message()
		self.yag.send(cfg.sms_gateway, subject_in, content)
		format_phone = '(%s) %s-%s' % tuple(re.findall(r'\d{4}$|\d{3}', cfg.sms_gateway[:10]))
		logging.info(f'Sent text to {format_phone}')

		if self.server.online():
			self.text_timer = PTimer(cfg.up_text_interval, self.text_timer)
		else:
			self.text_timer = PTimer(cfg.down_text_interval)
