import logging
import smtplib
import sys
import yagmail

from server_checker.checker_setup import *
from server_checker.m_server import MServer


class Checker:

	def __init__(self, email_password_in):
		logging.debug('Initializing checker')

		yag_server = yagmail.SMTP(cfg.email_address, email_password_in)
		try:
			yag_server.send(cfg.sms_gateway, 'Python MCStatus', f'Start monitoring {cfg.server_address}')
		except smtplib.SMTPAuthenticationError:
			logging.critical('Email credentials not accepted. Check email address/password.')
			sys.exit(0)
		self.server = MServer(cfg.server_address, cfg.server_port, yag_server)

	def command(self, command):
		commands = [
			'print status',
			'send text',
			'update',
			'next text',
			'next update',
			'debug level debug',
			'debug level info',
			'debug level warning',
			'debug level error',
			'debug level critical',
			'set update interval',
			'set up text interval',
			'set down text interval',
			'stop'
		]

		if command not in commands:
			logging.error(f'Command not found in {commands}')

		elif command == commands[0]:
			self.server.send_message(text=False)

		elif command == commands[1]:
			self.server.send_message(console=False)

		elif command == commands[2]:
			self.server.update()

		elif command == commands[3]:
			logging.info(f'Next text message in {self.server.message_timer.remaining() / 60:.1f} mins')

		elif command == commands[4]:
			logging.info(f'Next contact with server in {self.server.update_timer.remaining() / 60:.1f} mins')

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

			self.server.update_timer.new_time(cfg.check_interval)
			self.command('next status')

		elif command == commands[11]:
			cfg.up_text_interval = float(input('New up text interval (mins): ')) * 60
			if self.server.online():
				self.server.message_timer.new_time(cfg.up_text_interval)
			self.command('next text')

		elif command == commands[12]:
			cfg.down_text_interval = float(input('New down text interval (mins): ')) * 60
			if not self.server.online():
				self.server.message_timer.new_time(cfg.down_text_interval)
			self.command('next text')

		elif command == commands[13]:
			self.server.stop()
