import threading
import time
import logging


class PTimer:

	def __init__(self, time_in, function_in, args_in=(), start=True):
		logging.debug('Initializing perfect timer')

		self.int_timer = threading.Timer(time_in, function_in, args=args_in)
		self.interval = time_in
		self.func = function_in
		self.arg = args_in
		self.time_started = None
		if start:
			self.start()

	def start(self):
		self.int_timer.start()
		self.time_started = time.time()

	def cancel(self):
		self.int_timer.cancel()

	def pause(self):
		self.int_timer.cancel()
		self.int_timer = threading.Timer(self.remaining(), self.func, self.arg)

	def remaining(self):
		return self.interval - (time.time() - self.time_started)

	def elapsed(self):
		return time.time() - self.time_started

	def new_time(self, new_time_in, go=True):
		self.int_timer.cancel()
		self.interval = new_time_in
		self.int_timer = threading.Timer(new_time_in, self.func, self.arg)
		if go:
			self.start()

	def delete(self):
		logging.debug('Deleting perfect timer')
		self.cancel()
		del self

	def is_alive(self):
		return self.int_timer.is_alive()
