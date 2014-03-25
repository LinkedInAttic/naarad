# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License");?you may not use this file except in compliance with the License.?You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software?distributed under the License is distributed on an "AS IS" BASIS,?WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
__author__ = 'rmaheshw'

from collections import defaultdict
import logging

import naarad.utils

logger = logging.getLogger('naarad')


class Naarad(object):
  def __init__(self):
    self.ts_start = defaultdict(str)
    self.ts_end = defaultdict(str)
    self.default_test_id = -1

  def signal_start(self, test_id=None):
    if test_id:
      self.ts_start[test_id] = naarad.utils.get_now_in_naarad_format()
      return test_id
    else:
      self.default_test_id += 1
      self.ts_start[self.default_test_id] = naarad.utils.get_now_in_naarad_format()
      return self.default_test_id

  def signal_stop(self, config_file_location, output_dir, input_dir=None, test_id=None):
    if test_id:
      self.ts_end[test_id] = naarad.utils.get_now_in_naarad_format()
      return self.run(config_file_location, self.ts_start[test_id], self.ts_end[test_id], output_dir, input_dir=input_dir)
    else:
      self.ts_end[self.default_test_id] = naarad.utils.get_now_in_naarad_format()
      return self.run(config_file_location, self.ts_start[self.default_test_id], self.ts_end[self.default_test_id], output_dir, input_dir=input_dir)

  def run(self, config_file_location, ts_start, ts_end, output_dir, input_dir=None):
    return naarad.utils.convert_to_unixts(ts_end) - naarad.utils.convert_to_unixts(ts_start)



