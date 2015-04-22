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

import nose
from nose.plugins.attrib import attr
import os
import shutil
import sys
import time
import uuid

# add the path of ~/naarad/src;   the testing py is under ~/naarad/test
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')))

import naarad.httpdownload

# the port of local http server
port_test = 8011

# the temporary directory for testing, will remove it after done.
tmp_dir = ''

# the testing download file (will be hosted from local http server)
test_input_file = 'bin/naarad'


def setup():
  start_http_server()
  create_tmp_dir()


def teardown():
  kill_http_server()
  delete_tmp_dir()


def start_http_server():
  '''start a local http server for testing'''
  global port_test
  command = 'python -m SimpleHTTPServer %s &' % port_test
  os.system(command)
  time.sleep(1)


def kill_http_server():
  '''After testing, kill the local http server'''
  command = 'pkill -f SimpleHTTPServer'
  os.system(command)
  time.sleep(1)


def create_tmp_dir():
  '''create a unique tmp dir to hold the downloaded local files'''
  ''' if the tmp dir grenerated already exists, then simply return'''
  ''' the user simply try again to generate another unique tmp dir'''
  global tmp_dir
  tmp_dir = os.path.join('./tmp/', str(uuid.uuid4()))
  if not os.path.exists(tmp_dir):
    os.makedirs(tmp_dir)
  else:
    print "the path of %s already exists, please try again." % tmp_dir
    return


def delete_tmp_dir():
  '''delete the tmp directory'''
  global tmp_dir
  shutil.rmtree(tmp_dir)


@attr('local')
def test_list_of_urls_no_output():
  ''' list of abosulute urls with no output file name'''
  global tmp_dir
  url = "http://localhost:8011/bin/naarad"
  outdir = tmp_dir

  if os.path.exists(os.path.join(outdir, "naarad")):
    os.remove(os.path.join(outdir, "naarad"))

  output_file = naarad.httpdownload.download_url_single(url, outdir)

  assert os.path.exists(output_file), "File of %s does not exist! " % output_file

  if os.path.exists(os.path.join(outdir, "naarad")):
    os.remove(os.path.join(outdir, "naarad"))


@attr('local')
def test_list_of_urls_with_output():
  ''' list of abosulute urls with output file name given'''
  global tmp_dir

  url = "http://localhost:8011/bin/naarad"
  outfile = "naarad.tmp"
  outdir = tmp_dir

  if os.path.exists(os.path.join(outdir, "1a.html")):
    os.remove(os.path.join(outdir, "1a.html"))

  output_file = naarad.httpdownload.download_url_single(url, outdir, outfile)

  assert os.path.exists(output_file), "File of %s does not exist! " % output_file

  if os.path.exists(os.path.join(outdir, "1a.html")):
    os.remove(os.path.join(outdir, "1a.html"))


@attr('local')
def test_regex_urls():
  '''a seeding url, and a regex expression of urls '''
  global tmp_dir
  seed_url = "http://localhost:8011/test/httpdownload.html"
  outdir = tmp_dir
  regex = ".*"

  output_files = []
  output_files = naarad.httpdownload.download_url_regex(seed_url, outdir, regex)

  print output_files
  print 'abc'
  output_file = os.path.join(outdir, 'test_httpdownload.pyc')
  assert os.path.exists(output_file), "File of %s does not exist! " % output_file
  output_file = os.path.join(outdir, 'test_httpdownload.py')
  assert os.path.exists(output_file), "File of %s does not exist! " % output_file
