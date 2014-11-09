# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
import os
import sys
import uuid
import shutil

# add the path of ~/naarad/src;   the testing py is under ~/naarad/test
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')))
import naarad.utils
from naarad.metrics.netstat_metric import NetstatMetric

#the temporary directory for testing, will remove it after done.
tmp_dir = ''

def prepare_data():
  """
  Hard code the raw logs and output into files so that netstat metric can pick them up.
  Doing so can remove the dependency on physical logs.
  :return:
  """
  log = []
  log.append('2014-04-14 12:09:01.67581	Active Internet connections (w/o servers)')
  log.append('2014-04-14 12:09:01.67581	Proto Recv-Q Send-Q Local Address               Foreign Address             State       PID/Program name')
  log.append('2014-04-14 12:09:01.67581	tcp        0      500 host1.localdomain.com:43214 web1.remotedomain.com:https ESTABLISHED 4996/firefox')
  log.append('2014-04-14 12:09:01.67581	tcp        120      0 host1.localdomain.com:48860 email.localdomain.com:https ESTABLISHED 4996/firefox')
  log.append('2014-04-14 12:09:03.76251	Active Internet connections (w/o servers)')
  log.append('2014-04-14 12:09:03.76251	Proto Recv-Q Send-Q Local Address               Foreign Address             State       PID/Program name')
  log.append('2014-04-14 12:09:03.76251	tcp        0      200 host1.localdomain.com:43214 web1.remotedomain.com:https ESTABLISHED 4996/firefox')
  log.append('2014-04-14 12:09:03.76251	tcp        330      0 host1.localdomain.com:48860 email.localdomain.com:https ESTABLISHED 4996/firefox')
  log.append('2014-04-14 12:09:05.84302	Active Internet connections (w/o servers)')
  log.append('2014-04-14 12:09:05.84302	Proto Recv-Q Send-Q Local Address               Foreign Address             State       PID/Program name')
  log.append('2014-04-14 12:09:05.84302	tcp        0      345 host1.localdomain.com:43214 web1.remotedomain.com:https ESTABLISHED 4996/firefox')
  log.append('2014-04-14 12:09:05.84302	tcp        440      0 host1.localdomain.com:48860 email.localdomain.com:https ESTABLISHED 4996/firefox')
  log.append('2014-04-14 12:09:07.91455	Active Internet connections (w/o servers)')
  log.append('2014-04-14 12:09:07.91455	Proto Recv-Q Send-Q Local Address               Foreign Address             State       PID/Program name')
  log.append('2014-04-14 12:09:07.91455	tcp        0      0 host1.localdomain.com:43214 web1.remotedomain.com:https ESTABLISHED 4996/firefox')
  log.append('2014-04-14 12:09:07.91455	tcp        1550      0 host1.localdomain.com:48860 email.localdomain.com:https ESTABLISHED 4996/firefox')
  log.append('2014-04-14 12:09:09.98031	Active Internet connections (w/o servers)')
  log.append('2014-04-14 12:09:09.98031	Proto Recv-Q Send-Q Local Address               Foreign Address             State       PID/Program name')
  log.append('2014-04-14 12:09:09.98031	tcp        0      564 host1.localdomain.com:43214 web1.remotedomain.com:https ESTABLISHED 4996/firefox')
  log.append('2014-04-14 12:09:09.98031	tcp        20      0 host1.localdomain.com:48860 email.localdomain.com:https ESTABLISHED 4996/firefox')
  log.append('2014-04-14 12:09:12.05993	Active Internet connections (w/o servers)')
  log.append('2014-04-14 12:09:12.05993	Proto Recv-Q Send-Q Local Address               Foreign Address             State       PID/Program name')
  log.append('2014-04-14 12:09:12.05993	tcp        0      234 host1.localdomain.com:43214 web1.remotedomain.com:https ESTABLISHED 4996/firefox')
  log.append('2014-04-14 12:09:12.05993	tcp        3245      0 host1.localdomain.com:48860 email.localdomain.com:https ESTABLISHED 4996/firefox')

  with open(os.path.join(tmp_dir, 'netstat.tcp.out'), 'w') as fh:
    fh.write('\n'.join(log))

def setup():
  create_tmp_dir()
  prepare_data()

def teardown():
  delete_tmp_dir()

def create_tmp_dir():
  """
  create a unique tmp dir to hold the downloaded local files
  if the tmp_dir grenerated already exists, then simply return
  the user simply try again to generate another unique tmp dir
  :return:
  """
  global tmp_dir
  tmp_dir = os.path.join('./', 'tmp' + '.' + str(uuid.uuid4()))   #./tmp.'randomstring'
  if not os.path.exists(tmp_dir):
    os.makedirs(tmp_dir)
  else:
    print "the path of %s already exists, please try again." % tmp_dir
    return

def delete_tmp_dir():
  """
  delete the tmp directory
  :return:
  """
  shutil.rmtree(tmp_dir)

def test_netstatmetric():
  """
  First construct a NetstatMetric, then call the parse(), finally check whether the output files are there
  :return:
  """
  #construct a NetstatMetric
  section = 'NETSTAT-host1'
  label = 'NETSTAT-host1'
  hostname = 'localhost'
  resource_path = 'resources'
  rule_strings = {}
  output_directory = tmp_dir
  infile_list=['netstat.tcp.out']
  other_options = {'connections': 'host1.localdomain.com<->web1.remotedomain.com:https host1:48860<->email', 'processes': '/firefox'}
  ts_start = None
  ts_end = None
  anomaly_detection_metrics = None
  important_sub_metrics =[]

  cur_metric = NetstatMetric(section, infile_list, hostname, output_directory, resource_path, label, ts_start, ts_end, rule_strings, important_sub_metrics, anomaly_detection_metrics, **other_options)
  cur_metric.infile_list =[os.path.join(tmp_dir, f) for f in cur_metric.infile_list]

  # create sub-directory of resource_path
  sub_dir = os.path.join(output_directory, resource_path)
  if not os.path.exists(sub_dir):
    os.makedirs(sub_dir)

  cur_metric.parse()

  #check the existance of the output files
  output_files = ['NETSTAT-host1.host1.localdomain.com_43214.web1.remotedomain.com_https.RecvQ.csv',
                  'NETSTAT-host1.host1.localdomain.com_43214.web1.remotedomain.com_https.SendQ.csv',
                  'NETSTAT-host1.host1.localdomain.com_48860.email.localdomain.com_https.RecvQ.csv',
                  'NETSTAT-host1.host1.localdomain.com_48860.email.localdomain.com_https.SendQ.csv']
  for f in output_files:
    file_path = os.path.join(sub_dir, f)
    assert os.path.exists(file_path)

if __name__ == '__main__':
  test_netstatmetric()
