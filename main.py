import logging
import sys
from getpass import getpass
import server_checker as sc

print(f"\nJosh's server down notifier v{sc.version}")
email_password = getpass(f'Please enter the password for {sc.email_address}: ')
print('')

logging.info('Starting server down notifier')
checker = sc.Checker(email_password)
# delete password from memory
del email_password

while True:
	command = input()
	if command == 'stop':
		checker.command(command)
		break
	checker.command(command)

logging.info('Exiting server down notifier')
input('Press enter to exit...')
sys.exit(0)
