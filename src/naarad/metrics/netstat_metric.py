# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
from collections import defaultdict
import logging
from naarad.metrics.metric import Metric
import naarad.utils

logger = logging.getLogger('naarad.metrics.NetstatMetric')

class NetstatMetric(Metric):
  """
  Netstat metric
  The netstat output can be obtained by command of 'netstat -Ttp'
  'connections' is given by the user in config file. Each element contains two ends of the socket, they are keywords in the hostname and the port number;
  Note that port number can be 'ssh', and is optional
  'input_connections' is used internally, will contain a list of user interested connections;
  each element is a tuple of (host1,port1,host2,port2); (e.g., ('localhost','','','2344')
  'processes' is given by the user in config file;   It will contain user-input of process names (pid/process, or pid, or /process)
  'input_processes' is used internally, contains a list of pid/processes
  """
  connections = ''
  input_connections = []
  processes = ''
  input_processes = []

  def __init__ (self, metric_type, infile_list, hostname, output_directory, resource_path, label, ts_start, ts_end,
                rule_strings, important_sub_metrics, anomaly_detection_metrics, **other_options):
    Metric.__init__(self, metric_type, infile_list, hostname, output_directory, resource_path, label, ts_start, ts_end,
                    rule_strings, important_sub_metrics, anomaly_detection_metrics)
    self.sub_metrics = None
    for (key, val) in other_options.iteritems():
      setattr(self, key, val.split())

    self._extract_input_connections()
    self._extract_input_processes()

  def _get_tuple(self, fields):
    """
    :param fields: a list which contains either 0,1,or 2 values
    :return: a tuple with default values of '';
    """
    v1 = ''
    v2 = ''
    if len(fields) > 0:
      v1 = fields[0]
    if len(fields) > 1:
      v2 = fields[1]
    return v1, v2

  def _extract_input_connections(self):
    """
    Given user input of interested connections, it will extract the info and output a list of tuples.
    - input can be multiple values, separated by space;
    - either host or port is optional
    - it may be just one end,
    - e.g., "host1<->host2 host3<->  host1:port1<->host2"
    :return: None
    """
    for con in self.connections:
      ends = con.strip().split('<->')  # [host1:port1->host2]
      ends = filter(None, ends) #remove '' elements
      if len(ends) == 0:
        continue
      if len(ends) > 0:
        host1, port1 = self._get_tuple(ends[0].split(':'))
      host2 = ''
      port2 = ''
      if len(ends) > 1:
        host2, port2 = self._get_tuple(ends[1].split(':'))
      self.input_connections.append((host1,port1,host2,port2))

  def _extract_input_processes(self):
    """
    Given user input of interested processes, it will extract the info and output a list of tuples.
    - input can be multiple values, separated by space;
    - either pid or process_name is optional
    - e.g., "10001/python 10002/java cpp"
    :return: None
    """
    for proc in self.processes:
      ends = proc.split('/')
      pid, name = self._get_tuple(ends)
      self.input_processes.append((pid,name))

  def _match_host_port(self, host, port, cur_host, cur_port):
    """
    Determine whether user-specified (host,port) matches current (cur_host, cur_port)
    :param host,port: The user input of (host,port)
    :param cur_host, cur_port: The current connection
    :return: True or Not
    """
    # if host is '', true;  if not '', it should prefix-match cur_host
    host_match = False
    if not host:
      host_match = True
    elif cur_host.startswith(host):  #allow for partial match
      host_match = True

    # if port is '', true;  if not '', it should exactly match cur_port
    port_match = False
    if not port:
      port_match = True
    elif port == cur_port:
      port_match = True

    return host_match and port_match

  def _match_processes(self, pid, name, cur_process):
    """
    Determine whether user-specified "pid/processes" contain this process
    :param pid: The user input of pid
    :param name: The user input of process name
    :param process: current process info
    :return: True or Not; (if both pid/process are given, then both of them need to match)
    """
    cur_pid, cur_name = self._get_tuple(cur_process.split('/'))

    pid_match = False
    if not pid:
      pid_match = True
    elif pid == cur_pid:
      pid_match = True

    name_match = False
    if not name:
      name_match = True
    elif name == cur_name:
      name_match = True

    return pid_match and name_match

  def _check_connection(self, local_end, remote_end, process):
    """
    Check whether the connection is of interest or not
    :param local_end: Local connection end point, e.g., 'host1:port1'
    :param remote_end: Remote connection end point, e.g., 'host2:port2'
    :param process: Current connection 's process info, e.g., '1234/firefox'
    :return: a tuple of (local_end, remote_end, True/False); e.g. ('host1_23232', 'host2_2222', True)
    """
    # check tcp end points
    cur_host1, cur_port1 = self._get_tuple(local_end.split(':'))
    cur_host2, cur_port2 = self._get_tuple(remote_end.split(':'))

    #check whether the connection is interested or not by checking user input
    host_port_is_interested = False
    for host1,port1,host2,port2 in self.input_connections:
      if self._match_host_port(host1, port1, cur_host1, cur_port1) and self._match_host_port(host2, port2, cur_host2, cur_port2):
        host_port_is_interested = True
        break
      if self._match_host_port(host1, port1, cur_host2, cur_port2) and self._match_host_port(host2, port2, cur_host1, cur_port1):
        host_port_is_interested = True
        break

    # check whether the connection is interested or not by checking process names given in the config
    process_is_interested = False
    for pid, name in self.input_processes:
      if self._match_processes(pid, name, process):
        process_is_interested = True
        break

    return cur_host1 + '_' + cur_port1, cur_host2 + '_' + cur_port2, host_port_is_interested and process_is_interested

  def _add_data_line(self, data, col, value, ts):
    """
    Append the data point to the dictionary of "data"
    :param data: The dictionary containing all data
    :param col: The sub-metric name e.g. 'host1_port1.host2_port2.SendQ'
    :param value: integer
    :param ts: timestamp
    :return: None
    """
    if col in self.column_csv_map:
      out_csv = self.column_csv_map[col]
    else:
      out_csv = self.get_csv(col)   #  column_csv_map[] is assigned in get_csv()
      data[out_csv] = []
    data[out_csv].append(ts + "," + value)

  def parse(self):
    """
    Parse the netstat output file
    :return: status of the metric parse
    """
    #sample netstat output: 2014-04-02 15:44:02.86612	tcp     9600      0 host1.localdomain.com.:21567 remote.remotedomain.com:51168 ESTABLISH pid/process
    data = {}  # stores the data of each sub-metric
    for infile in self.infile_list:
      logger.info('Processing : %s',infile)
      timestamp_format = None
      with open(infile) as fh:
        for line in fh:
          if 'ESTABLISHED' not in line:
            continue
          words = line.split()
          if len(words) < 8 or words[2] != 'tcp':
            continue
          ts = words[0] + " " + words[1]
          if not timestamp_format or timestamp_format == 'unknown':
            timestamp_format = naarad.utils.detect_timestamp_format(ts)
          if timestamp_format == 'unknown':
            continue
          ts = naarad.utils.get_standardized_timestamp(ts, timestamp_format)
          if self.ts_out_of_range(ts):
            continue
          # filtering based on user input; (local socket, remote socket, pid/process)
          local_end, remote_end, interested = self._check_connection(words[5], words[6], words[8])
          if interested:
            self._add_data_line(data, local_end + '.' + remote_end + '.RecvQ', words[3], ts)
            self._add_data_line(data, local_end + '.' + remote_end + '.SendQ', words[4], ts)
    #post processing, putting data in csv files;
    for csv in data.keys():
      self.csv_files.append(csv)
      with open(csv, 'w') as fh:
        fh.write('\n'.join(sorted(data[csv])))
    return True
