# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
import logging
import os
from naarad.metrics.metric import Metric
from naarad.graphing.plot_data import PlotData as PD
import naarad.utils
import re

logger = logging.getLogger('naarad.metrics.JmeterMetric')

class JmeterMetric(Metric):
  def __init__ (self, metric_type, infile, access, output_directory, label, ts_start, ts_end, **other_options):
    Metric.__init__(self, metric_type, infile, access, output_directory, label, ts_start, ts_end)
    self.metric_description = {
      'lb' : 'Transaction Name',
      'lt' : 'Time to First byte',
      'ts' : 'Timestamp',
      'tn' : 'Transaction Name (Parent)',
      's' : 'Status',
      't' : 'Response Time',
      'rc' : 'Response Code',
      'rm' : 'Remarks',
      'dt' : 'Data Type',
      'by' : 'Response Size',
      'qps' : 'Transactions per second',
      'eps' : 'Errors per second'
    }
    self.metric_units = {
      'lt' : 'ms',
      't' : 'ms',
      'by' : 'bytes',
      'qps' : 'qps'
    }

  def get_csv(self, transaction_name, column):
    col = naarad.utils.sanitize_string(column)
    csv = os.path.join(self.outdir, self.metric_type + '.' + transaction_name + '.' + col + '.csv')
    return csv

  def calculate_average_qps_over_minute(self, all_qps, line_data):
    aggregate_timestamp = naarad.utils.convert_unix_ms_to_utc_no_seconds(line_data['ts']) + ':00'
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
    if time_period == 'minute':
      aggregate_timestamp = naarad.utils.convert_unix_ms_to_utc_no_seconds(line_data['ts']) + ':00'
    else:
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
    status = self.fast_parse()
    return status

  def fast_parse(self):
    with open(self.infile) as infile:
      data = {}
      success_qps = {}
      error_qps = {}
      response_times = {}
# Start of line-by-ling file processing
      for line in infile:
        if '<httpSample' not in line:
          continue
        line_data = dict(re.findall(r'([a-z]+)="([^"]+)"', line))
        actual_timestamp = naarad.utils.convert_unix_ms_to_utc(line_data['ts'])

        if line_data['s'] == 'true':
          self.calculate_average_qps_over_minute(success_qps, line_data)
        else:
          self.calculate_average_qps_over_minute(error_qps, line_data)

        self.aggregate_values_over_time(response_times,line_data,'t','minute')

###        metrics_to_extract = ['t', 'by', 'lt']
###        for metric in metrics_to_extract:
###          output_csv = self.get_csv(line_data['lb'], metric)
###          if output_csv in data:
###            data[output_csv].append(actual_timestamp + ',' + line_data[metric])
###          else:
###            data[output_csv] = []
###            data[output_csv].append(actual_timestamp + ',' + line_data[metric])
# End of line-by-line file processing
      for transaction in response_times:
        data[self.get_csv(transaction, 't')] = []
        rtimes = response_times[transaction]
        for time_stamp in sorted(rtimes):
          response_list = rtimes[time_stamp]
          data[self.get_csv(transaction, 't')].append(time_stamp + ',' + str(sum(map(int,response_list))/float(len(response_list))))

      for transaction in success_qps:
        data[self.get_csv(transaction + '.Successful', 'qps')] = []
        qps = success_qps[transaction]
        for time_stamp in sorted(qps):
          data[self.get_csv(transaction + '.Successful', 'qps')].append(time_stamp + ',' +  str(qps[time_stamp]/60))

      for transaction in error_qps:
        data[self.get_csv(transaction + '.Failed', 'qps')] = []
        qps = error_qps[transaction]
        for time_stamp in sorted(qps):
          data[self.get_csv(transaction + '.Failed', 'qps')].append(time_stamp + ',' +  str(qps[time_stamp]/60))

      for csv in data.keys():
        self.csv_files.append(csv)
        with open(csv, 'w') as csvf:
          csvf.write('\n'.join(sorted(data[csv])))

    return True

  def graph(self, graphing_library = 'matplotlib'):
    html_string = []
    html_string.append('<h1>Metric: {0}</h1>\n'.format(self.metric_type))
    logger.info('Using graphing_library {lib} for metric {name}'.format(lib=graphing_library, name=self.label))
    for out_csv in self.csv_files:
      csv_filename = os.path.basename(out_csv)
      # The last element is .csv, don't need that in the name of the chart
      column = csv_filename.split('.')[-2]
      graph_title = ' '.join(csv_filename.split('.')[1:-2]) + ' ' +  self.metric_description[column]
      image_prefix = '.'.join(csv_filename.split('.')[0:-1])

      plot_data = [PD(input_csv=out_csv, csv_column=1, series_name=graph_title, y_label=self.metric_units[column], precision=None, graph_height=600, graph_width=1200, graph_type='line')]
      graphed, html_ret = Metric.graphing_modules[graphing_library].graph_data(plot_data, self.outdir, image_prefix )
      if html_ret:
        html_string.append(html_ret)
      else:
        if graphed:
          img_tag = '<h3>{title}</h3><p><b>Description</b>: {description}</p><img src="{image_name}.png" />\n'.format(title=graph_title, description=self.metric_description[column], image_name=image_prefix)
        else:
          img_tag = '<h3>{title}</h3><p><b>Description</b>: {description}</p>No data for this metric\n'.format(title=graph_title, description=self.metric_description[column])
        html_string.append(img_tag)
    return '\n'.join(html_string)