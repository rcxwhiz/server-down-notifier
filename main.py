import sys
from getpass import getpass
from server_checker import *
print("\nJosh's server down notifier - 2.0")
email_password = getpass(f'Please enter the password for {cfg.email_address}: ')
print('')

logging.info('Starting server down notifier')
checker = Checker(email_password)
del email_password

while True:
	command = input()
	if command == 'stop':
		checker.command(command)
		break
	checker.command(command)

logging.info('Exiting server down notifier')
sys.exit(0)
