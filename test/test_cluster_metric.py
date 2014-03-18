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
# add the path of ~/naarad/src;   the testing py is under ~/naarad/test 
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')))

#the temporary directory for testing, will remove it after done. 
tmp_dir = ''
naarad_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ~/naarad/
config_dir = 'examples/conf'
config_file = 'config-cluster'
input_dir = 'examples/logs'

files_to_check = ["CLUSTER-1.sda.await.raw.png", 'CLUSTER-1.sda.await.sum.png', 'CLUSTER-1.sda.await.count.png', 'CLUSTER-1.all.percent-sys.raw.png']

def setup():
  create_tmp_dir()

def teardown():
  delete_tmp_dir() 
  #print 'tear down' 
 
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
  
def test_cluster():
  ''' list of abosulute urls with no output file name'''
  naarad_cmd = os.path.join(naarad_dir, 'bin/naarad')
  naarad_conf = os.path.join(naarad_dir, config_dir, config_file)
  naarad_input_dir = os.path.join(naarad_dir, input_dir)
  
  command = naarad_cmd + ' -c ' + naarad_conf + ' -i ' + naarad_input_dir + ' -o ' + tmp_dir
  os.system(command)
  
  for fc in files_to_check:
    file_path = os.path.join(tmp_dir, 'resources' , fc)
    assert os.path.exists(file_path),  "File of %s does not exist! " % file_path  
