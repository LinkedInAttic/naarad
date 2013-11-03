# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0
 
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
import calendar
from collections import defaultdict
import datetime
import logging
import numpy as np
import os
import pytz
from pytz import timezone
import re
import sys
import threading
import time
import urllib

logger = logging.getLogger('naarad.metrics.Metric')

class Metric(object):
  beginning_ts = None
  beginning_date = None
  ignore = False
  timezone = "PDT"
  options = None

  def __init__ (self, metric_type, infile, access, output_directory, label, ts_start, ts_end, **other_options):
    self.metric_type = metric_type
    self.infile = infile
    self.access = access
    self.outdir = output_directory
    self.label = label
    self.ts_start = ts_start
    self.ts_end = ts_end
    self.calc_metrics = None
    self.precision = None
    self.sep = ','
    self.titles_string = None
    self.ylabels_string = None
    self.csv_files = []
    self.metric_description = defaultdict(lambda: 'None')
    if other_options:
      for (key,val) in other_options.iteritems():
        setattr(self, key, val)
      if not self.titles_string:
        self.titles_string = self.columns
      if self.columns:
        self.columns = self.columns.split()
      self.titles = dict(zip(self.columns, self.titles_string.split(','))) if self.columns and self.titles_string else None
      self.ylabels = dict(zip(self.columns, self.ylabels_string.split(','))) if self.columns and self.ylabels_string else None

  def ts_out_of_range(self, timestamp):
    if self.ts_start and timestamp < self.ts_start:
      return True
    elif self.ts_end and timestamp > self.ts_end:
      return True
    return False

  def collect_local(self):
    return os.path.exists(self.infile)

  def collect(self):
    if self.access == 'local':
      return self.collect_local()
    else:
      logger.warn("WARNING: access is set to other than local for metric", self.label)
      return False

  def get_csv(self, column):
    col = sanitize_string(column)
    csv = os.path.join(self.outdir, self.metric_type + '.' + col + '.csv')
    return csv

  def parse(self):
    logger.info("Working on" + self.infile)
    with open(self.infile, 'r') as infile:
      data = {}
      for line in infile:
        if self.sep is None:
          words = line.strip().split()
        else:
          words = line.strip().split(self.sep)
        if len(words) == 0:
          continue
        if len(words) < len(self.columns):
          logger.error("ERROR: Number of columns given in config is more than number of columns present in file {0}\n".format(self.infile))
          return False
        ts = naarad.utils.reconcile_timezones(words[0], self.timezone, self.graph_timezone)
        for i in range(len(self.columns)):
          out_csv = self.get_csv(self.columns[i])
          if out_csv in data:
            data[out_csv].append( ts + ',' + words[i+1] )
          else:
            data[out_csv] = []
            data[out_csv].append( ts + ',' + words[i+1] )
    # Post processing, putting data in csv files
    for csv in data.keys():
      self.csv_files.append(csv)
      with open(csv, 'w') as fh:
        fh.write('\n'.join(data[csv]))
    return True

  def calculate_stats(self):
    data = {}
    metric_stats_csv_file = os.path.join(self.outdir, self.metric_type + '.stats.csv')
    with open(metric_stats_csv_file, 'w') as FH_W:
      FH_W.write("sub-metric, mean, std, p50, p75, p90, p95\n")
      for csv in self.csv_files:
        if not os.path.getsize(csv):
          continue
        data[csv] = []
        #TODO: Fix this hacky way to get the sub-metrics
        column = '.'.join(csv.split('.')[1:-1])
        with open(csv, 'r') as FH:
          for line in FH:
            words = line.split(',')
            data[csv].append(float(words[1]))
        #hist, bin_edges = np.histogram(data[csv],100)
        mean = np.mean(data[csv])
        std = np.std(data[csv])
        percentiles = {}
        percentile_csv_file = '.'.join(csv.split('.')[0:-1]) + '.percentiles.csv'
        with open(percentile_csv_file, 'w') as FH_P:
          for i in range(5, 100, 5):
            percentiles[i] = np.percentile(data[csv], i)
            FH_P.write("%d, %f\n" % (i, percentiles[i]))
        to_write = [column, mean, std, percentiles[50], percentiles[75], percentiles[90], percentiles[95]]
        to_write = map(lambda x: str(x), to_write)
        FH_W.write(', '.join(to_write) + '\n') 

  def calc(self):
    if not self.calc_metrics:
      return
    calculation_array = self.calc_metrics.split()
    for calculation in calculation_array:
      words = calculation.split('=')
      newmetric = words[0]
      expr = words[1]
      p = re.compile('(\w+)\((.+)\)')
      calc_type = p.match(expr).group(1)
      old_metric = p.match(expr).group(2)
      logger.debug('In calc() : %s %s %s %s', newmetric, expr, old_metric, calc_type)
      if not calc_type in ('rate', 'diff'):
        logger.error("ERROR: Invalid calc_metric type {0} defined in config".format(calc_type))
        continue
      old_metric_csv = self.get_csv(old_metric)
      new_metric_csv = self.get_csv(newmetric)
      self.csv_files.append(new_metric_csv)
      old_val = None
      with open(old_metric_csv, 'r') as FH:
        with open(new_metric_csv, 'w') as NEW_FH:
          for line in FH:
            w = line.split(',')
            ts = w[0]
            val = w[1]
            if not old_val:
              old_ts = ts
              old_val = val
              continue
            if calc_type == 'rate':
              #Multiply rate by 1000 since timestamp is in ms
              new_metric_val = 1000 * (float(val) - float(old_val)) / (convert_to_unixts(ts) - convert_to_unixts(old_ts))
            elif calc_type == 'diff':
              new_metric_val = (float(val) - float(old_val))
            old_ts = ts
            old_val = val
            NEW_FH.write(ts)
            NEW_FH.write(',')
            NEW_FH.write(str(new_metric_val))
            NEW_FH.write('\n')

  def graph(self, graphing_library = 'matplotlib'):
    html_string = []
    html_string.append('<h1>Metric: {0}</h1>\n'.format(self.metric_type))
    graphed = False
    if self.metric_type.startswith('GC'):
      graphing_library = 'matplotlib'
    logger.info('Using graphing_library {lib} for metric {name}'.format(lib=graphing_library, name=self.label))
    for out_csv in self.csv_files:
      csv_filename = os.path.basename(out_csv)
      # The last element is .csv, don't need that in the name of the chart
      graph_title = '.'.join(csv_filename.split('.')[0:-1])
      column = '.'.join(graph_title.split('.')[1:])
      graphed, html_ret = Metric.graphing_modules[graphing_library].graph_csv(self.outdir, out_csv, graph_title, graph_title)
      if html_ret:
        html_string.append(html_ret)
      else:
        if graphed:
          img_tag = '<h3>{title}</h3><p><b>Description</b>: {description}</p><img src={image_name}.png />\n'.format(title=graph_title, description=self.metric_description[column], image_name=graph_title)
        else:
          img_tag = '<h3>{title}</h3><p><b>Description</b>: {description}</p>No data for this metric\n'.format(title=graph_title, description=self.metric_description[column])
        html_string.append(img_tag)
    return '\n'.join(html_string)
