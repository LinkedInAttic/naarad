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
import naarad.utils
import sys

logger = logging.getLogger('naarad.metrics.cluster_metric')

class ClusterMetric(Metric):
  """
  supporting the metric of Cluster, which aggregates the performance metrics of multiple hosts
  """

  metrics = []   # all other non-aggregate metrics;
  aggr_metrics = []  # metrics to be aggregated
  aggr_hosts = [] # hosts to be aggregated

  def __init__ (self, section, aggregate_hosts, aggregate_metrics, metrics, output_directory, resource_path, label,
                ts_start, ts_end, rule_strings, important_sub_metrics, anomaly_detection_metrics, **other_options):
    self.metrics = metrics
    self.aggr_metrics = aggregate_metrics.split()
    self.aggr_hosts = aggregate_hosts.split()

    #Metric arguments take 'infile' and 'hostname', for ClusterMetric, they are invalid, so just provide empty strings.
    Metric.__init__(self, section, '', '', output_directory, resource_path, label, ts_start, ts_end, rule_strings,
                    important_sub_metrics, anomaly_detection_metrics)

    for (key, val) in other_options.iteritems():
      setattr(self, key, val.split())

  def collect(self):
    """
    Take a list of metrics, filter all metrics based on hostname, and metric_type
    For each metric, merge the corresponding csv files into one,update corresponding properties such as csv_column_map.
    Users can specify functions: raw, count (qps), sum (aggregated value), avg (averaged value)
    The timestamp granularity of aggregated submetrics is in seconds (sub-second is not supported)
    """

    for aggr_metric in self.aggr_metrics:   # e.g., SAR-device.sda.await:count,sum,avg
      functions_aggr = []
      fields = aggr_metric.split(":")
      cur_metric_type = fields[0].split(".")[0]  # e.g. SAR-device

      if len(fields) > 1:  # The user has to specify the aggregate functions (i.e., :raw,count,sum,avg)
        func_user = ''.join(fields[1].split())
        functions_aggr.extend(func_user.split(","))
      else:  # no user input of aggregate functions
        return True

      cur_column = '.'.join(fields[0].split('.')[1:])    #e.g. sda.await or all.percent-sys

      #store data points of various aggregation functions
      aggr_data = {}
      aggr_data['raw'] = []   #store all the raw values
      aggr_data['sum'] = defaultdict(float)   #store the sum values for each timestamp
      aggr_data['count'] = defaultdict(int) #store the count of each timestamp (i.e. qps)

      for metric in self.metrics:   # loop the list to find from all metrics to merge
        if metric.hostname in self.aggr_hosts and \
          cur_column in metric.csv_column_map.values():
          file_csv = metric.get_csv(cur_column)
          timestamp_format = None
          with open(file_csv) as fh:
            for line in fh:
              aggr_data['raw'].append(line.rstrip())
              words = line.split(",")
              ts = words[0].split('.')[0]   #in case of sub-seconds; we only want the value of seconds;
              if not timestamp_format or timestamp_format == 'unknown':
                timestamp_format = naarad.utils.detect_timestamp_format(ts)
              if timestamp_format == 'unknown':
                continue
              ts = naarad.utils.get_standardized_timestamp(ts, timestamp_format)
              aggr_data['sum'][ts] += float(words[1])
              aggr_data['count'][ts] += 1
      #"raw" csv file
      if 'raw' in functions_aggr:
        out_csv = self.get_csv(cur_column, 'raw')
        self.csv_files.append(out_csv)
        with open(out_csv, 'w') as fh:
          fh.write("\n".join(sorted(aggr_data['raw'])))
      
      #"sum"  csv file
      if 'sum' in functions_aggr:
        out_csv = self.get_csv(cur_column, 'sum')
        self.csv_files.append(out_csv)
        with open(out_csv, 'w') as fh:
          for k,v in sorted(aggr_data['sum'].items()):
            fh.write(k + "," + str(v) + '\n')

      # "avg" csv file
      if 'avg' in functions_aggr:
        out_csv = self.get_csv(cur_column, 'avg')
        self.csv_files.append(out_csv)
        with open(out_csv, 'w') as fh:
          for k,v in sorted(aggr_data['sum'].items()):
            fh.write(k + "," + str(v/aggr_data['count'][k]) + '\n')

      # "count" csv file (qps)
      if 'count' in functions_aggr:
        out_csv = self.get_csv(cur_column, 'count')
        self.csv_files.append(out_csv)
        with open(out_csv, 'w') as fh:
          for k,v in sorted(aggr_data['count'].items()):
            fh.write(k + "," + str(v) + '\n')

      gc.collect()
    return True

  def get_csv(self, column, func):
    csv_file = Metric.get_csv(self, column + '.' + func)
    return csv_file

  def parse(self):
    """
    merge multiple hosts' csv into one csv file. This approach has the benefit of reusing calculate_stats(), but with the penalty of reading the single csv later for calculate_stats()
    However, since file cache will cache the newly written csv files, reading the csv file will not likely be a IO bottleneck.
    """

    return True
