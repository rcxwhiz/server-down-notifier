from datetime import datetime
import logging
import smtplib
import socket
import sys
import yagmail

from server_checker.checker_setup import *
from server_checker.m_server import MServer


class Checker:

    def __init__(self, email_password_in):
        logging.debug('Initializing checker')

        yag_server = yagmail.SMTP(cfg.email_address, email_password_in)
        try:
            message = f'Started monitoring {cfg.server_address}\r[{datetime.now().strftime("%I:%M:%S %p")}]'
            yag_server.send(cfg.sms_gateway, 'Python MCStatus', message)
            logging.info(f'Sent startup text to {cfg.phone_str}')
        except smtplib.SMTPAuthenticationError:
            logging.critical('Email credentials not accepted. Check email address/password.')
            logging.critical('Make sure you have allowed access from unsecure apps to your gmail account.')
            logging.critical('https://support.google.com/accounts/answer/6010255?hl=en')
            input('Press enter to exit...')
            sys.exit(0)
        except socket.gaierror:
            logging.critical('No internet connection!')
            input('Press enter to exit...')
            sys.exit(0)
        self.server = MServer(cfg.server_address, cfg.server_port, yag_server)

    # lots of commands that can interact with the MServer object
    def command(self, command):
        commands = [
            'print status',
            'server info',
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

        elif command == 'print status':
            self.server.send_message(text=False)

        elif command == 'server info':
            self.server.print_server_info()

        elif command == 'send text':
            self.server.send_message(console=False)

        elif command == 'update':
            self.server.update()

        elif command == 'next text':
            logging.info(f'Next text message in {self.server.timers["message timer"].remaining() / 60:.1f} mins')

        elif command == 'next update':
            logging.info(f'Next contact with server in {self.server.timers["update timer"].remaining() / 60:.1f} mins')

        elif command == 'debug level debug':
            logging.getLogger().setLevel(logging.DEBUG)

        elif command == 'debug level info':
            logging.getLogger().setLevel(logging.INFO)

        elif command == 'debug level warning':
            logging.getLogger().setLevel(logging.WARNING)

        elif command == 'debug level error':
            logging.getLogger().setLevel(logging.ERROR)

        elif command == 'debug level critical':
            logging.getLogger().setLevel(logging.CRITICAL)

        elif command == 'set update interval':
            cfg.check_interval = float(input('New server contact interval (mins): ')) * 60

            self.server.timers['update timer'].new_time(cfg.check_interval)
            self.command('next status')

        elif command == 'set up text interval':
            cfg.up_text_interval = float(input('New up text interval (mins): ')) * 60
            if self.server.online():
                self.server.timers['message timer'].new_time(cfg.up_text_interval)
            self.command('next text')

        elif command == 'set down text interval':
            cfg.down_text_interval = float(input('New down text interval (mins): ')) * 60
            if not self.server.online():
                self.server.timers['message timer'].new_time(cfg.down_text_interval)
            self.command('next text')

        elif command == 'stop':
            self.server.stop()
