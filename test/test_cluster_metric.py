# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
import os
import nose
import sys
import uuid
import shutil
import time
import sys

# add the path of ~/naarad/src;   the testing py is under ~/naarad/test
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')))
import naarad.utils
from naarad.metrics.sar_metric import SARMetric
from naarad.metrics.cluster_metric import ClusterMetric

#the temporary directory for testing, will remove it after done.
tmp_dir = ''

def setup():
  create_tmp_dir()

def teardown():
  delete_tmp_dir()

def create_tmp_dir():
  '''create a unique tmp dir to hold the downloaded local files'''
  ''' if the tmp dir grenerated already exists, then simply return'''
  ''' the user simply try again to generate another unique tmp dir'''
  global tmp_dir
  tmp_dir = os.path.join('./','tmp' + '.' +str(uuid.uuid4()))   #./tmp.'randomstring'
  if not os.path.exists(tmp_dir):
    os.makedirs(tmp_dir)
  else:
    print "the path of %s already exists, please try again." % tmp_dir
    return

def delete_tmp_dir():
  '''delete the tmp directory'''
  global tmp_dir
  shutil.rmtree(tmp_dir)

def test_clustermetric():
  #construct 2 SARMetric
  metric1 = SARMetric('SAR-cpuusage-host1', 'sar.cpuusage.out', 'host1', '.', 'logs', 'SAR-cpuusage-host1', None, None, {}, None, None);
  metric1.csv_column_map['logs/SAR-cpuusage-host1.all.percent-sys.csv'] = 'all.%sys'
  metric1.column_csv_map['all.%sys'] = 'logs/SAR-cpuusage-host1.all.percent-sys.csv'

  metric2 = SARMetric('SAR-cpuusage-host2', 'sar.cpuusage.out', 'host2', '.', 'logs', 'SAR-cpuusage-host2', None, None, {}, None, None);
  metric2.csv_column_map['logs/SAR-cpuusage-host2.all.percent-sys.csv'] = 'all.%sys'
  metric2.column_csv_map['all.%sys'] = 'logs/SAR-cpuusage-host2.all.percent-sys.csv'

  #construct a ClusterMetric
  aggregate_metrics = 'SAR-cpuusage.all.percent-sys:raw,avg,sum,count'
  section = 'CLUSTER-cpuusage-1'
  label = 'CLUSTER-cpuusage-1'
  resource_path = 'resources'
  rule_strings = {}
  output_directory = tmp_dir
  aggregate_hosts = 'host1 host2'
  other_options = {}
  ts_start = None
  ts_end = None
  metrics = [metric1, metric2]

  cur_metric = ClusterMetric(section, aggregate_hosts, aggregate_metrics, metrics, output_directory, resource_path, label, ts_start, ts_end, rule_strings, None, None)

  # create sub-directory of resource_path
  sub_dir = os.path.join(output_directory, resource_path)
  if not os.path.exists(sub_dir):
    os.makedirs(sub_dir)

  # the only method to test; it will write to the directory the final csv files;
  cur_metric.collect()

  #check the existance of the output files
  functions = aggregate_metrics.split(':')
  prefix = functions[0].split('.') #'SAR-cpuusage.all.percent-sys'
  prefix[0] = section
  prefix = '.'.join(prefix)  #CLUSTER-cpuusage-1.all.percent-sys

  for func in functions[1].split(','): #'raw,avg,sum,count'
    file_name = prefix + '.' + func + '.csv'
    file_path = os.path.join(sub_dir, file_name)
    # print 'file to check = ' + file_path  #resources/CLUSTER-cpuusage-1.all.percent-sys.raw.csv
    assert os.path.exists(file_path)

if __name__ == '__main__':
  test_clustermetric()
