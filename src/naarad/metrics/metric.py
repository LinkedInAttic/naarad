# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0
 
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
from collections import defaultdict
import logging
import numpy 
import os
import re
import sys
import threading
import time
import urllib
from naarad.graphing.plot_data import PlotData as PD
import naarad.utils
import naarad.httpdownload

logger = logging.getLogger('naarad.metrics.Metric')

class Metric(object):
  beginning_ts = None
  beginning_date = None
  ignore = False
  timezone = "PDT"
  options = None
  
  sub_metrics = None   #users can specify what sub_metrics to process/plot;  
  unit = ''  # the unit of the metric
  

  def __init__ (self, metric_type, infile, hostname, output_directory, resource_path, label, ts_start, ts_end, **other_options):
    self.metric_type = metric_type
    self.infile = infile
    self.hostname = hostname
    self.outdir = output_directory
    self.resource_path = resource_path
    self.resource_directory = os.path.join(self.outdir, self.resource_path)
    self.label = label
    self.ts_start = ts_start
    self.ts_end = ts_end
    self.calc_metrics = None
    self.precision = None
    self.sep = ','
    self.titles_string = None
    self.ylabels_string = None
    self.csv_files = []
    self.plot_files = []
    self.stats_files = []
    self.important_stats_files = []
    self.percentiles_files = []
    self.csv_column_map = {}
    self.metric_description = defaultdict(lambda: 'None')
    self.important_sub_metrics = ()
    if other_options:
      for (key, val) in other_options.iteritems():
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
    # self.infile can be of several formats: for instance a local dir (e.g., /path/a.log) or an http url;  
    # decide the case based on self.infile; 
    # self.access is optional, can be removed. 
    
    if self.infile.startswith("http://") or self.infile.startswith("https://"):     
      if naarad.utils.is_valid_url(self.infile):      
        # reassign self.infile, so that it points to the local (downloaded) file
        http_download_dir = os.path.join(self.outdir, self.label)
        self.infile = naarad.httpdownload.download_url_single(self.infile, http_download_dir)
        return True
      else:
        logger.error("The given url of {0} is invalid.\n".format(self.infile))
        return False
    else:   
      self.collect_local()
      return True

  def get_csv(self, column):
    col = naarad.utils.sanitize_string(column)
    csv = os.path.join(self.resource_directory, self.metric_type + '.' + col + '.csv')
    self.csv_column_map[csv] = column
    return csv

  def get_important_sub_metrics_csv(self):
    csv = os.path.join(self.resource_directory, self.metric_type + '.important_sub_metrics.csv')
    return csv

  def get_stats_csv(self):
    csv = os.path.join(self.resource_directory, self.metric_type + '.stats.csv')
    return csv

  def get_percentiles_csv_from_data_csv(self, data_csv):
    percentile_csv_file = '.'.join(data_csv.split('.')[0:-1]) + '.percentiles.csv'
    return percentile_csv_file

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
          #print "adding %s to dict for %s" %(out_csv, self.columns[i])
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
    stats_to_calculate = ['mean', 'std']  # TODO: get input from user
    percentiles_to_calculate = range(5, 101, 5)  # TODO: get input from user
    percentiles_to_calculate.append(99)
    headers = 'sub-metric,mean,std,p50,p75,p90,p95,p99\n'
    metric_stats_csv_file = self.get_stats_csv()
    imp_metric_stats_csv_file = self.get_important_sub_metrics_csv()
    imp_metric_stats_present = False  
    logger.info("Calculating stats for important sub-metrics in %s and all sub-metrics in %s", imp_metric_stats_csv_file, metric_stats_csv_file)
    with open(metric_stats_csv_file, 'w') as FH_W:
      with open(imp_metric_stats_csv_file, 'w') as FH_W_IMP:
        FH_W.write(headers)
        for csv_file in self.csv_files:
          data = []
          if not os.path.getsize(csv_file):
            continue
          column = self.csv_column_map[csv_file]
          percentile_csv_file = self.get_percentiles_csv_from_data_csv(csv_file)
          with open(csv_file, 'r') as FH:
            for line in FH:
              words = line.split(',')
              data.append(float(words[1]))
          calculated_stats, calculated_percentiles = naarad.utils.calculate_stats(data, stats_to_calculate, percentiles_to_calculate)
          with open(percentile_csv_file, 'w') as FH_P:
            for percentile in sorted(calculated_percentiles.iterkeys()):
              FH_P.write("%d, %f\n" % (percentile, calculated_percentiles[percentile]))
          self.percentiles_files.append(percentile_csv_file)
          to_write = [column, calculated_stats['mean'], calculated_stats['std'], calculated_percentiles[50], calculated_percentiles[75], calculated_percentiles[90], calculated_percentiles[95], calculated_percentiles[99]]
          to_write = map(lambda x: naarad.utils.normalize_float_for_display(x), to_write)
          FH_W.write(','.join(to_write) + '\n') 
          # Important sub-metrics and their stats go in imp_metric_stats_csv_file
          if column in self.important_sub_metrics:
            if not important_sub_metrics:
              FH_W_IMP.write(headers)
              imp_metric_stats_present = True
            FH_W_IMP.write(','.join(to_write) + '\n')
        if imp_metric_stats_present:
          self.important_stats_files.append(imp_metric_stats_csv_file)
      self.stats_files.append(metric_stats_csv_file)


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
              ts_diff = naarad.utils.convert_to_unixts(ts) - naarad.utils.convert_to_unixts(old_ts)
              if ts_diff != 0 :
                new_metric_val = 1000 * (float(val) - float(old_val)) / ts_diff
              else:
                new_metric_val = 0
                logger.warn("rate calculation encountered zero timestamp difference")
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
    logger.info('Using graphing_library {lib} for metric {name}'.format(lib=graphing_library, name=self.label))
    for out_csv in self.csv_files:
      csv_filename = os.path.basename(out_csv)
      # The last element is .csv, don't need that in the name of the chart
      graph_title = '.'.join(csv_filename.split('.')[0:-1])
      column = self.csv_column_map[out_csv]
      column = naarad.utils.sanitize_string(column)
      if self.metric_description and column in self.metric_description.keys():
        plot_data = [PD(input_csv=out_csv, csv_column=1, series_name=graph_title, y_label=self.metric_description[column], precision=None, graph_height=600, graph_width=1200, graph_type='line')]
      else:
        plot_data = [PD(input_csv=out_csv, csv_column=1, series_name=graph_title, y_label=column, precision=None, graph_height=600, graph_width=1200, graph_type='line')]
      graphed, div_file = Metric.graphing_modules[graphing_library].graph_data(plot_data, self.resource_directory, self.resource_path, graph_title)
      if graphed:
        self.plot_files.append(div_file)
    return True
