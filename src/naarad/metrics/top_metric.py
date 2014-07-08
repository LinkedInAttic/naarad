# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""

from collections import defaultdict
import datetime
import logging
import gc
import os
import re
import numpy
from naarad.metrics.metric import Metric
import naarad.utils

logger = logging.getLogger('naarad.metrics.top_metric')

class TopMetric(Metric):
  """
  The raw log file is like the following:
  2014-06-23
  top - 00:00:02 up 18 days,  7:08, 19 users,  load average: 0.05, 0.03, 0.00
  Tasks: 447 total,   1 running, 443 sleeping,   2 stopped,   1 zombie
  Cpu(s):  1.6%us,  0.5%sy,  0.0%ni, 97.9%id,  0.0%wa,  0.0%hi,  0.0%si,  0.0%st
  Mem:    62.841G total,   15.167G used,   47.675G free,  643.434M buffers
  Swap:   63.998G total,    0.000k used,   63.998G free,   11.324G cached

  PID USER      PR  NI  VIRT  RES  SHR S %CPU %MEM    TIME+  COMMAND
  1730 root      20   0 4457m  10m 3328 S  1.9  0.0  80:13.45 lwregd
  The log lines can be generated by echo $t >> $RESULT/top.out &; top -b -M -n $COUNT -d $INTERVAL | grep -A 40 '^top' >> $RESULT/top.out &
  """  
  
  def __init__ (self, metric_type, infile, hostname, output_directory, resource_path, label, ts_start, ts_end,
                rule_strings, important_sub_metrics, **other_options):
    Metric.__init__(self, metric_type, infile, hostname, output_directory, resource_path, label, ts_start, ts_end,
                    rule_strings, important_sub_metrics, )
    
    #allow user to specify interested processes; in the format of 'PID=11 22' and 'COMMAND=firefox top'
    #It will search for any processes that match the PIDs listed or the commands listed. It's not an intersection of the PIDs and commands.
    self.PID = []
    self.COMMAND = []
    for (key, val) in other_options.iteritems():
      setattr(self, key, val.split())

    self.sub_metrics = None
    self.ts = ''
    self.ts_date = ''
    self.ts_time = ''
    self.saw_pid = False  #controls when to process individual commands;   
    
    self.data = defaultdict() #stores all data to be written out
    
    for (key, val) in other_options.iteritems():
      setattr(self, key, val.split())
      
    self.sub_metric_description = {
      'uptime_minute' : 'uptime of the machine',
      'num_users' : 'users sessions logged in', 
      'load_aver_1_minute' : 'average load on the system (last 1 minute)', 
      'load_aver_5_minute' : 'average load on the system (last 5 minutes)', 
      'load_aver_15_minute' : 'average load on the system (last 15 minutes)', 
      'tasks_total' : 'total processes',
      'tasks_running' : 'processes running', 
      'tasks_sleeping' : 'processes sleeping',
      'tasks_stopped' : 'processes stopped', 
      'tasks_zombie' : 'zombies',
      'cpu_us' : 'cpu percentage of running user processes',
      'cpu_sys' : 'cpu percentage of running system processes',
      'cpu_ni' : 'cpu percentage of running niced processes',
      'cpu_wa' : 'cpu percentage of waiting for IO', 
      'cpu_hi' : 'cpu percentage of serving hardware IRQ', 
      'cpu_si' : 'cpu percentage of serving software IRQ', 
      'cpu_st' : 'cpu percentage of being stolen',
      'mem_total' : 'total memory in GB',
      'mem_used' : 'total memory in use in GB',
      'mem_free' : 'total free memory in GB',
      'mem_buffers' : 'total buffers in GB',
      'swap_total' : 'total swap size in GB',
      'swap_used' : 'total swap in use in GB',
      'swap_free' : 'total free swap in GB',
      'swap_cached' : 'total swap cache in GB',
     }
  
  def put_value_into_data(self, col, value):
    """
    Append the 'value' into 'col' in self.data[]
    """
    if col in self.column_csv_map:
      out_csv = self.column_csv_map[col]
    else:
      out_csv = self.get_csv(col)   #  column_csv_map[] is assigned in get_csv()
      self.data[out_csv] = []
    self.data[out_csv].append(self.ts + "," + value)
      
  def process_top_line(self,words):
    """
    Process the line starting with "top"
    """
    self.ts_time = words[2]
    self.ts = self.ts_date + ' ' + self.ts_time
    up_days = int(words[4])  
    up_hour_minute = words[6].split(':')  # e.g. '4:02,'
    up_minutes = int(up_hour_minute[0]) * 60 + int(up_hour_minute[1].split(',')[0])
    uptime_minute = up_days * 24 * 60   + up_minutes  # converting days to minutes

    self.put_value_into_data('uptime_minute', str(uptime_minute))
    self.put_value_into_data('num_users', words[7])
    self.put_value_into_data('load_aver_1_minute', words[11][:-1])
    self.put_value_into_data('load_aver_5_minute', words[12][:-1])
    self.put_value_into_data('load_aver_15_minute', words[13])
    
  def process_tasks_line(self,words):
    """
    Process the line starting with "Tasks:"
    """    
    self.put_value_into_data('tasks_total', words[1])
    self.put_value_into_data('tasks_running', words[3])
    self.put_value_into_data('tasks_sleeping', words[5])
    self.put_value_into_data('tasks_stopped', words[7])
    self.put_value_into_data('tasks_zombie', words[9])
    
  def process_cpu_line(self, words):
    """
    Process the line starting with "Cpu(s):"
    """   
    self.put_value_into_data('cpu_us', words[1].split('%')[0])
    self.put_value_into_data('cpu_sy', words[2].split('%')[0])
    self.put_value_into_data('cpu_ni', words[3].split('%')[0])
    self.put_value_into_data('cpu_id', words[4].split('%')[0])
    self.put_value_into_data('cpu_wa', words[5].split('%')[0])
    self.put_value_into_data('cpu_hi', words[6].split('%')[0])
    self.put_value_into_data('cpu_si', words[7].split('%')[0])
    self.put_value_into_data('cpu_st', words[8].split('%')[0])
    
  def convert_to_G(self, word):
    """
    Given a size such as '2333M', return the converted value in G 
    """
    value = 0.0
    if word[-1] == 'G' or word[-1] == 'g':
      value = float(word[:-1])
    elif word[-1] == 'M' or word[-1] == 'm':
      value = float(word[:-1])/1000.0
    elif word[-1] == 'K' or word[-1] == 'k':
      value = float(word[:-1])/1000.0/1000.0
    else: #no unit
      value = float(word)/1000.0/1000.0/1000.0
    return str(value)
    
  def process_mem_line(self, words):
    """
    Process the line starting with "Mem:"
    For each value, needs to convert to 'G' (needs to handle cases of K, M)
    """    
    mem_total = self.convert_to_G(words[1])
    mem_used = self.convert_to_G(words[3])
    mem_free = self.convert_to_G(words[5])
    mem_buffers = self.convert_to_G(words[7])
    self.put_value_into_data('mem_total', mem_total)
    self.put_value_into_data('mem_used', mem_used)
    self.put_value_into_data('mem_free', mem_free)
    self.put_value_into_data('mem_buffers', mem_buffers)
    
  def process_swap_line(self, words):
    """
    Process the line starting with "Swap:"
    For each value, needs to convert to 'G' (needs to handle cases of K, M)
    """    
    swap_total = self.convert_to_G(words[1])
    swap_used = self.convert_to_G(words[3])
    swap_free = self.convert_to_G(words[5])
    swap_cached = self.convert_to_G(words[7])
    self.put_value_into_data('swap_total', swap_total)
    self.put_value_into_data('swap_used', swap_used)
    self.put_value_into_data('swap_free', swap_free)
    self.put_value_into_data('swap_cached', swap_cached)
  
  def process_individual_command(self, words):
    """
    process the individual lines like this:
    #PID USER      PR  NI  VIRT  RES  SHR S %CPU %MEM    TIME+  COMMAND
    29303 root      20   0 35300 2580 1664 R  3.9  0.0   0:00.02 top
    11 root      RT   0     0    0    0 S  1.9  0.0   0:18.87 migration/2
    3702 root      20   0 34884 4192 1692 S  1.9  0.0  31:40.47 cf-serverd
    It does not record all processes due to memory concern; rather only records interested processes (based on user input of PID and COMMAND)
    """
    pid = words[0]
    process = words[11]
    if pid in self.PID or process in self.COMMAND:
      process_name = process.split('/')[0]
      self.put_value_into_data(process_name + '_' + pid + '_' + 'PR', words[2])
      self.put_value_into_data(process_name + '_' + pid + '_' + 'NI', words[3])
      self.put_value_into_data(process_name + '_' + pid + '_' + 'VIRT', self.convert_to_G(words[4]))
      self.put_value_into_data(process_name + '_' + pid + '_' + 'RES', self.convert_to_G(words[5]))
      self.put_value_into_data(process_name + '_' + pid + '_' + 'SHR', self.convert_to_G(words[6]))
      self.put_value_into_data(process_name + '_' + pid + '_' + 'CPU', words[8])
      self.put_value_into_data(process_name + '_' + pid + '_' + 'MEM', words[9])
      
      uptime = words[10].split(':')
      uptime_sec = float(uptime[0]) * 60  + float(uptime[1])
      self.put_value_into_data(process_name + '_' + pid + '_' + 'TIME', str(uptime_sec) )
      
  def parse(self):
    """
    Parse the top output file
    Return status of the metric parse
    """
    logger.info('Processing : %s',self.infile_list)
    infile = self.infile_list[0]
    status = True
    file_status = naarad.utils.is_valid_file(infile)
    if not file_status:
      return False      

    with open(infile) as fh:
      for line in fh:
        words = line.split()
        if len(words) < 1:  #empty lines
          continue
        
        #'line of 2014-02-03'
        if re.match('^\d\d\d\d-\d\d-\d\d$',line):
          self.ts_date = words[0]
          continue

        prefix_word = words[0].strip()
        if prefix_word == 'top':
          self.process_top_line(words)
          self.saw_pid = False
        elif prefix_word == 'Tasks:':
          self.process_tasks_line(words)
        elif prefix_word == 'Cpu(s):':
          self.process_cpu_line(words)
        elif prefix_word == 'Mem:':
          self.process_mem_line(words)
        elif prefix_word == 'Swap:':
          self.process_swap_line(words)
        elif prefix_word == 'PID':
          self.saw_pid = True
        else:
          if self.saw_pid and len(words) > 10: #only valid process lines
            self.process_individual_command(words)
            
    #putting data in csv files;  
    for out_csv in self.data.keys():    # all sub_metrics
      self.csv_files.append(out_csv)
      with open(out_csv, 'w') as fh:
        fh.write('\n'.join(self.data[out_csv]))

    gc.collect()
    return status
