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
  naarad_obj.signal_start('/tmp/config')
  time.sleep(5)
  diff_time = naarad_obj.signal_stop()
  assert int(diff_time/1000) == 5
  naarad_obj.signal_start('/tmp/config')
  time.sleep(3)
  diff_time = naarad_obj.signal_stop()
  assert int(diff_time/1000) == 3


