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
from naarad.metrics.metric import Metric
from naarad.graphing.plot_data import PlotData as PD
import naarad.utils
import naarad.naarad_imports


logger = logging.getLogger('naarad.metrics.JmeterMetric')

class JmeterMetric(Metric):
  def __init__ (self, metric_type, infile, hostname, output_directory, label, ts_start, ts_end, **other_options):
    Metric.__init__(self, metric_type, infile, hostname, output_directory, label, ts_start, ts_end)
    self.metric_description = {
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
    self.metric_units = {
      'lt': 'ms',
      'ResponseTime': 'ms',
      'ResponseSize': 'bytes',
      'qps': 'qps',
      'DataThroughput': 'mbps',
      'ErrorsPerSecond': 'qps'
    }
    self.calculated_stats = {}
    #self.csv_files = []
    #self.plot_files = []
    #self.stats_files = []
    #self.important_stats_files = []
    #self.percentiles_files = []
    self.calculated_percentiles = {}
    self.important_sub_metrics = naarad.naarad_imports.important_sub_metrics_import['JMETER']

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
    csv = os.path.join(self.outdir, self.metric_type + '.' + transaction_name + '.' + col + '.csv')
    self.csv_column_map[csv] = column
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
            data[self.get_csv(transaction, metric)].append(','.join([time_stamp, str(sum(map(float,metric_data))/float(len(metric_data)))]))
            if metric == 'by':
              data[self.get_csv(transaction, 'thr')].append(','.join([time_stamp, str(sum(map(float,metric_data))/float(averaging_factor * 1024 * 1024 / 8.0))]))
          elif metric in ['qps', 'eqps']:
            data[self.get_csv(transaction, metric)].append(','.join([time_stamp, str(metric_data/float(averaging_factor))]))
    return None

  def get_all_response_times(self, metric_store):
    """
    Return a list of all the response time values by transaction.

    :param dict metric_store: The metric store used to store all the parsed jmeter log data
    :return: dict {transaction : response time values list}
    """
    response_store = metric_store['t']
    response_list = defaultdict(list)
    for transaction, time_store in response_store.items():
      for time_stamp in time_store:
        response_list[transaction].extend(time_store[time_stamp])
    return response_list

  def get_aggregation_timestamp(self, timestamp, granularity='minute'):
    """
    Return a timestamp from the raw epoch time based on the granularity preferences passed in.

    :param string timestamp: raw epoch timestamp from the jmeter log line
    :param string granularity: aggregation granularity used for plots.
    :return: string aggregate_timestamp that will be used for metrics aggregation in all functions for JmeterMetric
    """
    if granularity == 'hour':
      return datetime.datetime.utcfromtimestamp(int(timestamp) / 1000).strftime('%Y-%m-%d %H') + ':00:00', 3600
    elif granularity == 'minute':
      return datetime.datetime.utcfromtimestamp(int(timestamp) / 1000).strftime('%Y-%m-%d %H:%M') + ':00', 60
    else:
      return datetime.datetime.utcfromtimestamp(int(timestamp) / 1000).strftime('%Y-%m-%d %H:%M:%S'), 1

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
    raw_response_times = self.get_all_response_times(metric_store)
    stats_to_calculate = ['mean', 'std', 'median', 'min', 'max'] # TODO: get input from user
    percentiles_to_calculate = range(5,101,5) # TODO: get input from user
    percentiles_to_calculate.append(99)
    for transaction in raw_response_times:
      self.calculated_stats[transaction], self.calculated_percentiles[transaction] = naarad.utils.calculate_stats(raw_response_times[transaction], stats_to_calculate, percentiles_to_calculate)
    return None

  def parse(self):
    """
    Parse the Jmeter file and calculate key stats

    :return: status of the metric parse
    """
    logger.info('Processing : %s',self.infile)
    file_status = naarad.utils.is_valid_file(self.infile)
    if not file_status:
      return False
    # TBD: Read from user configuration
    status = self.parse_xml_jtl('minute')
    gc.collect()
    return status

  def parse_xml_jtl(self, granularity):
    """
    Parse Jmeter workload output in XML format and extract overall and per transaction data and key statistics

    :param string granularity: The time period over which to aggregate and average the raw data. Valid values are 'hour', 'minute' or 'second'
    :return: status of the metric parse
    """
    with open(self.infile) as infile:
      data = defaultdict(list)
      processed_data = defaultdict(lambda : defaultdict(lambda : defaultdict(list)))

      line_regex = re.compile(r' (lb|ts|t|by|s)="([^"]+)"')
      for line in infile:
        if '<httpSample' not in line:
          continue
        line_data = dict(re.findall(line_regex, line))
        aggregate_timestamp, averaging_factor = self.get_aggregation_timestamp(line_data['ts'], granularity)
        self.aggregate_count_over_time(processed_data, line_data, [line_data['lb'], '__overall_summary__'], aggregate_timestamp)
        self.aggregate_values_over_time(processed_data, line_data, [line_data['lb'], '__overall_summary__'], ['t', 'by'], aggregate_timestamp)
      logger.info('Finished parsing : %s', self.infile)

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
    stats_csv = os.path.join(self.outdir, self.metric_type + '.stats.csv')
    csv_header = 'sub_metric,mean,std. deviation,median,min,max,90%,95%,99%\n'

    with open(stats_csv,'w') as FH:
      FH.write(csv_header)
      for sub_metric in self.calculated_stats:
        percentile_data = self.calculated_percentiles[sub_metric]
        stats_data = self.calculated_stats[sub_metric]
        if sub_metric == '__overall_summary__':
          sub_metric = 'Overall_Summary'
        csv_data = ','.join([sub_metric,str(numpy.round_(stats_data['mean'], 2)),str(numpy.round_(stats_data['std'], 2)),str(numpy.round_(stats_data['median'], 2)),str(numpy.round_(stats_data['min'], 2)),str(numpy.round_(stats_data['max'], 2)),str(numpy.round_(percentile_data[90], 2)),str(numpy.round_(percentile_data[95], 2)),str(numpy.round_(percentile_data[99], 2))])
        FH.write(csv_data + '\n')
      self.stats_files.append(stats_csv)

    for sub_metric in self.calculated_percentiles:
      percentiles_csv = self.get_csv(sub_metric,'percentiles')
      percentile_data = self.calculated_percentiles[sub_metric]
      with open(percentiles_csv,'w') as FH:
        for percentile in sorted(percentile_data):
          FH.write(str(percentile) + ',' + str(numpy.round_(percentile_data[percentile],2)) + '\n')
        self.percentiles_files.append(percentiles_csv)

  def graph(self, graphing_library='matplotlib'):
    if graphing_library != 'matplotlib':
     return Metric.graph(self, graphing_library)
    else:
      html_string = []
      html_string.append('<h2>Metric: {0}</h2>\n'.format(self.metric_type))
      logger.info('Using graphing_library {lib} for metric {name}'.format(lib=graphing_library, name=self.label))
      plot_data = {}
      for out_csv in sorted(self.csv_files, reverse=True):
        csv_filename = os.path.basename(out_csv)
        # The last element is .csv, don't need that in the name of the chart
        column = csv_filename.split('.')[-2]
        transaction_name = ' '.join(csv_filename.split('.')[1:-2])
        plot = PD(input_csv=out_csv, csv_column=1, series_name=transaction_name, y_label=self.metric_description[column] + ' (' + self.metric_units[column] + ')', precision=None, graph_height=500, graph_width=1200, graph_type='line')
        if transaction_name in plot_data:
          plot_data[transaction_name].append(plot)
        else:
          plot_data[transaction_name] = [plot]
      for transaction in plot_data:
        graphed, div_file = Metric.graphing_modules[graphing_library].graph_data(plot_data[transaction], self.outdir, self.metric_type + '.' + transaction )
        if graphed:
          self.plot_files.append(div_file)
      return True
