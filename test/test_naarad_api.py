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
  naarad_obj.signal_start()
  time.sleep(5)
  diff_time = naarad_obj.signal_stop('/tmp/config', '/tmp')
  assert diff_time == 5000.0
  naarad_obj.signal_start()
  time.sleep(3)
  diff_time = naarad_obj.signal_stop('/tmp/config', '/tmp')
  assert diff_time == 3000.0


