import bs4
import coloredlogs
import logging
import requests
import time

import config_setter as cfg

coloredlogs.install(level=cfg.logging_level, ftm='%(asctime)s %(message)s')


class Checker:

	def __init__(self):
		logging.info('Initializing checker')
		cfg.up_text_interval *= 60
		cfg.down_text_interval *= 60
		cfg.check_interval *= 60
		if self.check_server_up():
			self.up_loop()
		else:
			self.down_loop()

	def check_server_up(self):
		for i in range(cfg.fails_required):
			res = requests.get(cfg.status_url)
			res.raise_for_status()
			status_page = bs4.BeautifulSoup(res.text, 'html.parser')
			if len(status_page.find_all('div', {'class': 'table-responsive'})) > 0:
				logging.debug(f'Attempt {i + 1} to access server succsessful')
				return True
			else:
				logging.debug(f'Attempt {i + 1} to access server unsuccessful')
		return False

	def up_loop(self):
		player_list = []
		time_since_message = cfg.up_text_interval + 1
		uptime = 0

		logging.info('Entering up_loop')
		while True:
			if not self.check_server_up():
				self.down_loop()
				return None

			if (not cfg.up_text_interval == 0) and (time_since_message > cfg.up_text_interval):
				self.send_up_message(uptime, player_list)
				time_since_message = 0
				logging.debug(f'Waiting {cfg.up_text_interval / 60:.1f} mins to send up message again')

			# TODO use some webscraping to append to player_list

			logging.debug(f'Waiting {cfg.check_interval / 60:.1f} mins to check server again')
			time.sleep(cfg.check_interval)
			time_since_message += cfg.check_interval

	def down_loop(self):
		time_since_message = cfg.down_text_interval + 1
		downtime = 0

		logging.info('Entering down loop')
		while True:
			if self.check_server_up():
				self.up_loop()
				return None

			if time_since_message > cfg.down_text_interval:
				self.send_down_message(downtime)
				time_since_message = 0
				logging.debug(f'Waiting {cfg.down_text_interval / 60:.1f} mins to send down message again')

			logging.debug(f'Waiting {cfg.check_interval / 60:.1f} mins to check server again')
			time.sleep(cfg.check_interval)
			if cfg.down_text_interval > 0:
				time_since_message += cfg.check_interval

	def send_up_message(self, uptime, player_list):
		logging.info("The server is up???")
		# TODO make this send as a text

	def send_down_message(self, downtime):
		logging.warning("The server is down???")
		# TODO make this send as a text
