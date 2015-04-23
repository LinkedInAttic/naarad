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

import sys
import logging
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')))
from naarad.reporting.diff import Diff
from naarad.reporting.diff import NaaradReport

diff_obj = None


def setup_module():
  global diff_obj
  reports_list = []
  report_name = 'diff'
  output_directory = ''
  resource_directory = ''
  resource_path = 'resource_path'
  naarad_reports = [NaaradReport('/tmp', None), NaaradReport('/tmp', None)]
  diff_obj = Diff(naarad_reports, 'diff', '/tmp', '/tmp', 'resources')


def test_collect_cdf_datasources():
  """
  Test whether collect_cdf_datasources works as expected
  :return: None
  """
  global diff_obj
  diff_obj.reports[0].cdf_datasource = ['a.csv', 'b.csv', 'c.csv']
  diff_obj.reports[1].cdf_datasource = ['a.csv', 'b.csv', 'd.csv']
  return_code = diff_obj.collect_cdf_datasources()
  assert return_code is True
  assert diff_obj.reports[0].cdf_datasource == diff_obj.reports[1].cdf_datasource
  assert len(diff_obj.reports[0].cdf_datasource) == 2
  assert diff_obj.reports[0].cdf_datasource[0] == 'a.csv'
  assert diff_obj.reports[0].cdf_datasource[1] == 'b.csv'
  diff_obj.reports[0].cdf_datasource = []
  diff_obj.reports[1].cdf_datasource = ['a.csv', 'b.csv', 'd.csv']
  return_code = diff_obj.collect_cdf_datasources()
  assert return_code is False
