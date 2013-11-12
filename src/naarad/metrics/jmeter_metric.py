# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
import logging
import os
import re
import mmap
from naarad.metrics.metric import Metric
from naarad.graphing.plot_data import PlotData as PD
import naarad.utils


logger = logging.getLogger('naarad.metrics.JmeterMetric')

class JmeterMetric(Metric):
  def __init__ (self, metric_type, infile, access, output_directory, label, ts_start, ts_end, **other_options):
    Metric.__init__(self, metric_type, infile, access, output_directory, label, ts_start, ts_end)
    self.metric_description = {
      'lb': 'Transaction Name',
      'lt': 'Time to First byte',
      'ts': 'Timestamp',
      'tn': 'Transaction Name (Parent)',
      's': 'Status',
      't': 'Response Time',
      'rc': 'Response Code',
      'rm': 'Response Message',
      'dt': 'Data Type',
      'by': 'Response Size',
      'qps': 'Successful Transactions per second',
      'eqps': 'Errors per second',
      'thr': 'Data Throughput'
    }
    self.metric_units = {
      'lt': 'ms',
      't': 'ms',
      'by': 'bytes',
      'qps': 'qps',
      'thr': 'mbps',
      'eqps': 'qps'
    }

  def get_csv(self, transaction_name, column):
    col = naarad.utils.sanitize_string(column)
    csv = os.path.join(self.outdir, self.metric_type + '.' + transaction_name + '.' + col + '.csv')
    return csv

  def calculate_average_qps_over_minute(self, success_qps, error_qps, line_data):
    aggregate_timestamp = naarad.utils.convert_unix_ms_to_utc_no_seconds(line_data['ts']) + ':00'
    if line_data['s'] == 'true':
      all_qps = success_qps
    else:
      all_qps = error_qps
    transaction = line_data['lb']
    if transaction in all_qps:
      qps = all_qps[transaction]
    else:
      all_qps[transaction] = {}
      qps = all_qps[transaction]
    if aggregate_timestamp in qps:
      qps[aggregate_timestamp] += 1
    else:
      qps[aggregate_timestamp] = 1
    return None

  def aggregate_values_over_time(self, metric_store, line_data, metric, time_period='minute'):
    transaction = line_data['lb']
    if time_period == 'hour':
      aggregate_timestamp = naarad.utils.convert_unix_ms_to_utc_no_minutes(line_data['ts']) + ':00:00'
    elif time_period == 'minute':
      aggregate_timestamp = naarad.utils.convert_unix_ms_to_utc_no_seconds(line_data['ts']) + ':00'
    elif time_period == 'second':
      aggregate_timestamp = naarad.utils.convert_unix_ms_to_utc(line_data['ts'])
    if transaction in metric_store:
      metric_series = metric_store[transaction]
    else:
      metric_store[transaction] = {}
      metric_series = metric_store[transaction]
    if aggregate_timestamp in metric_series:
      metric_data = metric_series[aggregate_timestamp]
      metric_data.append(line_data[metric])
    else:
      metric_series[aggregate_timestamp] = []
      metric_data = metric_series[aggregate_timestamp]
      metric_data.append(line_data[metric])
    return None

  def parse(self):
    logger.info('Processing : %s',self.infile)
    file_status, error_message = naarad.utils.is_valid_file(self.infile)
    if not file_status:
      return False
    status = self.faster_parse()
    return status

  def faster_parse(self):
    with open(self.infile) as infile:
      mm = mmap.mmap(fileno=infile.fileno(), length=0, access=mmap.PROT_READ)

      data = {}
      success_qps = {}
      error_qps = {}
      response_times = {}
      response_sizes = {}
#      line_regex = re.compile(r'([a-z]+)="([^"]+)"')
      line_regex = re.compile(r' (lb|ts|t|by|lt|s)="([^"]+)"')
      while True:
        line = mm.readline()
        if line == '':
          break

        if '<httpSample' not in line:
          continue
        line_data = dict(re.findall(line_regex, line))

        self.calculate_average_qps_over_minute(success_qps, error_qps, line_data)
        self.aggregate_values_over_time(response_times,line_data,'t','minute')
        self.aggregate_values_over_time(response_sizes,line_data,'by','minute')
      mm.close()
      logger.info('Finished parsing : %s', self.infile)
      logger.info('Processing response times')
      for transaction in response_times:
        data[self.get_csv(transaction, 't')] = []
        rtimes = response_times[transaction]
        for time_stamp in sorted(rtimes):
          response_list = rtimes[time_stamp]
          data[self.get_csv(transaction, 't')].append(time_stamp + ',' + str(sum(map(float,response_list))/float(len(response_list))))

      logger.info('Processing response size and data throughput')
      for transaction in response_sizes:
        data[self.get_csv(transaction, 'by')] = []
        data[self.get_csv(transaction, 'thr')] = []
        rsizes = response_sizes[transaction]
        for time_stamp in sorted(rsizes):
          response_list = rsizes[time_stamp]
          data[self.get_csv(transaction, 'by')].append(time_stamp + ',' + str(sum(map(float,response_list))/float(len(response_list))))
          data[self.get_csv(transaction, 'thr')].append(time_stamp + ',' + str(sum(map(float,response_list))/(60.0 * 1024 *1024/8)))

      logger.info('Processing Successful qps')
      for transaction in success_qps:
        data[self.get_csv(transaction, 'qps')] = []
        qps = success_qps[transaction]
        for time_stamp in sorted(qps):
          data[self.get_csv(transaction, 'qps')].append(time_stamp + ',' +  str(qps[time_stamp]/60))

      logger.info('Processing Error qps')
      for transaction in error_qps:
        data[self.get_csv(transaction, 'eqps')] = []
        qps = error_qps[transaction]
        for time_stamp in sorted(qps):
          data[self.get_csv(transaction, 'eqps')].append(time_stamp + ',' +  str(qps[time_stamp]/60))

      for csv in data.keys():
        self.csv_files.append(csv)
        with open(csv, 'w') as csvf:
          csvf.write('\n'.join(sorted(data[csv])))

    return True

  def fast_parse(self):
    with open(self.infile) as infile:
      data = {}
      success_qps = {}
      error_qps = {}
      response_times = {}
      response_sizes = {}
      for line in infile:
        if '<httpSample' not in line:
          continue
        line_data = dict(re.findall(r'([a-z]+)="([^"]+)"', line))

        self.calculate_average_qps_over_minute(success_qps, error_qps, line_data)
        self.aggregate_values_over_time(response_times,line_data,'t','minute')
        self.aggregate_values_over_time(response_sizes,line_data,'by','minute')

      logger.info('Finished parsing : %s', self.infile)
      logger.info('Processing response times')
      for transaction in response_times:
        data[self.get_csv(transaction, 't')] = []
        rtimes = response_times[transaction]
        for time_stamp in sorted(rtimes):
          response_list = rtimes[time_stamp]
          data[self.get_csv(transaction, 't')].append(time_stamp + ',' + str(sum(map(float,response_list))/float(len(response_list))))

      logger.info('Processing response size and data throughput')
      for transaction in response_sizes:
        data[self.get_csv(transaction, 'by')] = []
        data[self.get_csv(transaction, 'thr')] = []
        rsizes = response_sizes[transaction]
        for time_stamp in sorted(rsizes):
          response_list = rsizes[time_stamp]
          data[self.get_csv(transaction, 'by')].append(time_stamp + ',' + str(sum(map(float,response_list))/float(len(response_list))))
          data[self.get_csv(transaction, 'thr')].append(time_stamp + ',' + str(sum(map(float,response_list))/(60.0 * 1024 *1024/8)))

      logger.info('Processing Successful qps')
      for transaction in success_qps:
        data[self.get_csv(transaction, 'qps')] = []
        qps = success_qps[transaction]
        for time_stamp in sorted(qps):
          data[self.get_csv(transaction, 'qps')].append(time_stamp + ',' +  str(qps[time_stamp]/60))

      logger.info('Processing Error qps')
      for transaction in error_qps:
        data[self.get_csv(transaction, 'eqps')] = []
        qps = error_qps[transaction]
        for time_stamp in sorted(qps):
          data[self.get_csv(transaction, 'eqps')].append(time_stamp + ',' +  str(qps[time_stamp]/60))

      for csv in data.keys():
        self.csv_files.append(csv)
        with open(csv, 'w') as csvf:
          csvf.write('\n'.join(sorted(data[csv])))

    return True

  def graph(self, graphing_library = 'matplotlib'):
    html_string = []
    html_string.append('<h1>Metric: {0}</h1>\n'.format(self.metric_type))
    logger.info('Using graphing_library {lib} for metric {name}'.format(lib=graphing_library, name=self.label))
    plot_data = {}
    for out_csv in sorted(self.csv_files):
      csv_filename = os.path.basename(out_csv)
      # The last element is .csv, don't need that in the name of the chart
      column = csv_filename.split('.')[-2]
      transaction_name = ' '.join(csv_filename.split('.')[1:-2])
#      graph_title = transaction_name + ' ' +  self.metric_description[column]
#      image_prefix = '.'.join(csv_filename.split('.')[0:-1])
      plot = PD(input_csv=out_csv, csv_column=1, series_name=transaction_name, y_label=self.metric_description[column] + ' (' + self.metric_units[column] + ')', precision=None, graph_height=600, graph_width=1500, graph_type='line')
      if transaction_name in plot_data:
        plot_data[transaction_name].append(plot)
      else:
        plot_data[transaction_name] = [plot]
    for transaction in plot_data:
      graphed, html_ret = Metric.graphing_modules[graphing_library].graph_data(plot_data[transaction], self.outdir, transaction )
      if html_ret:
        html_string.append(html_ret)
      else:
        if graphed:
          img_tag = '<h3>{title}</h3><p><b>Description</b>: {description}</p><img src="{image_name}.png" />\n'.format(title=transaction, description='', image_name=transaction)
        else:
          img_tag = '<h3>{title}</h3><p><b>Description</b>: {description}</p>No data for this metric\n'.format(title=transaction, description='')
        html_string.append(img_tag)
    return '\n'.join(html_string)