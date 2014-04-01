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

  def __init__ (self, section, aggregate_hosts, aggregate_metrics, metrics, output_directory, resource_path, label, ts_start, ts_end,
                rule_strings, **other_options):
    self.metrics = metrics
    self.aggr_metrics = aggregate_metrics.split()
    self.aggr_hosts = aggregate_hosts.split()
                  
    #Metric arguments take 'infile' and 'hostname', for ClusterMetric, they are invalid, so just provide empty strings.     
    Metric.__init__(self, section, '', '', output_directory, resource_path, label, ts_start, ts_end, rule_strings)
    
    # in particular, Section can specify a subset of all rows (default has 43 rows):  "sub_metrics=nr_free_pages nr_inactive_anon"
    for (key, val) in other_options.iteritems():
      setattr(self, key, val.split())
      
  def collect(self):
    """
    take metrics, filter all metrics based on hostname, and metric_type (which comes from section)
    for each metric, merge the corresponding csv files into one, and output to disk
    update corresponding properties such as csv_column_map. 
    by default, each aggr_metric only gets "raw" function (the simply merged data points)
    users can specify other functions:  count (qps), sum (aggregated value), avg (averaged value)
    The timestamp granularity of aggregated submetrics is in seconds (sub-second is not supported)
    """
    
    for aggr_metric in self.aggr_metrics:   # e.g., SAR-device.sda.await:count,sum,avg
      functions = set()      
      fields = aggr_metric.split(":")   
      cur_metric_type = fields[0].split(".")[0]  # e.g. SAR-device
      
      if len(fields) > 1:  # if config file has ":sum,count"
        for func in fields[1].split(","):
          functions.add(func)

      cur_column = '.'.join(fields[0].split('.')[1:])    #e.g. sda.await or all.percent-sys
      cur_column = cur_column.replace('percent-','%')  # to handle the case when user specify "percent-" rather than '%'; we expect "%"
    
      merged_raw = []      #store all the raw values
      merged_sum = defaultdict(float)       #store the sum values for each timestamp   
      merged_count = defaultdict(float)     #store the count of each timestamp (i.e. qps)
      
      for metric in self.metrics:   # loop the list to find from all metrics to merge       
        file_csv = ""
        if metric.hostname in self.aggr_hosts and \
          cur_column in metric.csv_column_map.values():  
          file_csv = metric.get_csv(cur_column)

          with open(file_csv) as fh:
            for line in fh:
              merged_raw.append(line.rstrip())              
              # generate "sum" and "avg" sub-metric
              words = line.split(",")  
              value = words[1]                     
              ts = words[0]  # timestamp in "2014-03-03 01:02:11.2334" format or "2014-03-03 01:02:11"
              ts = ts.split('.')[0] #in case of sub-seconds; we only want seconds; 
               
              if ts in merged_sum.keys():
                merged_sum[ts] += float(value)
                merged_count[ts] += 1
              else:
                merged_sum[ts] = float(value)
                merged_count[ts] = 1      

      #"raw" csv file
      if 'raw' in functions:
        out_csv = self.get_csv(cur_column + ".raw")
        self.csv_files.append(out_csv)
        with open(out_csv, 'w') as fh:
          fh.write("\n".join(sorted(merged_raw)) )
      
      #"sum"  csv file
      if 'sum' in functions:
        out_csv = self.get_csv(cur_column + '.sum')
        self.csv_files.append(out_csv)
        with open(out_csv, 'w') as fh:
          for k,v in sorted(merged_sum.items()):
            fh.write(k + "," + str(v)+"\n")
      
      # "avg" csv file  
      if 'avg' in functions: 
        out_csv = self.get_csv(cur_column + '.avg')
        self.csv_files.append(out_csv)
        with open(out_csv, 'w') as fh:
          for k,v in sorted(merged_sum.items()):
            fh.write(k + "," + str(v/merged_count[k])+"\n")
          
      # "count" csv file (qps)
      if 'count' in functions:
        out_csv = self.get_csv(cur_column + '.count')
        self.csv_files.append(out_csv)
        with open(out_csv, 'w') as fh:
          for k,v in sorted(merged_count.items()):
            fh.write(k + "," + str(v)+"\n")
          
      gc.collect()
    return True 
          
  def parse(self):
    """
    merge multiple hosts' csv into one csv file. This approach has the benefit of reusing calculate_stats(), but with the penalty of reading the single csv later for calculate_stats()
    However, since file cache will cache the newly written csv files, reading the csv file will not likely be a IO bottleneck. 
    """
    
    return True
