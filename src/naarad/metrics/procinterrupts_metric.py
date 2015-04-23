# coding=utf-8
"""
Copyright 2013 LinkedIn Corp. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import datetime
import logging
import os
import re

from naarad.metrics.metric import Metric
import naarad.utils
from naarad.naarad_constants import important_sub_metrics_import

logger = logging.getLogger('naarad.metrics.ProcInterruptsMetric')


class ProcInterruptsMetric(Metric):
  """
  Metric parser for /proc/interrupts log file.
  This parser will parse interrupts per core and per IRQ and store the differences between intervals. Thus the first entry will be considered 0.
  This is because the interrupts are an increasing counter rather than per interval.

  Extra Configurations:

    You can specify CPUS= in the configuration file to define which CPUs to look at. For example to have the CPUs 0,
    3, 4, and 8 then specify the following line in the PROCINTERRUPTS section of the configurations:

    [PROCINTERRUPTS]
    CPUS=CPU0 CPU3 CPU4 CPU8
    ...

  You can of course use the other general metric settings such as ts_start, infile, etc.
  """
  def __init__(self, metric_type, infile_list, hostname, outdir, resource_path, label, ts_start, ts_end, rule_strings,
               important_sub_metrics, anomaly_detection_metrics, **other_options):
    Metric.__init__(self, metric_type, infile_list, hostname, outdir, resource_path, label, ts_start, ts_end, rule_strings,
                    important_sub_metrics, anomaly_detection_metrics)
    if not self.important_sub_metrics and self.metric_type in important_sub_metrics_import.keys():
      self.important_sub_metrics = important_sub_metrics_import[self.metric_type]
    self.options = None

    self.CPUS = None
    for (key, val) in other_options.iteritems():
      setattr(self, key, val.split())

  def get_csv(self, cpu, device=None):
    """
    Returns the CSV file related to the given metric. The metric is determined by the cpu and device.
    The cpu is the CPU as in the interrupts file for example CPU12.
    The metric is a combination of the CPU and device. The device consists of IRQ #, the irq device ASCII name.

                                      CPU0   CPU1
    2014-10-29 00:27:42.15161    59:    29      2    IR-IO-APIC-edge    timer
                                  ^      ^      ^          ^              ^
                                  |      |      |          |              |
                                IRQ#   Value  Value   IRQ Device       Ascii Name

    This would produce a metric CPU0.timer-IRQ59 and CPU1.timer-IRQ59 so one per IRQ per CPU.

    :param cpu: The name of the cpu given as CPU#.
    :param device: The device name as given by the system. <ASCII name>-IRQ<IRQ #>
    :return: The CSV file for the metric.
    """
    cpu = naarad.utils.sanitize_string(cpu)
    if device is None:
      outcsv = os.path.join(self.resource_directory, "{0}.{1}.csv".format(self.label, cpu))
      self.csv_column_map[outcsv] = cpu
    else:
      device = naarad.utils.sanitize_string(device)
      outcsv = os.path.join(self.resource_directory, "{0}.{1}.{2}.csv".format(self.label, cpu, device))
      self.csv_column_map[outcsv] = cpu + '.' + device
    return outcsv

  def is_header_line(self, line):
    """
    Checks to see if the line is a header line.
    The header line style is currently:

      2014-10-29 00:28:42.15161        CPU0   CPU1   CPU2   CPU3  ...

    :param line: The line of the file to check.
    :return: Boolean of true or false of whether line is header line or not.
    """
    return 'CPU' in line

  def find_header(self, infile):
    """
    Parses the file and tries to find the header line. The header line has format:

      2014-10-29 00:28:42.15161        CPU0   CPU1   CPU2   CPU3  ...

    So should always have CPU# for each core. This function verifies a good header and
    returns the list of CPUs that exist from the header.

    :param infile: The opened file in read mode to find the header.
    :return cpus: A list of the core names so in this example ['CPU0', 'CPU1', ...]
    """
    cpus = []
    for line in infile:  # Pre-processing - Try to find header
      if not is_header_line(line):
        continue
      # Verifying correctness of the header
      cpu_header = line.split()
      for cpu_h in cpu_header[2:]:
        if not cpu_h.startswith('CPU'):
          cpus = []  # Bad header so reset to nothing
          break
        else:
          cpus.append(cpu_h)
      if len(cpus) > 0:  # We found the header
        break
    return cpus

  def parse(self):
    """
    Processes the files for each IRQ and each CPU in terms of the differences.
    Also produces accumulated interrupt count differences for each set of Ethernet IRQs.
    Generally Ethernet has 8 TxRx IRQs thus all are combined so that one can see the overall interrupts being generated by the NIC.

    Simplified Interrupt File Format: (See examples for example log)

                                        CPU0   CPU1
      2014-10-29 00:27:42.15161    59:    29      2    IR-IO-APIC-edge    timer
      2014-10-29 00:27:42.15161    60:  2123      0    IR-PCI-MSI-edge    eth0

                                        CPU0   CPU1
      2014-10-29 00:27:42.15161    59:    29      2    IR-IO-APIC-edge    timer
      2014-10-29 00:27:42.15161    60:  2123      0    IR-PCI-MSI-edge    eth0

    :returns: True or False whether parsing was successful or not.
    """
    if not os.path.isdir(self.outdir):
      os.makedirs(self.outdir)
    if not os.path.isdir(self.resource_directory):
      os.makedirs(self.resource_directory)

    data = {}
    for input_file in self.infile_list:
      logger.info('Processing : %s', input_file)
      timestamp_format = None
      with open(input_file, 'r') as infile:
        # Get the header for this file
        cpus = self.find_header(infile)
        if len(cpus) == 0:  # Make sure we have header otherwise go to next file
          logger.error("Header not found for file: %s", input_file)
          continue

        # Parse the actual file after header
        prev_data = None    # Stores the previous interval's log data
        curr_data = {}      # Stores the current interval's log data
        eth_data = {}
        for line in infile:
          if is_header_line(line):  # New section so save old and aggregate ETH
            prev_data = curr_data
            curr_data = {}
            # New section so store the collected Ethernet data
            # Example Aggregate metric: PROCINTERRUPTS.AGGREGATE.eth0
            for eth in eth_data:
              outcsv = self.get_csv('AGGREGATE', eth)
              if outcsv not in data:
                data[outcsv] = []
              data[outcsv].append(ts + ',' + str(eth_data[eth]))
            eth_data = {}
            continue

          words = line.split()
          if len(words) <= 4:  # Does not have any CPU data so skip
            continue

          # Process timestamp or determine timestamp
          ts = words[0] + " " + words[1]
          if not timestamp_format or timestamp_format == 'unknown':
            timestamp_format = naarad.utils.detect_timestamp_format(ts)
          if timestamp_format == 'unknown':
            continue
          ts = naarad.utils.get_standardized_timestamp(ts, timestamp_format)
          if self.ts_out_of_range(ts):  # See if time is in range
            continue

          # Process data lines
          # Note that some IRQs such as ERR and MIS do not have device nor ascii name
          device = words[2].strip(':')  # Get IRQ Number/Name
          if re.match("\d+", device):
            # Devices with digits need ASCII name if exists
            if (4 + len(cpus)) < len(words):
              device = words[4 + len(cpus)] + "-IRQ" + device
            else:
              device = "IRQ" + device
          else:
            # For devices with IRQ # that aren't digits then has description
            device = "-".join(words[(3 + len(cpus)):]) + "-IRQ" + device

          # Deal with each column worth of data
          for (cpu, datum) in zip(cpus, words[3:]):
            if self.CPUS and cpu not in self.CPUS:  # Skip if config defines which CPUs to look at
              continue
            outcsv = self.get_csv(cpu, device)
            curr_data[outcsv] = int(datum)
            if outcsv in data:
              datum = int(datum) - prev_data[outcsv]  # prev_data exists since outcsv exists in data
            else:
              data[outcsv] = []
              datum = 0  # First data point is set to 0
            # Store data point
            data[outcsv].append(ts + ',' + str(datum))

            # Deal with accumulating aggregate data for Ethernet
            m = re.search("(?P<eth>eth\d)", device)
            if m:
              eth = m.group('eth')
              if eth not in eth_data:
                eth_data[eth] = 0
              eth_data[eth] += datum

    # Post processing, putting data in csv files
    for csv in data.keys():
      self.csv_files.append(csv)
      with open(csv, 'w') as csvf:
        csvf.write('\n'.join(sorted(data[csv])))
    return True
