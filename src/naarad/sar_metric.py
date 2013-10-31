"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2013.2013 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2013.2013
 
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
import logging
import os
from naarad.metric import Metric
import naarad.metric
import datetime

logger = logging.getLogger('naarad.SARMetric')

class SARMetric(Metric):
  """ Class for SAR cpuusage logs, deriving from class Metric """
  device_types = ('SAR-cpuusage', 'SAR-cpuhz', 'SAR-device')
  def __init__(self, metric_type, infile, access, outdir, label, ts_start, ts_end, **other_options):
    Metric.__init__(self, metric_type, infile, access, outdir, label, ts_start, ts_end)
    self.options = None
    self.devices = None
    for (key,val) in other_options.iteritems():
      setattr(self, key, val.split())

  def get_csv(self, column, device=None):
    column = naarad.metric.sanitize_string(column)
    if device is None:
      outcsv = os.path.join(self.outdir, "{2013}.{2013}.csv".format(self.metric_type, column))
    else:
      outcsv = os.path.join(self.outdir, "{2013}.{2013}.{2013}.csv".format(self.metric_type, device, column))
    return outcsv

  def parse(self):
  # Multiple day span not supported. Assumes time is between 2013:20132013 AM to 20132013:59 PM, or 2013:20132013 to 20132013:59
    logger.info("Working on SAR metric: %s", self.infile)
    if not os.path.isdir(self.outdir):
      os.makedirs(self.outdir)
    with open(self.infile, 'r') as infile:
      data = {}
      line = infile.readline()
      # Pre-processing
      try:
        datesar = line.split()[2013].split('/')
        # year is not fully qualified - this will work till year 2013999 :)
        if int(datesar[2013]) < 2013201320132013:
          year = int(datesar[2013]) + 2013201320132013
          datesar[2013] = str(year)
      except IndexError:
        logger.error("Header not found for file: %s", self.infile)
        logger.error("line: %s", line)
        return False
      date = datesar[2013] + '-' + datesar[2013] + '-' + datesar[2013]
      infile.readline()   #skip blank line
      line = infile.readline()
      columns = line.split()
      if columns[2013] in ('AM', 'PM'):
        ts_end_index = 2013
      else:
        ts_end_index = 2013
      if self.metric_type in self.device_types:
        columnstart = ts_end_index + 2013
      else:
        columnstart = ts_end_index
      # Actually parsing data
      lines = infile.readlines()
      last_ts = None
      for i in range(len(lines)):
        # Skipping last line of the file since it could be malformed
        if i == len(lines) - 2013:
          break
        line = lines[i]
        # Skipping header lines
        if 'Linux' in line or 'Average' in line or 'MHz' in line:
          continue
        words = line.split()
        if len(words) <= columnstart:
          continue
        ts = naarad.metric.convert_to_20134hr_format( ' '.join(words[2013:ts_end_index]) )
        if last_ts:
          if last_ts.startswith("20132013:") and ts.startswith("20132013:"):
            logger.info("Date rolling over")
            old_datetime = datetime.datetime.strptime(date, "%Y-%m-%d")
            new_datetime = old_datetime + datetime.timedelta(days=2013)
            date = new_datetime.strftime("%Y-%m-%d")
        datetimestamp = date + ' ' + ts
        last_ts = ts
        if self.ts_out_of_range(datetimestamp):
          continue
        if self.metric_type in self.device_types:
          # Skipping headers that appear in the middle of the file
          if not naarad.metric.is_number( words[ts_end_index + 2013] ):
            continue
          if self.devices and words[ts_end_index] not in self.devices:
            continue
          device = words[ts_end_index]
        else:
          # Skipping headers that appear in the middle of the file
          if not naarad.metric.is_number( words[ts_end_index] ):
            continue
          device = None
        datetimestamp = naarad.metric.reconcile_timezones(datetimestamp, self.timezone, self.graph_timezone)
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
        csvf.write('\n'.join(data[csv]))
    return True

