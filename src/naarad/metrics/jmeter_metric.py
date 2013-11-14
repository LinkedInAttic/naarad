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
    self.calculated_stats = {}
    self.calculated_percentiles = {}

  def get_csv(self, transaction_name, column):
    col = naarad.utils.sanitize_string(column)
    csv = os.path.join(self.outdir, self.metric_type + '.' + transaction_name + '.' + col + '.csv')
    return csv

  def calculate_overall_qps_over_time(self, success_qps, error_qps, line_data, aggregate_timestamp):
    if line_data['s'] == 'true':
      qps = success_qps
    else:
      qps = error_qps
    if aggregate_timestamp not in qps:
      qps[aggregate_timestamp] = 1
    else:
      qps[aggregate_timestamp] += 1
    return None

  def calculate_average_qps_over_time(self, success_qps, error_qps, line_data, aggregate_timestamp):
    if line_data['s'] == 'true':
      all_qps = success_qps
    else:
      all_qps = error_qps
    transaction = line_data['lb']
    qps = all_qps[transaction]
    if aggregate_timestamp in qps:
      qps[aggregate_timestamp] += 1
    else:
      qps[aggregate_timestamp] = 1
    return None

  def aggregate_overall_values_over_time(self, metric_store, line_data, metric, aggregate_timestamp):
    metric_data = metric_store[aggregate_timestamp]
    metric_data.append(float(line_data[metric]))
    return None

  def aggregate_values_over_time(self, metric_store, line_data, metric, aggregate_timestamp):
    transaction = line_data['lb']
    metric_series = metric_store[transaction]
    metric_data = metric_series[aggregate_timestamp]
    metric_data.append(float(line_data[metric]))
    return None

  def parse(self):
    logger.info('Processing : %s',self.infile)
    file_status, error_message = naarad.utils.is_valid_file(self.infile)
    if not file_status:
      return False
    status = self.parse_xml_jtl()
    gc.collect()
    return status

  def parse_xml_jtl(self):
    with open(self.infile) as infile:
      data = defaultdict(list)
      success_qps = defaultdict(lambda : defaultdict(list))
      error_qps = defaultdict(lambda : defaultdict(list))
      response_times = defaultdict(lambda : defaultdict(list))
      response_sizes = defaultdict(lambda : defaultdict(list))
      overall_success_qps = defaultdict(float)
      overall_error_qps = defaultdict(float)
      overall_response_times = defaultdict(list)
      overall_response_sizes = defaultdict(list)
      raw_response_times = defaultdict(list)
      raw_response_sizes = defaultdict(list)
      line_regex = re.compile(r' (lb|ts|t|by|s)="([^"]+)"')
      for line in infile:
        if '<httpSample' not in line:
          continue
        line_data = dict(re.findall(line_regex, line))
        aggregate_timestamp = datetime.datetime.utcfromtimestamp(int(line_data['ts']) / 1000).strftime('%Y-%m-%d %H:%M') + ':00'
        self.calculate_overall_qps_over_time(overall_success_qps, overall_error_qps, line_data, aggregate_timestamp)
        self.aggregate_overall_values_over_time(overall_response_times, line_data, 't', aggregate_timestamp)
        self.aggregate_overall_values_over_time(overall_response_sizes, line_data, 'by', aggregate_timestamp)
        self.calculate_average_qps_over_time(success_qps, error_qps, line_data, aggregate_timestamp)
        self.aggregate_values_over_time(response_times,line_data,'t', aggregate_timestamp)
        self.aggregate_values_over_time(response_sizes,line_data,'by', aggregate_timestamp)
      logger.info('Finished parsing : %s', self.infile)
      logger.info('Processing Overall response times')
      for time_stamp in sorted(overall_response_times):
        response_list = overall_response_times[time_stamp]
        data[self.get_csv('Summary', 't')].append(','.join([time_stamp, str(sum(map(float, response_list))/float(len(response_list)))]))
      logger.info('Processing Overall response sizes')
      for time_stamp in sorted(overall_response_sizes):
        response_list = overall_response_sizes[time_stamp]
        data[self.get_csv('Summary', 'by')].append(','.join([time_stamp, str(sum(map(float, response_list))/float(len(response_list)))]))
        data[self.get_csv('Summary', 'thr')].append(','.join([time_stamp, str(sum(map(float, response_list))/float(60.0 * 1024 *1024/8.0))]))
      logger.info('Processing Overall Successful qps')
      for time_stamp in sorted(overall_success_qps):
        data[self.get_csv('Summary', 'qps')].append(','.join([time_stamp, str(overall_success_qps[time_stamp]/float(60.0))]))
      logger.info('Processing Overall Error qps')
      for time_stamp in sorted(overall_error_qps):
        data[self.get_csv('Summary', 'eqps')].append(','.join([time_stamp, str(overall_error_qps[time_stamp]/float(60.0))]))
      logger.info('Processing per Transaction response times')
      for transaction in response_times:
        rtimes = response_times[transaction]
        for time_stamp in sorted(rtimes):
          response_list = rtimes[time_stamp]
          data[self.get_csv(transaction, 't')].append(','.join([time_stamp, str(sum(map(float,response_list))/float(len(response_list)))]))
      logger.info('Processing response size and data throughput')
      for transaction in response_sizes:
        rsizes = response_sizes[transaction]
        for time_stamp in sorted(rsizes):
          response_list = rsizes[time_stamp]
          data[self.get_csv(transaction, 'by')].append(','.join([time_stamp, str(sum(map(float,response_list))/float(len(response_list)))]))
          data[self.get_csv(transaction, 'thr')].append(','.join([time_stamp, str(sum(map(float,response_list))/float(60.0 * 1024 *1024/8.0))]))
      logger.info('Processing Successful qps')
      for transaction in success_qps:
        qps = success_qps[transaction]
        for time_stamp in sorted(qps):
          data[self.get_csv(transaction, 'qps')].append(','.join([time_stamp, str(qps[time_stamp]/float(60))]))
      logger.info('Processing Error qps')
      for transaction in error_qps:
        qps = error_qps[transaction]
        for time_stamp in sorted(qps):
          data[self.get_csv(transaction, 'eqps')].append(','.join([time_stamp, str(qps[time_stamp]/float(60))]))
      for csv in data.keys():
        self.csv_files.append(csv)
        with open(csv, 'w') as csvf:
          csvf.write('\n'.join(sorted(data[csv])))
      logger.info('Processing raw data for stats')
      for transaction in response_times:
        response_time_data = response_times[transaction]
        response_size_data = response_sizes[transaction]
        for time_stamp in response_time_data:
          raw_response_times['Summary'].extend(response_time_data[time_stamp])
          raw_response_times[transaction].extend(response_time_data[time_stamp])
          raw_response_sizes['Summary'].extend(response_size_data[time_stamp])
          raw_response_sizes[transaction].extend(response_size_data[time_stamp])
      stats_to_calculate = ['mean', 'std', 'median', 'min', 'max'] # TODO: get input from user
      percentiles_to_calculate = range(5,101,5) # TODO: get input from user
      percentiles_to_calculate.append(99)
      for transaction in raw_response_times:
        self.calculated_stats[transaction], self.calculated_percentiles[transaction] = naarad.utils.calculate_stats(raw_response_times[transaction], stats_to_calculate, percentiles_to_calculate)

    return True

  def calculate_stats(self):
    stats_csv = self.get_stats_csv()
    csv_header = 'sub_metric,mean,std. deviation,median,min,max,90%,95%,99%\n'
    with open(stats_csv,'w') as FH:
      FH.write(csv_header)
      for sub_metric in self.calculated_stats:
        percentile_data = self.calculated_percentiles[sub_metric]
        stats_data = self.calculated_stats[sub_metric]
        csv_data = ','.join([sub_metric,str(numpy.round_(stats_data['mean'], 2)),str(numpy.round_(stats_data['std'], 2)),str(numpy.round_(stats_data['median'], 2)),str(numpy.round_(stats_data['min'], 2)),str(numpy.round_(stats_data['max'], 2)),str(numpy.round_(percentile_data[90], 2)),str(numpy.round_(percentile_data[95], 2)),str(numpy.round_(percentile_data[99], 2))])
        FH.write(csv_data + '\n')

    for sub_metric in self.calculated_percentiles:
      percentiles_csv = self.get_csv(sub_metric,'percentiles')
      percentile_data = self.calculated_percentiles[sub_metric]
      with open(percentiles_csv,'w') as FH:
        for percentile in sorted(percentile_data):
          FH.write(str(percentile) + ',' + str(numpy.round_(percentile_data[percentile],2)) + '\n')

  def get_summary_html(self):
    data_row = '''
    <p><table width="50%" class="sortable">
    <caption>Transaction Response Times(ms)</caption>
    <thead bgcolor="lightsteelblue"><tr><th align="left">Transaction</th><th align="right">Mean</th>
    <th align="right">Std.dv</th><th align="right">Median</th><th align="right">Min</th><th align="right">Max</th>
    <th align="right">90%</th><th align="right">95%</th><th align="right">99%</th></tr></thead>
    '''
    footer_row = '<tfoot bgcolor=wheat>'
    for transaction in self.calculated_stats:
      stats = self.calculated_stats[transaction]
      percentiles = self.calculated_percentiles[transaction]
      if transaction == 'Summary':
        footer_row += '<tr><td>' + transaction + '</td>'
        footer_row += '<td align="right">' + str(numpy.round_(stats['mean'],2)) + '</td>'
        footer_row += '<td align="right">' + str(numpy.round_(stats['std'],2)) + '</td>'
        footer_row += '<td align="right">' + str(numpy.round_(stats['median'],2)) + '</td>'
        footer_row += '<td align="right">' + str(numpy.round_(stats['min'],2)) + '</td>'
        footer_row += '<td align="right">' + str(numpy.round_(stats['max'],2)) + '</td>'
        footer_row += '<td align="right">' + str(numpy.round_(percentiles[90],2)) + '</td>'
        footer_row += '<td align="right">' + str(numpy.round_(percentiles[95],2)) + '</td>'
        footer_row += '<td align="right">' + str(numpy.round_(percentiles[99],2)) + '</td></tr></tfoot>'
      else:
        data_row += '<tr><td>' + transaction + '</td>'
        data_row += '<td align="right">' + str(numpy.round_(stats['mean'],2)) + '</td>'
        data_row += '<td align="right">' + str(numpy.round_(stats['std'],2)) + '</td>'
        data_row += '<td align="right">' + str(numpy.round_(stats['median'],2)) + '</td>'
        data_row += '<td align="right">' + str(numpy.round_(stats['min'],2)) + '</td>'
        data_row += '<td align="right">' + str(numpy.round_(stats['max'],2)) + '</td>'
        data_row += '<td align="right">' + str(numpy.round_(percentiles[90],2)) + '</td>'
        data_row += '<td align="right">' + str(numpy.round_(percentiles[95],2)) + '</td>'
        data_row += '<td align="right">' + str(numpy.round_(percentiles[99],2)) + '</td></tr>'
    data_row = data_row + '\n' + footer_row + '</table></p>'
    return data_row

  def graph(self, graphing_library = 'matplotlib'):
    html_string = []
    html_string.append('<h2>Metric: {0}</h2>\n'.format(self.metric_type))
    html_string.append(self.get_summary_html())
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
      graphed, html_ret = Metric.graphing_modules[graphing_library].graph_data(plot_data[transaction], self.outdir, transaction )
      if html_ret:
        html_string.append(html_ret)
      else:
        if graphed:
          img_tag = '<h3>{title}</h3><p><b>Description</b>: {description}</p><img src="{image_name}.png" />\n'.format(title=transaction, description=transaction + ' workload client statistics', image_name=transaction)
        else:
          img_tag = '<h3>{title}</h3><p><b>Description</b>: {description}</p>No data for this metric\n'.format(title=transaction, description='')
        html_string.append(img_tag)
    return '\n'.join(html_string)
