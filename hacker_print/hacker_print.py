import time
import sys
import random
import string


def hacker_print(message, rand=True, delay=0.01, start_char=' '):
	guess = list(start_char * len(message))

	for i, c in enumerate(message):
		sys.stdout.write(f"\r{''.join(guess)}")
		if rand:
			cnt = 0
			while True:
				guess[i] = random.choice(string.ascii_letters + string.punctuation + ' ')
				sys.stdout.write(f"\r{''.join(guess)}")
				time.sleep(delay)
				cnt += 1
				if cnt == 30:
					guess[i] = c
					sys.stdout.write(f"\r{''.join(guess)}")
				if guess[i] == c:
					break
		else:
			sys.stdout.write(f"\r{''.join(guess)}")
			guess[i] = chr(31)
			while True:
				guess[i] = chr(ord(guess[i]) + 1)
				sys.stdout.write(f"\r{''.join(guess)}")
				time.sleep(delay)
				if guess[i] == c:
					break
