import logging
import sys
from getpass import getpass
import server_checker as sc
from hacker_print import hacker_print

print('')
hacker_print(str(f"Josh's server down notifier v{sc.version}"), delay=0.005)
print('')
email_password = getpass(f'Please enter the password for {sc.email_address}: ')
print('')

logging.info('Starting server down notifier')
checker = sc.Checker(email_password)
del email_password

while True:
	command = input()
	if command == 'stop':
		checker.command(command)
		break
	checker.command(command)

logging.info('Exiting server down notifier')
sys.exit(0)
