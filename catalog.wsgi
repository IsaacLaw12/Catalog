#!/usr/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/Catalog/")

from catalog import app as application
application.secret_key = 'grader'

if __name__ == "__main__":
	application.run()
