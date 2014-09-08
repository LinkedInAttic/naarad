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

import gc
import os
import re
import logging
from naarad.metrics.metric import Metric
import naarad.utils

logger = logging.getLogger('naarad.metrics.top_metric')

class TopMetric(Metric):
  def __init__ (self, metric_type, infile, hostname, output_directory, resource_path, label, ts_start, ts_end,
                rule_strings, important_sub_metrics, anomaly_detection_metrics, **other_options):
    Metric.__init__(self, metric_type, infile, hostname, output_directory, resource_path, label, ts_start, ts_end,
                    rule_strings, important_sub_metrics, anomaly_detection_metrics)

    # Allow user to specify interested processes; in the format of 'PID=11 22' and 'COMMAND=firefox top'
    # It will search for any processes that match the PIDs listed or the commands listed. It's not an intersection of the PIDs and commands.
    self.PID = []
    self.COMMAND = []
    self.ts_valid_lines = True

    for (key, val) in other_options.iteritems():
      setattr(self, key, val.split())

    self.sub_metrics = None
    self.process_headers = []
    self.ts = ''
    self.ts_date = ''
    self.ts_time = ''
    self.saw_pid = False   # Controls when to process individual commands;

    self.data = {} # Stores all data to be written out

    for key, val in other_options.iteritems():
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
      'cpu_sy' : 'cpu percentage of running system processes',
      'cpu_id' : 'cpu percentage of idel time',
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

  def put_values_into_data(self, values):
    """
    Take the (col, value) in 'values', append value into 'col' in self.data[]
    """
    for col, value in values.items():
      if col in self.column_csv_map:
        out_csv = self.column_csv_map[col]
      else:
        out_csv = self.get_csv(col)   # column_csv_map[] is assigned in get_csv()
        self.data[out_csv] = []
      self.data[out_csv].append(self.ts + "," + value)

  def process_top_line(self, words):
    """
    Process the line starting with "top"
    Example log:   top - 00:00:02 up 32 days,  7:08, 19 users,  load average: 0.00, 0.00, 0.00
    """
    self.ts_time = words[2]
    self.ts = self.ts_date + ' ' + self.ts_time
    self.ts = ts = naarad.utils.get_standardized_timestamp(self.ts, None)

    if self.ts_out_of_range(self.ts):
      self.ts_valid_lines = False
    else:
      self.ts_valid_lines = True
    up_days = int(words[4])
    up_hour_minute = words[6].split(':')  # E.g. '4:02,'
    up_minutes = int(up_hour_minute[0]) * 60 + int(up_hour_minute[1].split(',')[0])
    uptime_minute = up_days * 24 * 60   + up_minutes  # Converting days to minutes

    values = {}
    values['uptime_minute'] = str(uptime_minute)
    values['num_users'] = words[7]
    values['load_aver_1_minute'] = words[11][:-1]
    values['load_aver_5_minute'] = words[12][:-1]
    values['load_aver_15_minute'] = words[13]
    self.put_values_into_data(values)

  def process_tasks_line(self,words):
    """
    Process the line starting with "Tasks:"
    Example log:   Tasks: 446 total,   1 running, 442 sleeping,   2 stopped,   1 zombie
    """
    words = words[1:]
    length = len(words) / 2 # The number of pairs
    values = {}
    for offset in range(length):
      k = words[2 * offset + 1].strip(',')
      v = words[2 * offset]
      values['tasks_' + k] = v
    self.put_values_into_data(values)

  def process_cpu_line(self, words):
    """
    Process the line starting with "Cpu(s):"
    Example log: Cpu(s):  1.3%us,  0.5%sy,  0.0%ni, 98.2%id,  0.0%wa,  0.0%hi,  0.0%si,  0.0%st
    """

    values = {}
    for word in words[1:]:
      val, key = word.split('%')
      values['cpu_' + key.strip(',')] = val
    self.put_values_into_data(values)

  def convert_to_G(self, word):
    """
    Given a size such as '2333M', return the converted value in G
    """
    value = 0.0
    if word[-1] == 'G' or word[-1] == 'g':
      value = float(word[:-1])
    elif word[-1] == 'M' or word[-1] == 'm':
      value = float(word[:-1]) / 1000.0
    elif word[-1] == 'K' or word[-1] == 'k':
      value = float(word[:-1]) / 1000.0 / 1000.0
    else: # No unit
      value = float(word) / 1000.0 / 1000.0 / 1000.0
    return str(value)

  def process_mem_line(self, words):
    """
    Process the line starting with "Mem:"
    Example log: Mem:    62.841G total,   16.038G used,   46.803G free,  650.312M buffers
    For each value, needs to convert to 'G' (needs to handle cases of K, M)
    """
    words = words[1:]
    length = len(words) / 2 # The number of pairs
    values = {}
    for offset in range(length):
      k = words[2 * offset + 1].strip(',')
      v = self.convert_to_G(words[2 * offset])
      values['mem_' + k] = v
    self.put_values_into_data(values)

  def process_swap_line(self, words):
    """
    Process the line starting with "Swap:"
    Example log: Swap:   63.998G total,    0.000k used,   63.998G free,   11.324G cached
    For each value, needs to convert to 'G' (needs to handle cases of K, M)
    """
    words = words[1:]
    length = len(words) / 2 # The number of pairs
    values = {}
    for offset in range(length):
      k = words[2 * offset + 1].strip(',')
      v = self.convert_to_G(words[2 * offset])
      values['swap_' + k] = v
    self.put_values_into_data(values)

  def process_individual_command(self, words):
    """
    process the individual lines like this:
    #PID USER      PR  NI  VIRT  RES  SHR S %CPU %MEM    TIME+  COMMAND
    29303 root      20   0 35300 2580 1664 R  3.9  0.0   0:00.02 top
    11 root      RT   0     0    0    0 S  1.9  0.0   0:18.87 migration/2
    3702 root      20   0 34884 4192 1692 S  1.9  0.0  31:40.47 cf-serverd
    It does not record all processes due to memory concern; rather only records interested processes (based on user input of PID and COMMAND)
    """
    pid_index = self.process_headers.index('PID')
    proces_index = self.process_headers.index('COMMAND')

    pid = words[pid_index]
    process = words[proces_index]
    if pid in self.PID or process in self.COMMAND:
      process_name = process.split('/')[0]

      values = {}
      for word_col in self.process_headers:
        word_index = self.process_headers.index(word_col)
        if word_col in ['VIRT', 'RES', 'SHR']: # These values need to convert to 'G'
          values[process_name + '_' + pid + '_' + word_col] = self.convert_to_G(words[word_index])
        elif word_col in ['PR', 'NI', '%CPU', '%MEM']: # These values will be assigned later or ignored
          values[process_name + '_' + pid + '_' + word_col.strip('%')] = words[word_index]

        uptime_index = self.process_headers.index('TIME+')
        uptime = words[uptime_index].split(':')
        uptime_sec = float(uptime[0]) * 60  + float(uptime[1])
        values[process_name + '_' + pid + '_' + 'TIME'] = str(uptime_sec)
      self.put_values_into_data(values)

  def parse(self):
    """
    Parse the top output file
    Return status of the metric parse

    The raw log file is like the following:
    2014-06-23
    top - 00:00:02 up 18 days,  7:08, 19 users,  load average: 0.05, 0.03, 0.00
    Tasks: 447 total,   1 running, 443 sleeping,   2 stopped,   1 zombie
    Cpu(s):  1.6%us,  0.5%sy,  0.0%ni, 97.9%id,  0.0%wa,  0.0%hi,  0.0%si,  0.0%st
    Mem:    62.841G total,   15.167G used,   47.675G free,  643.434M buffers
    Swap:   63.998G total,    0.000k used,   63.998G free,   11.324G cached

    PID USER      PR  NI  VIRT  RES  SHR S %CPU %MEM    TIME+  COMMAND
    1730 root      20   0 4457m  10m 3328 S  1.9  0.0  80:13.45 lwregd
    The log lines can be generated by echo $t >> $RESULT/top.out &; top -b -n $COUNT -d $INTERVAL | grep -A 40 '^top' >> $RESULT/top.out &
    """

    for infile in self.infile_list:
      logger.info('Processing : %s', infile)
      status = True
      file_status = naarad.utils.is_valid_file(infile)
      if not file_status:
        return False

      with open(infile) as fh:
        for line in fh:
          words = line.split()
          if not words:
            continue

          # Pattern matches line of '2014-02-03'
          if re.match('^\d\d\d\d-\d\d-\d\d$', line):
            self.ts_date = words[0]
            continue

          prefix_word = words[0].strip()
          if prefix_word == 'top':
            self.process_top_line(words)
            self.saw_pid = False  # Turn off the processing of individual process line
          elif self.ts_valid_lines:
            if prefix_word == 'Tasks:':
              self.process_tasks_line(words)
            elif prefix_word == 'Cpu(s):':
              self.process_cpu_line(words)
            elif prefix_word == 'Mem:':
              self.process_mem_line(words)
            elif prefix_word == 'Swap:':
              self.process_swap_line(words)
            elif prefix_word == 'PID':
              self.saw_pid = True  # Turn on the processing of individual process line
              self.process_headers = words
            else: # Each individual process line
              if self.saw_pid and len(words) >= len(self.process_headers): # Only valid process lines
                self.process_individual_command(words)

    # Putting data in csv files;
    for out_csv in self.data.keys():    # All sub_metrics
      self.csv_files.append(out_csv)
      with open(out_csv, 'w') as fh:
        fh.write('\n'.join(self.data[out_csv]))

    gc.collect()
    return status
