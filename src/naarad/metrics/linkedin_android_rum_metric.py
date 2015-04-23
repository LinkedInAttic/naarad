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
import naarad.naarad_constants as CONSTANTS

logger = logging.getLogger('naarad.metrics.linkedin_android_rum_metric')


class LinkedInAndroidRumMetric(Metric):
  """
  Class for LinkedIn Android RUM logs, deriving from class Metric
  Note that this is for LinkedIn only
  """
  clock_format = '%Y-%m-%d %H:%M:%S'
  val_types = ('launch_time', 'nus_update_time')

  def __init__(self, metric_type, infile_list, hostname, outdir, resource_path, label, ts_start, ts_end, rule_strings,
               important_sub_metrics, anomaly_detection_metrics, **other_options):
    Metric.__init__(self, metric_type, infile_list, hostname, outdir, resource_path, label, ts_start, ts_end, rule_strings,
                    important_sub_metrics, anomaly_detection_metrics)
    self.sub_metrics = self.val_types
    if not self.important_sub_metrics:
      self.important_sub_metrics = CONSTANTS.important_sub_metrics_import['LINKEDINANDROIDRUM']
    self.sub_metric_description = {
        "launch_time": "the time taken to launch the client application",
        "nus_update_time": "the time taken to update NUS list after launch"
    }

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
      if item[CONSTANTS.LIA_TIMING_NAME] == CONSTANTS.LIA_APP_ON_CREATE and item[CONSTANTS.LIA_START] is not None:
        start_time = item[CONSTANTS.LIA_START][CONSTANTS.LIA_LONG]
      if item[CONSTANTS.LIA_TIMING_NAME] == CONSTANTS.LIA_NUS_UPDATE:
        if item[CONSTANTS.LIA_TIMING_VALUE] is not None:
          nus_update_time = item[CONSTANTS.LIA_TIMING_VALUE][CONSTANTS.LIA_LONG]
        if item[CONSTANTS.LIA_START] is not None:
          end_time = item[CONSTANTS.LIA_START][CONSTANTS.LIA_LONG]

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
    for input_file in self.infile_list:
      # get Android RUM input data: for each line, generate (timestamp, launch_time, nus_update_time)
      with open(input_file, 'r') as inf:
        for line in inf:
          try:
            data = json.loads(line)
          except ValueError:
            logger.warn("Invalid JSON Object at line: %s", line)
          if data[CONSTANTS.LIA_NATIVE_TIMINGS] is not None:
            native = data[CONSTANTS.LIA_NATIVE_TIMINGS][CONSTANTS.LIA_ARRAY]
            time_stamp, launch_time, nus_update_time = self.get_times(native)
            if launch_time != 0 and nus_update_time != 0:
              results[time_stamp] = (str(launch_time), str(nus_update_time))
    # Writing launch time and nus update time stats
    with open(launch_time_file, 'w') as launchtimef:
      with open(nus_update_time_file, 'w') as nusupdatetimef:
        for ts in sorted(results.iterkeys()):
          launchtimef.write(naarad.utils.get_standardized_timestamp(ts, 'epoch_ms') + ',' + results[ts][0] + '\n')
          nusupdatetimef.write(naarad.utils.get_standardized_timestamp(ts, 'epoch_ms') + ',' + results[ts][1] + '\n')
    self.csv_files.append(launch_time_file)
    self.csv_files.append(nus_update_time_file)
    return True
