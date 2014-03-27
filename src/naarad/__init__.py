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


class Analysis(object):
  """
  Class that saves state for analysis to be conducted
  """
  def __init__(self, ts_start, config_file_location, test_id=None):
    self.ts_start = ts_start
    self.ts_end = None
    self.test_id = test_id
    self.config_file_location = config_file_location


class Naarad(object):
  """
  Naarad base class that will let the caller run multiple naarad analysis
  """

  def __init__(self):
    self.default_test_id = -1
    self.analyses = {}

  def signal_start(self, config_file_location, test_id=None):
    """
    Initialize an analysis object and set ts_start for the analysis represented by test_id
    :param test_id: integer that represents the analysis
    :param config_file_location: local or http location of the naarad config used for this analysis
    :return: test_id
    """
    if not test_id:
      self.default_test_id += 1
      test_id = self.default_test_id
    self.analyses[test_id] = Analysis(naarad.utils.get_standardized_timestamp('now', None), config_file_location,
                                      test_id=test_id)
    return test_id

  def signal_stop(self, test_id=None):
    """
    Set ts_end for the analysis represented by test_id
    :param test_id: integer that represents the analysis
    :return: test_id
    """
    if not test_id:
      test_id = self.default_test_id
    self.analyses[test_id].ts_end = naarad.utils.get_standardized_timestamp('now', None)
    return naarad.utils.convert_to_unixts(self.analyses[test_id].ts_end) - \
           naarad.utils.convert_to_unixts(self.analyses[test_id].ts_start)

  def analyze(self):
    """
    Run all the analysis saved in self.analyses, sorted by test_id
    :return:
    """
    for test_id in sorted(self.analyses.keys()):
      self.run(self.analyses[test_id])

  def run(self, test_id):
    """
    Placeholder for actually running the analysis
    :param test_id:
    :return:
    """
    return
