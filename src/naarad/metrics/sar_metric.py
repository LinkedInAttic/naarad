# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
import datetime
import logging
import os

from naarad.metrics.metric import Metric
import naarad.utils
from naarad.naarad_constants import important_sub_metrics_import

logger = logging.getLogger('naarad.metrics.SARMetric')

class SARMetric(Metric):
  """ Class for SAR cpuusage logs, deriving from class Metric """
  supported_sar_types = ('SAR-cpuusage', 'SAR-cpuhz', 'SAR-device', 'SAR-memory', 'SAR-memutil', 'SAR-paging',
      'SAR-etcp', 'SAR-tcp', 'SAR-dev', 'SAR-edev', 'SAR-sock', 'SAR-swapping', 'SAR-network', 'SAR-queue', 'SAR-switching')
  def __init__(self, metric_type, infile_list, hostname, outdir, resource_path, label, ts_start, ts_end, rule_strings,
               important_sub_metrics, anomaly_detection_metrics, **other_options):
    metric_type = self.extract_metric_name(metric_type)
    Metric.__init__(self, metric_type, infile_list,  hostname, outdir, resource_path, label, ts_start, ts_end, rule_strings,
                    important_sub_metrics, anomaly_detection_metrics)
    if not self.important_sub_metrics and self.metric_type in important_sub_metrics_import.keys():
      self.important_sub_metrics = important_sub_metrics_import[self.metric_type]
    self.options = None
    self.devices = None
    for (key, val) in other_options.iteritems():
      setattr(self, key, val.split())


  def extract_metric_name(self, metric_name):
    """
    Method to extract SAR metric names from the section given in the config. The SARMetric class assumes that
    the section name will contain the SAR types listed in self.supported_sar_types tuple

    :param str metric_name: Section name from the config
    :return: str which identifies what kind of SAR metric the section represents
    """
    for metric_type in self.supported_sar_types:
      if metric_type in metric_name:
        return metric_type
    logger.error('Section [%s] does not contain a valid metric type, using type: "SAR-generic". Naarad works better '
                 'if it knows the metric type. Valid SAR metric names are: %s', metric_name, self.supported_sar_types)
    return 'SAR-generic'

  def get_csv(self, col, device=None):
    column = naarad.utils.sanitize_string(col)
    if device is None:
      outcsv = os.path.join(self.resource_directory, "{0}.{1}.csv".format(self.label, column))
      self.csv_column_map[outcsv] = col
    else:
      outcsv = os.path.join(self.resource_directory, "{0}.{1}.{2}.csv".format(self.label, device, column))
      self.csv_column_map[outcsv] = device + '.' + col
    return outcsv

  def parse(self):
  # Multiple day span not supported. Assumes time is between 0:00 AM to 11:59 PM, or 0:00 to 23:59
    if not os.path.isdir(self.outdir):
      os.makedirs(self.outdir)
    if not os.path.isdir(self.resource_directory):
      os.makedirs(self.resource_directory)
    data = {}
    for input_file in self.infile_list:
      timestamp_format = None
      with open(input_file, 'r') as infile:
        line = infile.readline()
        # Pre-processing
        try:
          datesar = line.split()[3].split('/')
          # year is not fully qualified - this will work till year 2999 :)
          if int(datesar[2]) < 1000:
            year = int(datesar[2]) + 2000
            datesar[2] = str(year)
        except IndexError:
          logger.error("Header not found for file: %s", input_file)
          logger.error("line: %s", line)
          return False
        date = datesar[2] + '-' + datesar[0] + '-' + datesar[1]
        infile.readline()   #skip blank line
        line = infile.readline()
        columns = line.split()
        if columns[1] in ('AM', 'PM'):
          ts_end_index = 2
        else:
          ts_end_index = 1
        if self.metric_type in self.device_types:
          columnstart = ts_end_index + 1
        else:
          columnstart = ts_end_index
        # Actually parsing data
        lines = infile.readlines()
        last_ts = None
        for i in range(len(lines)):
          # Skipping last line of the file since it could be malformed
          if i == len(lines) - 1:
            break
          line = lines[i]
          # Skipping header lines
          if 'Linux' in line or 'Average' in line or 'MHz' in line:
            continue
          words = line.split()
          if len(words) <= columnstart:
            continue
          ts = naarad.utils.convert_to_24hr_format( ' '.join(words[0:ts_end_index]) )
          if last_ts:
            if last_ts.startswith("23:") and ts.startswith("00:"):
              logger.info("Date rolling over")
              old_datetime = datetime.datetime.strptime(date, "%Y-%m-%d")
              new_datetime = old_datetime + datetime.timedelta(days=1)
              date = new_datetime.strftime("%Y-%m-%d")
          datetimestamp = date + ' ' + ts
          if not timestamp_format or timestamp_format == 'unknown':
            timestamp_format = naarad.utils.detect_timestamp_format(datetimestamp)
          if timestamp_format == 'unknown':
            continue
          datetimestamp = naarad.utils.get_standardized_timestamp(datetimestamp, timestamp_format)
          last_ts = ts
          if self.ts_out_of_range(datetimestamp):
            continue
          if self.metric_type in self.device_types:
            # Skipping headers that appear in the middle of the file
            if not naarad.utils.is_number( words[ts_end_index + 1] ):
              continue
            if self.devices and words[ts_end_index] not in self.devices:
              continue
            device = words[ts_end_index]
          else:
            # Skipping headers that appear in the middle of the file
            if not naarad.utils.is_number( words[ts_end_index] ):
              continue
            device = None
          datetimestamp = naarad.utils.reconcile_timezones(datetimestamp, self.timezone, self.graph_timezone)
          for i in range(columnstart, len(words)):
            if self.options and columns[i] not in self.options:
              continue
            outcsv = self.get_csv(columns[i], device)
            if outcsv in data:
              data[outcsv].append(datetimestamp + ',' + words[i])
            else:
              data[outcsv] = []
              data[outcsv].append( datetimestamp + ',' + words[i] )
    # Post processing, putting data in csv files
    for csv in data.keys():
      self.csv_files.append(csv)
      with open(csv, 'w') as csvf:
        csvf.write('\n'.join(sorted(data[csv])))
    return True

