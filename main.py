import os
from getpass import getpass
from server_checker import *
email_password = getpass(f'Please enter the password for {cfg.email_address}: ')

logging.info('Starting server down notifier program')

checker = Checker(email_password)

while True:
	command = input()
	checker.command(command)
	if command == 'stop':
		break

logging.warning('Exiting server down notifier')
os._exit(0)
