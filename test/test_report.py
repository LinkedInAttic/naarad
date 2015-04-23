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
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')))
import naarad.utils
from naarad.metrics.metric import Metric
from naarad.reporting.report import Report
output_directory = ''
resource_directory = ''
input_log_directory = ''
resource_path = 'resources'


def setup_module():
  global output_directory
  global resource_path
  global resource_directory
  global input_log_directory
  output_directory = os.path.join('.', 'tmp_report_test')
  resource_directory = os.path.join(output_directory, resource_path)
  input_log_directory = os.path.join(output_directory, 'logs')
  if not os.path.exists(output_directory):
    os.makedirs(output_directory)
  if not os.path.exists(input_log_directory):
    os.makedirs(input_log_directory)
  if not os.path.exists(resource_directory):
    os.makedirs(resource_directory)
  with open(os.path.join(input_log_directory, 'a.csv'), 'w') as TestFile1:
    TestFile1.write('2014-03-26 00:00:00, 0')
  with open(os.path.join(input_log_directory, 'b.csv'), 'w') as TestFile1:
    TestFile1.write('2014-03-26 00:00:00, 1')


def get_three_metrics(output_directory, resource_path, rules):
  metrics = [Metric('MetricOne', 'TestOne.csv', 'HostnameOne', output_directory, resource_path, 'MetricOne', None, None, rules, None, None),
             Metric('MetricTwo', 'TestTwo.csv', 'HostnameOne', output_directory, resource_path, 'MetricTwo', None, None, rules, None, None),
             Metric('MetricThree', 'TestThree.csv', 'HostnameOne', output_directory, resource_path, 'MetricThree', None, None, rules, None, None)]
  return metrics


def get_two_metrics(output_directory, resource_path, rules):
  metrics = [Metric('MetricOne', 'TestOne.csv', 'HostnameOne', output_directory, resource_path, 'MetricOne', None, None, rules, None, None),
             Metric('MetricTwo', 'TestTwo.csv', 'HostnameOne', output_directory, resource_path, 'MetricTwo', None, None, rules, None, None)]
  return metrics


def test_metrics_without_summary_with_error():
  """
  Tests to verify that metric reports are not generated if the metrics are in error. Also no summary report should be created.
  """
  global output_directory
  global resource_path
  rules = {}
  metrics = get_three_metrics(output_directory, resource_path, rules)
  aggregate_metrics = []
  correlated_plots = []
  rpt = Report(None, output_directory, resource_directory, resource_path, metrics + aggregate_metrics, correlated_plots=correlated_plots)
  rpt.generate()
  assert not naarad.utils.is_valid_file(os.path.join(output_directory, 'MetricOne_report.html'))
  assert not naarad.utils.is_valid_file(os.path.join(output_directory, 'MetricTwo_report.html'))
  assert not naarad.utils.is_valid_file(os.path.join(output_directory, 'MetricThree_report.html'))
  assert naarad.utils.is_valid_file(os.path.join(output_directory, 'report.html'))
  assert not naarad.utils.is_valid_file(os.path.join(output_directory, 'summary_report.html'))
  os.system('rm -rf tmp_report_test/*.*')
  os.system('rm -rf tmp_report_test/resources/*.*')


def test_metrics_without_summary_without_error():
  """
  Tests to verify that metric reports are generated if the metrics are not in error. Also no summary report should be created.
  """
  global output_directory
  global input_log_directory
  global resource_path
  rules = {}
  metrics = get_three_metrics(output_directory, resource_path, rules)
  for metric in metrics:
    files_list = [os.path.join(input_log_directory, 'a.csv'), os.path.join(input_log_directory, 'b.csv')]
    metric.csv_files = files_list
    metric.stats_files = files_list
    metric.timeseries_csv_list = files_list
    metric.percentiles_files = files_list

  aggregate_metrics = []
  correlated_plots = []
  rpt = Report(None, output_directory, resource_directory, resource_path, metrics + aggregate_metrics, correlated_plots=correlated_plots)
  rpt.generate()
  assert naarad.utils.is_valid_file(os.path.join(output_directory, 'MetricOne_report.html'))
  assert naarad.utils.is_valid_file(os.path.join(output_directory, 'MetricTwo_report.html'))
  assert naarad.utils.is_valid_file(os.path.join(output_directory, 'MetricThree_report.html'))
  assert naarad.utils.is_valid_file(os.path.join(output_directory, 'report.html'))
  assert not naarad.utils.is_valid_file(os.path.join(output_directory, 'summary_report.html'))
  os.system('rm -rf tmp_report_test/*.*')
  os.system('rm -rf tmp_report_test/resources/*.*')


def test_metrics_with_summary_without_error():
  """
  Tests to verify that metric reports are generated if the metrics are not in error. Also a summary report should be created.
  """
  global output_directory
  global input_log_directory
  global resource_path
  rules = {}
  metrics = get_three_metrics(output_directory, resource_path, rules)
  for metric in metrics:
    files_list = [os.path.join(input_log_directory, 'a.csv'), os.path.join(input_log_directory, 'b.csv')]
    metric.csv_files = files_list
    metric.stats_files = files_list
    metric.timeseries_csv_list = files_list
    metric.important_stats_files = files_list
    metric.percentiles_files = files_list

  aggregate_metrics = []
  correlated_plots = []
  rpt = Report(None, output_directory, resource_directory, resource_path, metrics + aggregate_metrics, correlated_plots=correlated_plots)
  rpt.generate()
  assert naarad.utils.is_valid_file(os.path.join(output_directory, 'MetricOne_report.html'))
  assert naarad.utils.is_valid_file(os.path.join(output_directory, 'MetricTwo_report.html'))
  assert naarad.utils.is_valid_file(os.path.join(output_directory, 'MetricThree_report.html'))
  assert naarad.utils.is_valid_file(os.path.join(output_directory, 'report.html'))
  assert naarad.utils.is_valid_file(os.path.join(output_directory, 'summary_report.html'))
  os.system('rm -rf tmp_report_test/*.*')
  os.system('rm -rf tmp_report_test/resources/*.*')


def test_metrics_with_summary_with_partial_error():
  """
  Tests to verify that metric reports are generated for OK metrics if there are some metrics that are in error. Also a summary report should be created.
  """
  global output_directory
  global input_log_directory
  global resource_path
  rules = {}
  metrics = get_two_metrics(output_directory, resource_path, rules)
  files_list = [os.path.join(input_log_directory, 'a.csv'), os.path.join(input_log_directory, 'b.csv')]
  for metric in metrics:
    metric.csv_files = files_list
    metric.stats_files = files_list
    metric.timeseries_csv_list = files_list
    metric.important_stats_files = files_list
    metric.percentiles_files = files_list

  metrics.append(Metric('MetricThree', 'TestThree.csv', 'HostnameOne', output_directory, resource_path, 'MetricThree', None, None, rules, None, None))

  aggregate_metrics = []
  correlated_plots = []
  rpt = Report(None, output_directory, resource_directory, resource_path, metrics + aggregate_metrics, correlated_plots=correlated_plots)
  rpt.generate()
  assert naarad.utils.is_valid_file(os.path.join(output_directory, 'MetricOne_report.html'))
  assert naarad.utils.is_valid_file(os.path.join(output_directory, 'MetricTwo_report.html'))
  assert not naarad.utils.is_valid_file(os.path.join(output_directory, 'MetricThree_report.html'))
  assert naarad.utils.is_valid_file(os.path.join(output_directory, 'report.html'))
  assert naarad.utils.is_valid_file(os.path.join(output_directory, 'summary_report.html'))
  os.system('rm -rf tmp_report_test/*.*')
  os.system('rm -rf tmp_report_test/resources/*.*')


def test_metrics_without_summary_with_partial_error():
  """
  Tests to verify that metric reports are generated for OK metrics if there are some metrics that are in error. Also no summary report should be created.
  """
  global output_directory
  global input_log_directory
  global resource_path
  rules = {}
  metrics = get_two_metrics(output_directory, resource_path, rules)
  files_list = [os.path.join(input_log_directory, 'a.csv'), os.path.join(input_log_directory, 'b.csv')]
  for metric in metrics:
    metric.csv_files = files_list
    metric.stats_files = files_list
    metric.timeseries_csv_list = files_list
    metric.percentiles_files = files_list

  metrics.append(Metric('MetricThree', 'TestThree.csv', 'HostnameOne', output_directory, resource_path, 'MetricThree', None, None, rules, None, None))

  aggregate_metrics = []
  correlated_plots = []
  rpt = Report(None, output_directory, resource_directory, resource_path, metrics + aggregate_metrics, correlated_plots=correlated_plots)
  rpt.generate()
  assert naarad.utils.is_valid_file(os.path.join(output_directory, 'MetricOne_report.html'))
  assert naarad.utils.is_valid_file(os.path.join(output_directory, 'MetricTwo_report.html'))
  assert not naarad.utils.is_valid_file(os.path.join(output_directory, 'MetricThree_report.html'))
  assert naarad.utils.is_valid_file(os.path.join(output_directory, 'report.html'))
  assert not naarad.utils.is_valid_file(os.path.join(output_directory, 'summary_report.html'))
  os.system('rm -rf tmp_report_test/*.*')
  os.system('rm -rf tmp_report_test/resources/*.*')


def tearDown():
  os.system('rm -rf tmp_report_test')
