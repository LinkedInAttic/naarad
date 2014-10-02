# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
from collections import defaultdict
import datetime
import gc
import logging
import os
import re
import numpy
import heapq
from naarad.metrics.metric import Metric
from naarad.graphing.plot_data import PlotData as PD
import naarad.utils
import naarad.naarad_imports
from naarad.naarad_constants import important_sub_metrics_import


logger = logging.getLogger('naarad.metrics.JmeterMetric')

class JmeterMetric(Metric):
  def __init__ (self, metric_type, infile_list, hostname, output_directory, resource_path, label, ts_start, ts_end,
                rule_strings, important_sub_metrics, anomaly_detection_metrics, **other_options):
    Metric.__init__(self, metric_type, infile_list, hostname, output_directory, resource_path, label, ts_start, ts_end,
                    rule_strings, important_sub_metrics, anomaly_detection_metrics)
    self.sub_metric_description = {
      'lb': 'Transaction Name',
      'lt': 'Time to First byte',
      'ts': 'Timestamp',
      'tn': 'Transaction Name (Parent)',
      's': 'Status',
      'ResponseTime': 'Response Time',
      'rc': 'Response Code',
      'rm': 'Response Message',
      'dt': 'Data Type',
      'ResponseSize': 'Response Size',
      'qps': 'Successful Transactions per second',
      'ErrorsPerSecond': 'Errors per second',
      'DataThroughput': 'Data Throughput'
    }
    self.sub_metric_units = {
      'lt': 'ms',
      'ResponseTime': 'ms',
      'ResponseSize': 'bytes',
      'qps': 'qps',
      'DataThroughput': 'mbps',
      'ErrorsPerSecond': 'qps'
    }
    self.calculated_stats = {}
    self.aggregation_granularity = 'second'
    self.calculated_percentiles = {}
    self.summary_stats = defaultdict(dict)
    self.summary_html_content_enabled = True
    self.summary_charts = [self.label + '.Overall_Summary.div']
    if not self.important_sub_metrics:
      self.important_sub_metrics = important_sub_metrics_import['JMETER']
    if other_options:
      for (key, val) in other_options.iteritems():
        setattr(self, key, val)



  def get_csv(self, transaction_name, column):
    col = naarad.utils.sanitize_string(column)
    if col == 't':
      col = 'ResponseTime'
    elif col == 'by':
      col = 'ResponseSize'
    elif col == 'thr':
      col = 'DataThroughput'
    elif col == 'eqps':
      col = 'ErrorsPerSecond'

    if transaction_name == '__overall_summary__':
      transaction_name = 'Overall_Summary'
    csv = os.path.join(self.resource_directory, self.label + '.' + transaction_name + '.' + col + '.csv')
    self.csv_column_map[csv] = transaction_name + '.' + col
    return csv

  def aggregate_count_over_time(self, metric_store, line_data, transaction_list, aggregate_timestamp):
    """
    Organize and store the count of data from the log line into the metric store by metric type, transaction, timestamp

    :param dict metric_store: The metric store used to store all the parsed jmeter log data
    :param dict line_data: dict with the extracted k:v from the log line
    :param list transaction_list: list of transaction to be used for storing the metrics from given line
    :param string aggregate_timestamp: timestamp used for storing the raw data. This accounts for aggregation time period
    :return: None
    """
    for transaction in transaction_list:
      if line_data['s'] == 'true':
        all_qps = metric_store['qps']
      else:
        all_qps = metric_store['eqps']
      qps = all_qps[transaction]
      if aggregate_timestamp in qps:
        qps[aggregate_timestamp] += 1
      else:
        qps[aggregate_timestamp] = 1
    return None

  def aggregate_values_over_time(self, metric_store, line_data, transaction_list, metric_list, aggregate_timestamp):
    """
    Organize and store the data from the log line into the metric store by metric type, transaction, timestamp

    :param dict metric_store: The metric store used to store all the parsed jmeter log data
    :param dict line_data: dict with the extracted k:v from the log line
    :param list transaction_list: list of transaction to be used for storing the metrics from given line
    :param list metric_list: list of metrics to extract from the log line
    :param string aggregate_timestamp: timestamp used for storing the raw data. This accounts for aggregation time period
    :return: None
    """
    for metric in metric_list:
      for transaction in transaction_list:
        metric_data = reduce(defaultdict.__getitem__,[metric, transaction, aggregate_timestamp], metric_store)
        metric_data.append(float(line_data[metric]))
    return None

  def average_values_for_plot(self, metric_store, data, averaging_factor):
    """
    Create the time series for the various metrics, averaged over the aggregation period being used for plots

    :param dict metric_store: The metric store used to store all the parsed jmeter log data
    :param dict data: Dict with all the metric data to be output to csv
    :param float averaging_factor: averaging factor to be used for calculating the average per second metrics
    :return: None
    """
    for metric, transaction_store in metric_store.items():
      for transaction, time_store in transaction_store.items():
        for time_stamp, metric_data in sorted(time_store.items()):
          if metric in ['t', 'by']:
            data[self.get_csv(transaction, metric)].append(','.join([str(time_stamp), str(sum(map(float,metric_data))/float(len(metric_data)))]))
            if metric == 'by':
              metric_store['thr'][transaction][time_stamp] = sum(map(float,metric_data))/float(averaging_factor * 1024 * 1024 / 8.0)
              data[self.get_csv(transaction, 'thr')].append(','.join([str(time_stamp), str(metric_store['thr'][transaction][time_stamp])]))
          elif metric in ['qps', 'eqps']:
            data[self.get_csv(transaction, metric)].append(','.join([str(time_stamp), str(metric_data/float(averaging_factor))]))
    return None

  def calculate_key_stats(self, metric_store):
    """
    Calculate key statistics for given data and store in the class variables calculated_stats and calculated_percentiles
    calculated_stats:
      'mean', 'std', 'median', 'min', 'max'
    calculated_percentiles:
      range(5,101,5), 99
    :param dict metric_store: The metric store used to store all the parsed jmeter log data
    :return: none
    """
    stats_to_calculate = ['mean', 'std', 'median', 'min', 'max'] # TODO: get input from user
    percentiles_to_calculate = range(5,101,5) # TODO: get input from user
    percentiles_to_calculate.append(99)
    for transaction in metric_store['t'].keys():
      transaction_key = transaction + '.' + 'ResponseTime'
      #For ResponseTime and ResponseSize, each timestamp has a list of values associated with it.
      #Using heapq.merge to merge all the lists into a single list to be passed to numpy.
      self.calculated_stats[transaction_key], self.calculated_percentiles[transaction_key] = \
        naarad.utils.calculate_stats(list(heapq.merge(*metric_store['t'][transaction].values())),
                                     stats_to_calculate, percentiles_to_calculate)
      self.update_summary_stats(transaction_key)
      transaction_key = transaction + '.' + 'qps'
      if len(metric_store['qps'][transaction].values()) > 0:
        self.calculated_stats[transaction_key], self.calculated_percentiles[transaction_key] = \
          naarad.utils.calculate_stats(metric_store['qps'][transaction].values(),
                                       stats_to_calculate, percentiles_to_calculate)
        self.update_summary_stats(transaction_key)
      transaction_key = transaction + '.' + 'ResponseSize'
      self.calculated_stats[transaction_key], self.calculated_percentiles[transaction_key] = \
        naarad.utils.calculate_stats(list(heapq.merge(*metric_store['by'][transaction].values())),
                                     stats_to_calculate, percentiles_to_calculate)
      self.update_summary_stats(transaction_key)
      if 'eqps' in metric_store.keys() and transaction in metric_store['eqps'].keys():
        transaction_key = transaction + '.' + 'ErrorsPerSecond'
        self.calculated_stats[transaction_key], self.calculated_percentiles[transaction_key] = \
          naarad.utils.calculate_stats(metric_store['eqps'][transaction].values(),
                                       stats_to_calculate, percentiles_to_calculate)
        self.update_summary_stats(transaction + '.' + 'ErrorsPerSecond')
      transaction_key = transaction + '.' + 'DataThroughput'
      self.calculated_stats[transaction_key], self.calculated_percentiles[transaction_key] = \
        naarad.utils.calculate_stats(metric_store['thr'][transaction].values(),
                                     stats_to_calculate, percentiles_to_calculate)
      self.update_summary_stats(transaction_key)
    return None

  def parse(self):
    """
    Parse the Jmeter file and calculate key stats

    :return: status of the metric parse
    """
    file_status = True
    for infile in self.infile_list:
      file_status = file_status and naarad.utils.is_valid_file(infile)
      if not file_status:
        return False

    status = self.parse_xml_jtl(self.aggregation_granularity)
    gc.collect()
    return status

  def _sanitize_label(self, raw_label):
    return raw_label.replace('/', '_').replace('?', '_')

  def parse_xml_jtl(self, granularity):
    """
    Parse Jmeter workload output in XML format and extract overall and per transaction data and key statistics

    :param string granularity: The time period over which to aggregate and average the raw data. Valid values are 'hour', 'minute' or 'second'
    :return: status of the metric parse
    """
    data = defaultdict(list)
    processed_data = defaultdict(lambda : defaultdict(lambda : defaultdict(list)))
    line_regex = re.compile(r' (lb|ts|t|by|s)="([^"]+)"')
    for input_file in self.infile_list:
      logger.info('Processing : %s', input_file)
      timestamp_format = None
      with open(input_file) as infile:
        for line in infile:
          if '<httpSample' not in line and '<sample' not in line:
            continue
          line_data = dict(re.findall(line_regex, line))
          if not timestamp_format or timestamp_format == 'unknown':
            timestamp_format = naarad.utils.detect_timestamp_format(line_data['ts'])
          if timestamp_format == 'unknown':
            continue
          ts = naarad.utils.get_standardized_timestamp(line_data['ts'], timestamp_format)
          if ts == -1:
            continue
          ts = naarad.utils.reconcile_timezones(ts, self.timezone, self.graph_timezone)
          aggregate_timestamp, averaging_factor = self.get_aggregation_timestamp(ts, granularity)
          self.aggregate_count_over_time(processed_data, line_data, [self._sanitize_label(line_data['lb']), 'Overall_Summary'], aggregate_timestamp)
          self.aggregate_values_over_time(processed_data, line_data, [self._sanitize_label(line_data['lb']), 'Overall_Summary'], ['t', 'by'], aggregate_timestamp)
        logger.info('Finished parsing : %s', input_file)
    logger.info('Processing metrics for output to csv')
    self.average_values_for_plot(processed_data, data, averaging_factor)
    logger.info('Writing time series csv')
    for csv in data.keys():
      self.csv_files.append(csv)
      with open(csv, 'w') as csvf:
        csvf.write('\n'.join(sorted(data[csv])))
    logger.info('Processing raw data for stats')
    self.calculate_key_stats(processed_data)
    return True

  def calculate_stats(self):
    stats_csv = self.get_stats_csv()
    imp_metric_stats_csv = self.get_important_sub_metrics_csv()
    csv_header = 'sub_metric,mean,std. deviation,median,min,max,90%,95%,99%\n'
    imp_csv_header = 'sub_metric,mean,std,p50,p75,p90,p95,p99,min,max\n'
    with open(stats_csv,'w') as FH:
      FH.write(csv_header)
      for sub_metric in self.calculated_stats:
        percentile_data = self.calculated_percentiles[sub_metric]
        stats_data = self.calculated_stats[sub_metric]
        csv_data = ','.join([sub_metric,str(round(stats_data['mean'], 2)),str(round(stats_data['std'], 2)),str(round(stats_data['median'], 2)),str(round(stats_data['min'], 2)),str(round(stats_data['max'], 2)),str(round(percentile_data[90], 2)),str(round(percentile_data[95], 2)),str(round(percentile_data[99], 2))])
        FH.write(csv_data + '\n')
      self.stats_files.append(stats_csv)
    for sub_metric in self.calculated_percentiles:
      percentiles_csv = self.get_csv(sub_metric,'percentiles')
      percentile_data = self.calculated_percentiles[sub_metric]
      with open(percentiles_csv,'w') as FH:
        for percentile in sorted(percentile_data):
          FH.write(str(percentile) + ',' + str(numpy.round_(percentile_data[percentile],2)) + '\n')
        self.percentiles_files.append(percentiles_csv)
    with open(imp_metric_stats_csv, 'w') as FH_IMP:
      FH_IMP.write(csv_header)
      for sub_metric in self.important_sub_metrics:
        if sub_metric in self.calculated_stats.keys():
          percentile_data = self.calculated_percentiles[sub_metric]
          stats_data = self.calculated_stats[sub_metric]
          csv_data = ','.join([sub_metric,str(round(stats_data['mean'], 2)),str(round(stats_data['std'], 2)),str(round(stats_data['median'], 2)),str(round(stats_data['min'], 2)),str(round(stats_data['max'], 2)),str(round(percentile_data[90], 2)),str(round(percentile_data[95], 2)),str(round(percentile_data[99], 2))])
          FH_IMP.write(csv_data + '\n')
      self.important_stats_files.append(imp_metric_stats_csv)

  def plot_timeseries(self, graphing_library='matplotlib'):
    if graphing_library != 'matplotlib':
     return Metric.plot_timeseries(self, graphing_library)
    else:
      logger.info('Using graphing_library {lib} for metric {name}'.format(lib=graphing_library, name=self.label))
      plot_data = {}
      # plot time series data for submetrics
      for out_csv in sorted(self.csv_files, reverse=True):
        csv_filename = os.path.basename(out_csv)
        # The last element is .csv, don't need that in the name of the chart
        column = csv_filename.split('.')[-2]
        transaction_name = ' '.join(csv_filename.split('.')[1:-2])
        plot = PD(input_csv=out_csv, csv_column=1, series_name=transaction_name, y_label=self.sub_metric_description[column] + ' (' + self.sub_metric_units[column] + ')', precision=None, graph_height=500, graph_width=1200, graph_type='line')
        if transaction_name in plot_data:
          plot_data[transaction_name].append(plot)
        else:
          plot_data[transaction_name] = [plot]
      for transaction in plot_data:
        graphed, div_file = Metric.graphing_modules[graphing_library].graph_data(plot_data[transaction], self.resource_directory, self.resource_path, self.label + '.' + transaction )
        if graphed:
          self.plot_files.append(div_file)
      return True
