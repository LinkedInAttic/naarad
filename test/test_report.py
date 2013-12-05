# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
import sys
import logging
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')))

from naarad.reporting.report import Report

logger = logging.getLogger('naarad')

def init_logging(log_level):
  log_file = 'test_reporting.log'
  # clear the log file
  with open(log_file, 'w'):
    pass
  numeric_level = getattr(logging, log_level.upper(), None) if log_level else logging.INFO
  if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % log_level)
  logger.setLevel(logging.DEBUG)
  fh = logging.FileHandler(log_file)
  fh.setLevel(logging.DEBUG)
  ch = logging.StreamHandler()
  ch.setLevel(numeric_level)
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  fh.setFormatter(formatter)
  ch.setFormatter(formatter)
  logger.addHandler(fh)
  logger.addHandler(ch)

def main():
  init_logging('INFO')
  rpt = Report(report_name = 'test report', output_directory = '/tmp/naarad', metric_list = ['JMETER', 'GC', 'SAR-memory', 'SAR-device'] )
  rpt.generate()
main()
