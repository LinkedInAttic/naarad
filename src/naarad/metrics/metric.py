# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
from collections import defaultdict
import glob
import logging
import os
import re
from naarad.graphing.plot_data import PlotData as PD
import naarad.utils
import naarad.httpdownload
import naarad.naarad_constants as CONSTANTS
import datetime
import heapq
from luminol import anomaly_detector, correlator

logger = logging.getLogger('naarad.metrics.metric')

class Metric(object):

  def __init__(self, metric_type, infile_list, hostname, output_directory, resource_path, label, ts_start, ts_end,
                rule_strings, important_sub_metrics, anomaly_detection_metrics, **other_options):
    self.metric_type = metric_type
    self.infile_list = infile_list
    self.hostname = hostname
    self.outdir = output_directory
    self.resource_path = resource_path
    self.resource_directory = os.path.join(self.outdir, self.resource_path)
    self.label = label
    self.ts_start = naarad.utils.get_standardized_timestamp(ts_start, None)
    self.ts_end = naarad.utils.get_standardized_timestamp(ts_end, None)
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
    self.column_csv_map = {}
    self.csv_column_map = {}
    self.sub_metric_description = defaultdict(lambda: 'None')  # the description of the submetrics.
    self.sub_metric_unit = defaultdict(lambda: 'None')      # the unit of the submetrics.  The plot will have the Y-axis being: Metric name (Unit)
    self.important_sub_metrics = important_sub_metrics
    self.sla_list = []  # TODO : remove this once report has grading done in the metric tables
    self.sla_map = defaultdict(lambda :defaultdict(lambda: defaultdict(None)))
    self.calculated_stats = {}
    self.calculated_percentiles = {}
    self.summary_stats_list = CONSTANTS.DEFAULT_SUMMARY_STATS
    self.summary_stats = defaultdict(dict)
    self.status = CONSTANTS.OK
    self.ignore = False
    self.timezone = "PDT"
    self.options = None
    self.sub_metrics = None   #users can specify what sub_metrics to process/plot;
    self.groupby = None
    self.summary_charts = []
    self.aggregation_granularity = 'second'
    # Leave the flag here for the future use to control summary page
    self.summary_html_content_enabled = True
    self.anomaly_detection_metrics = anomaly_detection_metrics
    self.anomalies = {}
    for (key, val) in rule_strings.iteritems():
      naarad.utils.set_sla(self, self.label, key, val)
    if other_options:
      for (key, val) in other_options.iteritems():
        setattr(self, key, val)
      if not self.titles_string:
        self.titles_string = self.columns
      if self.columns:
        self.columns = self.columns.split()
      if self.groupby:
        self.groupby = self.groupby.split()

      self.titles = dict(zip(self.columns, self.titles_string.split(','))) if self.columns and self.titles_string else None
      self.ylabels = dict(zip(self.columns, self.ylabels_string.split(','))) if self.columns and self.ylabels_string else None

  def name_to_index(self, name):
    index = None
    for i in range(len(self.columns)):
      if name == self.columns[i]:
        index = i+1
    return index

  def get_groupby_indexes(self, groupby):
    groupby_indexes = []
    for group in groupby:
      if ':' in group.rstrip(':'):
        name, index = group.split(':')
        groupby_indexes.append(index)
      else:
        groupby_indexes.append(self.name_to_index(group.rstrip(':')))
    return groupby_indexes

  def ts_out_of_range(self, timestamp):
    if self.ts_start and timestamp < self.ts_start:
      return True
    elif self.ts_end and timestamp > self.ts_end:
      return True
    return False

  def collect_local(self, infile):
    return os.path.exists(infile)

  def collect(self):
    # self.infile_list can be of several formats: for instance a local dir (e.g., /path/a.log) or an http url;
    # decide the case based on self.infile_list;
    # self.access is optional, can be removed.
    collected_files = []
    for infile in self.infile_list:
      if infile.startswith("http://") or infile.startswith("https://"):
        if naarad.utils.is_valid_url(infile):
          http_download_dir = os.path.join(self.outdir, self.label)
          output_file = naarad.httpdownload.download_url_single(infile, http_download_dir)
          if output_file:
            collected_files.append(output_file)
          else:
            return False
        else:
          logger.error("The given url of {0} is invalid.\n".format(infile))
          return False
      else:
        file_matches = glob.glob(infile)
        if len(file_matches) == 0:
          return False
        for file_name in file_matches:
          if self.collect_local(file_name):
            collected_files.append(file_name)
          else:
            return False
    self.infile_list = collected_files
    return True

  def get_csv(self, column, groupby=None):
    if groupby:
      column = groupby + '.' + column
    if column in self.column_csv_map.keys():
      return self.column_csv_map[column]
    col = naarad.utils.sanitize_string(column)
    csv = os.path.join(self.resource_directory, self.label + '.' + col + '.csv')
    self.csv_column_map[csv] = column
    self.column_csv_map[column] = csv
    return csv

  def get_important_sub_metrics_csv(self):
    csv = os.path.join(self.resource_directory, self.label + '.important_sub_metrics.csv')
    return csv

  def get_stats_csv(self):
    csv = os.path.join(self.resource_directory, self.label + '.stats.csv')
    return csv

  def get_percentiles_csv_from_data_csv(self, data_csv):
    percentile_csv_file = '.'.join(data_csv.split('.')[0:-1]) + '.percentiles.csv'
    return percentile_csv_file

  def get_sla_csv(self):
    csv = os.path.join(self.resource_directory, self.label + '.sla.csv')
    return csv

  def update_summary_stats(self, column):
    for stat in self.summary_stats_list:
      if stat.startswith('p'):
        self.summary_stats[column][stat] = naarad.utils.normalize_float_for_display(self.calculated_percentiles[column][int(stat[1:])])
      else:
        self.summary_stats[column][stat] = naarad.utils.normalize_float_for_display(self.calculated_stats[column][stat])

  def get_aggregation_timestamp(self, timestamp, granularity='second'):
    """
    Return a timestamp from the raw epoch time based on the granularity preferences passed in.

    :param string timestamp: timestamp from the log line
    :param string granularity: aggregation granularity used for plots.
    :return: string aggregate_timestamp: timestamp used for metrics aggregation in all functions
    """
    if granularity == 'hour':
      return (int(timestamp)/(3600*1000)) * 3600 * 1000, 3600
    elif granularity == 'minute':
      return (int(timestamp)/(60*1000)) * 60 * 1000, 60
    else:
      return (int(timestamp)/1000) * 1000, 1

  def aggregate_count_over_time(self, metric_store, groupby_name, aggregate_timestamp):
    """
    Organize and store the count of data from the log line into the metric store by columnm, group name, timestamp

    :param dict metric_store: The metric store used to store all the parsed the log data
    :param string groupby_name: the group name that the log line belongs to
    :param string aggregate_timestamp: timestamp used for storing the raw data. This accounts for aggregation time period
    :return: None
    """
    all_qps = metric_store['qps']
    qps = all_qps[groupby_name]
    if aggregate_timestamp in qps:
      qps[aggregate_timestamp] += 1
    else:
      qps[aggregate_timestamp] = 1
    return None

  def aggregate_values_over_time(self, metric_store, data, groupby_name, column_name, aggregate_timestamp):
    """
    Organize and store the data from the log line into the metric store by metric type, transaction, timestamp

    :param dict metric_store: The metric store used to store all the parsed log data
    :param string data: column data in the log line
    :param string groupby_name: the group that the data belongs to
    :param string column_name: the column name of the data
    :param string aggregate_timestamp: timestamp used for storing the raw data. This accounts for aggregation time period
    :return: None
    """
    # To add overall_summary one
    if self.groupby:
      metric_data = reduce(defaultdict.__getitem__, [column_name, 'Overall_summary', aggregate_timestamp], metric_store)
      metric_data.append(float(data))
    metric_data = reduce(defaultdict.__getitem__, [column_name, groupby_name, aggregate_timestamp], metric_store)
    metric_data.append(float(data))
    return None

  def average_values_for_plot(self, metric_store, data, averaging_factor):
    """
    Create the time series for the various metrics, averaged over the aggregation period being used for plots

    :param dict metric_store: The metric store used to store all the parsed log data
    :param dict data: Dict with all the metric data to be output to csv
    :param float averaging_factor: averaging factor to be used for calculating the average per second metrics
    :return: None
    """
    for column, groups_store in metric_store.items():
      for group, time_store in groups_store.items():
        for time_stamp, column_data in sorted(time_store.items()):
          if column in ['qps']:
            if self.groupby:
              data[self.get_csv(column, group)].append(','.join([str(time_stamp), str(column_data/float(averaging_factor))]))
            else:
              data[self.get_csv(column)].append(','.join([str(time_stamp), str(column_data/float(averaging_factor))]))
          else:
            if self.groupby:
              data[self.get_csv(column, group)].append(','.join([str(time_stamp), str(sum(map(float, column_data))/float(len(column_data)))]))
            else:
              data[self.get_csv(column)].append(','.join([str(time_stamp), str(sum(map(float, column_data))/float(len(column_data)))]))
    return None

  def parse(self):
    processed_data = defaultdict(lambda : defaultdict(lambda : defaultdict(list)))
    data = defaultdict(list)
    groupby_idxes = None
    averaging_factor = None
    if self.groupby:
      groupby_idxes = self.get_groupby_indexes(self.groupby)
    for input_file in self.infile_list:
      logger.info("Working on " + input_file)
      timestamp_format = None
      with open(input_file, 'r') as infile:
        for line in infile:
          if self.sep is None or self.sep == '':
            words = line.strip().split()
          else:
            words = line.strip().split(self.sep)
          if len(words) == 0:
            continue
          if len(words) <= len(self.columns): #NOTE: len(self.columns) is always one less than len(words) since we assume the very first column is timestamp
            logger.warning("WARNING: Number of columns given in config is more than number of columns present in line {0}\n", line)
            continue
          if not timestamp_format or timestamp_format == 'unknown':
            timestamp_format = naarad.utils.detect_timestamp_format(words[0])
          if timestamp_format == 'unknown':
            continue
          ts = naarad.utils.get_standardized_timestamp(words[0], timestamp_format)
          if ts == -1:
            continue
          ts = naarad.utils.reconcile_timezones(ts, self.timezone, self.graph_timezone)
          if self.ts_out_of_range(ts):
            continue
          if self.groupby:
            groupby_names = None
            for index in groupby_idxes:
              if not groupby_names:
                groupby_names = words[index].rstrip(':')
              else:
                groupby_names += '.' + words[index].rstrip(':')
            aggregate_timestamp, averaging_factor = self.get_aggregation_timestamp(ts, self.aggregation_granularity)
            self.aggregate_count_over_time(processed_data, groupby_names, aggregate_timestamp)
            for i in range(len(self.columns)):
              if i+1 in groupby_idxes:
                continue
              else:
                self.aggregate_values_over_time(processed_data, words[i+1], groupby_names, self.columns[i], aggregate_timestamp)
          else:
            groupby_names = 'DEFAULT'
            aggregate_timestamp, averaging_factor = self.get_aggregation_timestamp(ts, self.aggregation_granularity)
            self.aggregate_count_over_time(processed_data, groupby_names, aggregate_timestamp)
            for i in range(len(self.columns)):
              self.aggregate_values_over_time(processed_data, words[i+1], groupby_names, self.columns[i], aggregate_timestamp)
    # Post processing, putting data in csv files
    self.average_values_for_plot(processed_data, data, averaging_factor)
    for csv in data.keys():
      self.csv_files.append(csv)
      with open(csv, 'w') as fh:
        fh.write('\n'.join(sorted(data[csv])))
    self.calc_key_stats(processed_data)
    return True

  def calc_key_stats(self, metric_store):
    """
    Calculate stats such as percentile and mean

    :param dict metric_store: The metric store used to store all the parsed log data
    :return: None
    """
    stats_to_calculate = ['mean', 'std', 'min', 'max']  # TODO: get input from user
    percentiles_to_calculate = range(0, 100, 1)  # TODO: get input from user
    for column, groups_store in metric_store.items():
      for group, time_store in groups_store.items():
        data = metric_store[column][group].values()
        if self.groupby:
          column = group + '.' + column
        if column.startswith('qps'):
          self.calculated_stats[column], self.calculated_percentiles[column] = naarad.utils.calculate_stats(data, stats_to_calculate, percentiles_to_calculate)
        else:
          self.calculated_stats[column], self.calculated_percentiles[column] = naarad.utils.calculate_stats(list(heapq.merge(*data)), stats_to_calculate, percentiles_to_calculate)
        self.update_summary_stats(column)

  def calculate_stats(self):
    """
    Calculate stats with different function depending on the metric type:
    Data is recorded in memory for base metric type, and use calculate_base_metric_stats()
    Data is recorded in CSV file for other metric types, and use calculate_other_metric_stats()

    """
    metric_type = self.metric_type.split('-')[0]
    if metric_type in naarad.naarad_imports.metric_classes or metric_type in naarad.naarad_imports.aggregate_metric_classes:
      self.calculate_other_metric_stats()
    else:
      self.calculate_base_metric_stats()

  def calculate_base_metric_stats(self):
    stats_to_calculate = ['mean', 'std', 'min', 'max']  # TODO: get input from user
    percentiles_to_calculate = range(0, 101, 1)  # TODO: get input from user
    headers = CONSTANTS.SUBMETRIC_HEADER + ',mean,std,p50,p75,p90,p95,p99,min,max\n'  # TODO: This will be built from user input later on
    metric_stats_csv_file = self.get_stats_csv()
    imp_metric_stats_csv_file = self.get_important_sub_metrics_csv()
    imp_metric_stats_present = False
    metric_stats_present = False
    logger.info("Calculating stats for important sub-metrics in %s and all sub-metrics in %s", imp_metric_stats_csv_file, metric_stats_csv_file)
    with open(metric_stats_csv_file,'w') as FH:
      with open(imp_metric_stats_csv_file, 'w') as FH_IMP:
        FH.write(headers)
        FH_IMP.write(headers)
        for sub_metric in self.calculated_stats:
          percentile_data = self.calculated_percentiles[sub_metric]
          stats_data = self.calculated_stats[sub_metric]
          csv_data = ','.join([sub_metric] + map(lambda x: str(round(x, 2)), [stats_data['mean'], stats_data['std'],
                                                                              percentile_data[50], percentile_data[75],
                                                                              percentile_data[90], percentile_data[95],
                                                                              percentile_data[99], stats_data['min'],
                                                                              stats_data['max']]))
          FH.write(csv_data + '\n')
          if self.important_sub_metrics is not None and sub_metric in self.important_sub_metrics:
            FH_IMP.write(csv_data + '\n')
        self.stats_files.append(metric_stats_csv_file)
        self.important_stats_files.append(imp_metric_stats_csv_file)
    for column in self.calculated_percentiles:
      csv_file = self.column_csv_map[column]
      percentiles_csv_file = self.get_percentiles_csv_from_data_csv(csv_file)
      percentile_data = self.calculated_percentiles[column]
      with open(percentiles_csv_file,'w') as FH:
        for percentile in sorted(percentile_data):
          FH.write(str(percentile) + ',' + str(round(percentile_data[percentile],2)) + '\n')
        self.percentiles_files.append(percentiles_csv_file)

  def calculate_other_metric_stats(self):
    stats_to_calculate = ['mean', 'std', 'min', 'max']  # TODO: get input from user
    percentiles_to_calculate = range(0, 101, 1)  # TODO: get input from user
    headers = CONSTANTS.SUBMETRIC_HEADER + ',mean,std,p50,p75,p90,p95,p99,min,max\n'  # TODO: This will be built from user input later on
    metric_stats_csv_file = self.get_stats_csv()
    imp_metric_stats_csv_file = self.get_important_sub_metrics_csv()
    imp_metric_stats_present = False
    metric_stats_present = False
    logger.info("Calculating stats for important sub-metrics in %s and all sub-metrics in %s", imp_metric_stats_csv_file, metric_stats_csv_file)
    with open(metric_stats_csv_file, 'w') as FH_W:
      with open(imp_metric_stats_csv_file, 'w') as FH_W_IMP:
        for csv_file in self.csv_files:
          data = []
          value_error = False
          if not os.path.getsize(csv_file):
            continue
          column = self.csv_column_map[csv_file]
          percentile_csv_file = self.get_percentiles_csv_from_data_csv(csv_file)
          with open(csv_file, 'r') as FH:
            for line in FH:
              words = line.split(',')
              try:
                data.append(float(words[1]))
              except ValueError:
                if not value_error:
                  logger.error("Cannot convert to float. Some data is ignored in file " + csv_file)
                  value_error = True
                continue
          self.calculated_stats[column], self.calculated_percentiles[column] = naarad.utils.calculate_stats(data, stats_to_calculate, percentiles_to_calculate)
          with open(percentile_csv_file, 'w') as FH_P:
            for percentile in sorted(self.calculated_percentiles[column].iterkeys()):
              FH_P.write("%d, %f\n" % (percentile, self.calculated_percentiles[column][percentile]))
          self.percentiles_files.append(percentile_csv_file)
          self.update_summary_stats(column)
          to_write = [column, self.calculated_stats[column]['mean'], self.calculated_stats[column]['std'], self.calculated_percentiles[column][50], self.calculated_percentiles[column][75], self.calculated_percentiles[column][90], self.calculated_percentiles[column][95], self.calculated_percentiles[column][99], self.calculated_stats[column]['min'], self.calculated_stats[column]['max']]
          to_write = map(lambda x: naarad.utils.normalize_float_for_display(x), to_write)
          if not metric_stats_present:
            metric_stats_present = True
            FH_W.write(headers)
          FH_W.write(','.join(to_write) + '\n')
          # Important sub-metrics and their stats go in imp_metric_stats_csv_file
          sub_metric = column
          if self.metric_type in self.device_types:
            sub_metric = column.split('.')[1]
          if self.important_sub_metrics and sub_metric in self.important_sub_metrics:
            if not imp_metric_stats_present:
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

  def plot_timeseries(self, graphing_library = 'matplotlib'):
    """
    plot timeseries for sub-metrics
    """
    if self.groupby:
      plot_data = {}
      # plot time series data for submetrics
      for out_csv in sorted(self.csv_files, reverse=True):
        csv_filename = os.path.basename(out_csv)
        transaction_name = ".".join(csv_filename.split('.')[1:-1])
        if transaction_name in self.anomalies.keys():
          highlight_regions = self.anomalies[transaction_name]
        else:
          highlight_regions = None
        # The last element is .csv, don't need that in the name of the chart
        column = csv_filename.split('.')[-2]
        transaction_name = ' '.join(csv_filename.split('.')[1:-2])
        plot = PD(input_csv=out_csv, csv_column=1, series_name=transaction_name + '.' + column, y_label=column + ' (' + self.sub_metric_description[column] + ')', precision=None, graph_height=500, graph_width=1200, graph_type='line', highlight_regions=highlight_regions)
        if transaction_name in plot_data:
          plot_data[transaction_name].append(plot)
        else:
          plot_data[transaction_name] = [plot]
      for transaction in plot_data:
        graphed, div_file = Metric.graphing_modules[graphing_library].graph_data(plot_data[transaction], self.resource_directory, self.resource_path, self.label + '.' + transaction )
        if graphed:
          self.plot_files.append(div_file)
    else:
      graphed = False
      for out_csv in self.csv_files:
        csv_filename = os.path.basename(out_csv)
        transaction_name = ".".join(csv_filename.split('.')[1:-1])
        if transaction_name in self.anomalies.keys():
          highlight_regions = self.anomalies[transaction_name]
        else:
          highlight_regions = None
        # The last element is .csv, don't need that in the name of the chart
        column = self.csv_column_map[out_csv]
        column = naarad.utils.sanitize_string(column)
        graph_title = '.'.join(csv_filename.split('.')[0:-1])
        if self.sub_metric_description and column in self.sub_metric_description.keys():
          graph_title += ' ('+self.sub_metric_description[column]+')'
        if self.sub_metric_unit and column in self.sub_metric_unit.keys():
          plot_data = [PD(input_csv=out_csv, csv_column=1, series_name=graph_title, y_label=column +' ('+ self.sub_metric_unit[column]+')', precision=None, graph_height=600, graph_width=1200, graph_type='line', highlight_regions=highlight_regions)]
        else:
          plot_data = [PD(input_csv=out_csv, csv_column=1, series_name=graph_title, y_label=column, precision=None, graph_height=600, graph_width=1200, graph_type='line', highlight_regions=highlight_regions)]
        graphed, div_file = Metric.graphing_modules[graphing_library].graph_data(plot_data, self.resource_directory, self.resource_path, graph_title)
        if graphed:
          self.plot_files.append(div_file)
    return True

  def check_important_sub_metrics(self, sub_metric):
    """
    check whether the given sub metric is in important_sub_metrics list
    """
    if not self.important_sub_metrics:
      return False
    if sub_metric in self.important_sub_metrics:
      return True
    items = sub_metric.split('.')
    if items[-1] in self.important_sub_metrics:
      return True
    return False

  def plot_cdf(self, graphing_library = 'matplotlib'):
    """
    plot CDF for important sub-metrics
    """
    graphed = False
    for percentile_csv in self.percentiles_files:
      csv_filename = os.path.basename(percentile_csv)
      # The last element is .csv, don't need that in the name of the chart
      column = self.csv_column_map[percentile_csv.replace(".percentiles.", ".")]
      if not self.check_important_sub_metrics(column):
        continue
      column = naarad.utils.sanitize_string(column)
      graph_title = '.'.join(csv_filename.split('.')[0:-1])
      if self.sub_metric_description and column in self.sub_metric_description.keys():
        graph_title += ' ('+self.sub_metric_description[column]+')'
      if self.sub_metric_unit and column in self.sub_metric_unit.keys():
        plot_data = [PD(input_csv=percentile_csv, csv_column=1, series_name=graph_title, x_label='Percentiles', y_label=column +' ('+ self.sub_metric_unit[column]+')', precision=None, graph_height=600, graph_width=1200, graph_type='line')]
      else:
        plot_data = [PD(input_csv=percentile_csv, csv_column=1, series_name=graph_title, x_label='Percentiles', y_label=column, precision=None, graph_height=600, graph_width=1200, graph_type='line')]
      graphed, div_file = Metric.graphing_modules[graphing_library].graph_data_on_the_same_graph(plot_data, self.resource_directory, self.resource_path, graph_title)
      if graphed:
        self.plot_files.append(div_file)
    return True

  def graph(self, graphing_library = 'matplotlib'):
    """
    graph generates two types of graphs
    'time': generate a time-series plot for all submetrics (the x-axis is a time series)
    'cdf': generate a CDF plot for important submetrics (the x-axis shows percentiles)
    """
    logger.info('Using graphing_library {lib} for metric {name}'.format(lib=graphing_library, name=self.label))
    self.plot_cdf(graphing_library)
    self.plot_timeseries(graphing_library)
    return True

  def detect_anomaly(self):
    """
    Detect anomalies in the timeseries data for the submetrics specified in the config file. Identified anomalies are
    stored in self.anomalies as well as written to .anomalies.csv file to be used by the client charting page. Anomaly
    detection uses the luminol library (http://pypi.python.org/pypi/luminol)
    """
    if not self.anomaly_detection_metrics or len(self.anomaly_detection_metrics) <= 0:
      return
    for submetric in self.anomaly_detection_metrics:
      csv_file = self.get_csv(submetric)
      if naarad.utils.is_valid_file(csv_file):
        detector = anomaly_detector.AnomalyDetector(csv_file)
        anomalies = detector.get_anomalies()
        if len(anomalies) <= 0:
          return
        self.anomalies[submetric] = anomalies
        anomaly_csv_file = os.path.join(self.resource_directory, self.label + '.' + submetric + '.anomalies.csv')
        with open(anomaly_csv_file, 'w') as FH:
          for anomaly in anomalies:
            FH.write(",".join([str(anomaly.anomaly_score), str(anomaly.start_timestamp), str(anomaly.end_timestamp), str(anomaly.exact_timestamp)]))
            FH.write('\n')
