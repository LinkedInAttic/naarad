__author__ = 'rmaheshw'

import time

from naarad import Naarad

naarad_obj = None

def setup_module():
  global naarad_obj
  naarad_obj = Naarad()

def test_naarad_start_stop():
  """
  :return: None
  """
  global naarad_obj
  naarad_obj.start()
  time.sleep(5)
  naarad_obj.stop('/tmp/config', '/tmp')
  naarad_obj.start()
  time.sleep(3)
  naarad_obj.stop('/tmp/config', '/tmp')

