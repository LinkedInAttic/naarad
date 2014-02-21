# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
import datetime
import logging
import os
import re
import sys
import threading
import json
import time
from datetime import date
from naarad.metrics.metric import Metric
import naarad.utils

logger = logging.getLogger('naarad.metrics.android_rum_metric')

class AndroidRumMetric(Metric):
  """ Class for Android RUM logs, deriving from class Metric """
  clock_format = '%Y-%m-%d %H:%M:%S'
  val_types = ('launch_time', 'nus_update_time')

  # constants for extracting android launch time metrics  
  timing_name = 'timingName'
  timing_value = 'timingValue'
  start = 'start'
  app_on_create = 'linkedin_android_app_oncreate_time'
  nus_update = 'linkedin_android_nus_update_time'
  

  def __init__ (self, metric_type, infile, hostname, outdir, resource_path, label, ts_start, ts_end, rule_strings,
                **other_options):
    Metric.__init__(self, metric_type, infile, hostname, outdir, resource_path, label, ts_start, ts_end, rule_strings)
    self.sub_metrics = self.val_types
    self.sub_metric_description = {
      "launch_time" :"the time taken to launch the client application",
      "nus_update_time" :"the time taken to update NUS list after launch"
    }


  # convert time stamp to date
  def convert_to_date(self, time_stamp):
    """
    convert time stamp in ms to date in format '%Y-%m-%d %H:%M:%S'
    :param LONG time_stamp
    :return: STRING date in format '%Y-%m-%d %H:%M:%S'
    """
    return time.strftime(self.clock_format, time.localtime(time_stamp/1000));


  # get start time stamp, launch time duration, and nus update time duration 
  def get_times(self, native):
    """
    get start time stamp, launch time duration, and nus update time duration from JSON object native
    :param JSON OBJECT native
    :return: LONG event time stamp, LONG launch time, and LONG nus update time
    """
    start_time = 0
    end_time = 0
    launch_time = 0
    nus_update_time = 0

    for item in native:
      if item[self.timing_name] == self.app_on_create and item[self.start] is not None:
        start_time = item[self.start]['long']
      if item[self.timing_name] == self.nus_update:
        if item[self.timing_value] is not None:
          nus_update_time = item[self.timing_value]['long']
        if item[self.start] is not None:
          end_time = item[self.start]['long']

    if start_time == 0 or end_time == 0:
      time_stamp = 0
      launch_time = 0
    else:
      time_stamp = start_time
      launch_time = end_time - start_time
    return (time_stamp, launch_time, nus_update_time)
  
  
  # parse Android RUM logs
  def parse(self):
    # check if outdir exists, if not, create it
    if not os.path.isdir(self.outdir):
      os.makedirs(self.outdir)
    if not os.path.isdir(self.resource_directory):
      os.makedirs(self.resource_directory)

    results = {}
    ts = None

    # set output csv
    launch_time_file = self.get_csv('launch_time')
    nus_update_time_file = self.get_csv('nus_update_time')

    # get Android RUM input data: for each line, generate (timestamp, launch_time, nus_update_time)
    with open(self.infile, 'r') as inf:
      for line in inf:
        try:
          data = json.loads(line)
        except ValueError:
          logger.warn("Invalid JSON Object at line: %s", line)
          
        if data['nativeTimings'] is not None:
          native = data['nativeTimings']['array']
          time_stamp, launch_time, nus_update_time = self.get_times(native)
          if launch_time != 0 and nus_update_time != 0: 
            results[time_stamp] = (str(launch_time), str(nus_update_time))

    # Writing launch time and nus update time stats
    with open(launch_time_file, 'w') as launchtimef:
      with open(nus_update_time_file, 'w') as nusupdatetimef:
        for ts in sorted(results.iterkeys()):
          launchtimef.write( self.convert_to_date(ts) + ',' + results[ts][0] + '\n' )
          nusupdatetimef.write( self.convert_to_date(ts) + ',' + results[ts][1] + '\n' )
    self.csv_files.append(launch_time_file)
    self.csv_files.append(nus_update_time_file)

    return True

