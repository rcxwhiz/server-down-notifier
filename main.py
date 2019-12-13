from getpass import getpass
from server_checker import *
email_password = getpass(f'Please enter the password for {cfg.email_address}: ')

logging.info('Starting server down notifier program')

checker = Checker(email_password)  # checker will automatically initialize itself

logging.error('Exiting server down notifier')
