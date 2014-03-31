# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License");?you may not use this file except in compliance with the License.?You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software?distributed under the License is distributed on an "AS IS" BASIS,?WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""

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


