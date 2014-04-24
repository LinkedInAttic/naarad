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
  
def test_netstatmetric():
  #construct a NetstatMetric
  section = 'NETSTAT-host1'
  label = 'NETSTAT-host1'
  hostname = 'localhost'
  resource_path = 'resources'
  rule_strings = {}
  output_directory = tmp_dir
  infile='netstat.tcp.out'
  other_options = {'connections': 'host1.localdomain.com<->web1.remotedomain.com:https host1:48860<->email', 'processes': '/firefox'}
  ts_start = None
  ts_end = None

  cur_metric = NetstatMetric(section, infile, hostname, output_directory, resource_path, label, ts_start, ts_end, rule_strings, **other_options)
  cur_metric.infile = os.path.join('logs', infile)

  print cur_metric.infile
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
  for f in output_files: #'raw,avg,sum,count'
    file_path = os.path.join(sub_dir, f)
    assert os.path.exists(file_path)

if __name__ == '__main__':
  test_netstatmetric()
