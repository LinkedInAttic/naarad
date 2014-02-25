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
  # all other non-aggregate metrics; 
  metrics = [] 
  
  # metrics to be aggregated
  aggr_metrics = []
  
  # hosts to be aggregated
  aggr_hosts = []
    
  sub_metrics = None
              
  #store all the merged files; 
  infiles = []
  
  def __init__ (self, section, aggregate_hosts, aggregate_metrics, metrics, output_directory, resource_path, label, ts_start, ts_end,
                rule_strings, **other_options):
    self.metrics = metrics
    self.aggr_metrics = re.split(",| |:", aggregate_metrics)  #support both "," and " ", ":" as separator
    self.aggr_hosts = re.split(",| |:", aggregate_hosts) 
                  
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
    """

    for aggr_metric in self.aggr_metrics:   # e.g., SAR-device.sda.await
      cur_metric_type =  aggr_metric.split(".")[0]  # e.g. SAR-device
      cur_column = aggr_metric[len(cur_metric_type)+1:]  #e.g. sda.await or all.percent-sys
      cur_column = cur_column.replace('percent-','%')  # to handle the case when user specify "percent-" rather than '%';  what we expect is "%"      
    
      merged_data = []      #store all the possible values
      for metric in self.metrics:   # loop the list to find from all metrics to merge       
        file_csv = ""
        if metric.hostname in self.aggr_hosts and \
          cur_column in metric.csv_column_map.values():             
          file_csv = metric.get_csv(cur_column)                      
        
        if file_csv:   # found the file, merge it into merged_csv{}
          with open(file_csv) as fh:
            for line in fh:
              # handle the last line from each file gracefully by adding "\n"
              if "\n" in line:
                merged_data.append(line)
              else:
                merged_data.append(line + "\n")          
      
      out_csv = self.get_csv(cur_column)   #  column_csv_map and csv_column_map are assigned in get_csv()                 
      with open(out_csv, 'w') as fh:
        self.csv_files.append(out_csv)
        fh.write("".join(sorted(merged_data)) )

      gc.collect()
    return True
  
  def parse(self):
    """
    merge multiple hosts' csv into one csv file. This approach has the benefit of reusing calculate_stats(), but with the penalty of reading the single csv later for calculate_stats()
    However, since file cache will cache the newly written csv files, reading the csv file will not likely be a IO bottleneck. 
    """
    return True
    
