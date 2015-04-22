# coding=utf-8
"""
Copyright 2013 LinkedIn Corp. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import ConfigParser
import os
import sys
import time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')))
from naarad import Naarad
import naarad.naarad_constants as CONSTANTS
naarad_obj = None


def setup_module():
  global naarad_obj
  naarad_obj = Naarad()


def test_naarad_apis():
  """
  :return: None
  """
  examples_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'examples')
  config_file = os.path.join(os.path.join(examples_directory, 'conf'), 'config-gc')
  config_object = ConfigParser.ConfigParser()
  config_object.optionxform = str
  config_object.read(config_file)
  input_directory = os.path.join(examples_directory, 'logs')
  output_directory = 'test_api_temp'
  diff_output_directory = 'test_api_temp/diff_location'
  report1_location = 'test_api_temp/0'
  report2_location = 'test_api_temp/1'
  global naarad_obj
  test_id_1 = naarad_obj.signal_start(config_file)
  time.sleep(60)
  naarad_obj.signal_stop(test_id_1)
  test_id_2 = naarad_obj.signal_start(config_object)
  time.sleep(60)
  naarad_obj.signal_stop(test_id_2)
  if naarad_obj.analyze(input_directory, output_directory) != CONSTANTS.OK:
    print naarad_obj.get_failed_analyses()
  naarad_obj.get_sla_data(test_id_1)
  naarad_obj.get_stats_data(test_id_1)
  naarad_obj.get_sla_data(test_id_2)
  naarad_obj.get_stats_data(test_id_2)
  if naarad_obj.diff(test_id_1, test_id_2, None) != CONSTANTS.OK:
    print 'Error encountered during diff'
  if naarad_obj.diff_reports_by_location(report1_location, report2_location, diff_output_directory, None):
    print 'Error encountered during diff'
  print 'Please inspect the generated reports manually'
