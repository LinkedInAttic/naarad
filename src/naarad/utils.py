# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
import calendar
import ConfigParser
import datetime
import logging
import numpy
import os
import pytz
from pytz import timezone
import re
import sys
import time
import urllib

from naarad.metrics.sar_metric import SARMetric
from naarad.metrics.metric import Metric
from naarad.graphing.plot_data import PlotData

logger = logging.getLogger('naarad.utils')

def is_valid_url(url):
  """
  Check if a given string is in the correct URL format or not

  :param str url:
  :return: True or False
  """
  regex = re.compile(
      r'^(?:http|ftp)s?://' # http:// or https://
      r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
      r'localhost|' #localhost...
      r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
      r'(?::\d+)?' # optional port
      r'(?:/?|[/?]\S+)$', re.IGNORECASE)
  if regex.match(url):
    logger.info( "URL given as config")
    return True
  else:
    return False

def download_file(url):
  """
  Download a file pointed to by url to a temp file on local disk

  :param str url:
  :return: local_file
  """
  try:
    (local_file, headers) = urllib.urlretrieve(url)
  except:
    sys.exit("ERROR: Problem downloading config file. Please check the URL (" + url + "). Exiting...")
  return local_file

def sanitize_string_section_name(string):
  string = string.replace('/', '_')
  string = string.replace('%', '_')
  return string

def is_valid_metric_name(metric_name):
  """
  check the validity of metric_name in config; the metric_name will be used for creation of sub-dir, so only contains: alphabet, digits , '.', '-' and '_'
  :param str metric_name: metric_name
  :return: True if valid
  """
  reg=re.compile('^[a-zA-Z0-9\.\-\_]+$')
  if reg.match(metric_name) and not metric_name.startswith('.'):
    return True
  else:
    return False

def get_run_time_period(run_steps):
  """
  This method finds the time range which covers all the Run_Steps

  :param run_steps: list of Run_Step objects
  :return: tuple of start and end timestamps
  """
  init_ts_start = time.strftime("%Y-%m-%d %H:%M:%S")
  ts_start = init_ts_start
  ts_end = '0'
  for run_step in run_steps:
    if run_step.ts_start and run_step.ts_end:
      if run_step.ts_start < ts_start:
        ts_start = run_step.ts_start
      if run_step.ts_end > ts_end:
        ts_end = run_step.ts_end
  if ts_end == '0':
    ts_end = None
  if ts_start == init_ts_start:
    ts_start = None
  logger.info('get_run_time_period range returned ' + str(ts_start) + ' to ' + str(ts_end))
  return ts_start, ts_end

def parse_basic_metric_options(config_obj, section):
  """
  Parse basic options from metric sections of the config
  :param config_obj: ConfigParser object
  :param section: Section name
  :return: all the parsed options
  """
  infile = None
  aggr_hosts = None
  aggr_metrics = None
  ts_start = None
  ts_end = None
  precision = None
  hostname = "localhost"
  rule_strings = {}
  try:
    if config_obj.has_option(section, 'hostname'):
      hostname = config_obj.get(section, 'hostname')
      config_obj.remove_option(section, 'hostname')
    else:
      logger.info('No hostname is found in section %s ' % section)
    
    #'infile' is not mandatory for aggregate metrics
    if config_obj.has_option(section,'infile'):
      infile = config_obj.get(section, 'infile')
      config_obj.remove_option(section, 'infile')

    label = sanitize_string_section_name(section)
    if config_obj.has_option(section, 'ts_start'):
      ts_start = config_obj.get(section, 'ts_start')
      config_obj.remove_option(section, 'ts_start')
    if config_obj.has_option(section, 'ts_end'):
      ts_end = config_obj.get(section, 'ts_end')
      config_obj.remove_option(section, 'ts_end')
    if config_obj.has_option(section, 'precision'):
      precision = config_obj.get(section, 'precision')
      config_obj.remove_option(section, 'precision')
      
    #support aggregate metrics, which take aggr_hosts and aggr_metrics
    if config_obj.has_option(section, 'aggr_hosts'):
      aggr_hosts = config_obj.get(section, 'aggr_hosts')
      config_obj.remove_option(section, 'aggr_hosts')
    else: 
      logger.info('No aggr_hosts is found in section %s ' % section)
    if config_obj.has_option(section, 'aggr_metrics'):
      aggr_metrics = config_obj.get(section, 'aggr_metrics')
      config_obj.remove_option(section, 'aggr_metrics')
    else: 
      logger.info('No aggr_metrics is found in section %s ' % section)
      
    kwargs = dict(config_obj.items(section))
    for key in kwargs.keys():
      if key.endswith('.sla'):
        rule_strings[key.replace('.sla','')] = kwargs[key]
        del kwargs[key]
  except ConfigParser.NoOptionError:
    logger.exception("Exiting.... some mandatory options are missing from the config file in section: " + section)
    sys.exit()
  return hostname, infile, aggr_hosts, aggr_metrics, label, ts_start, ts_end, precision, kwargs, rule_strings

def parse_metric_section(config_obj, section, metric_classes,  metrics, aggregate_metric_classes, outdir_default, resource_path):
  """
  Parse a metric section and create a Metric object
  :param config_obj: ConfigParser object
  :param section: Section name
  :param metric_classes: List of valid metric types
  :param metrics: List of all regular metric objects (used by aggregate metric)
  :param aggregate_metric_classes: List of all valid aggregate metric types
  :param outdir_default: Default output directory
  :param resource_path: Default resource directory
  :return: An initialized Metric object
  """
  hostname, infile, aggr_hosts, aggr_metrics, label, ts_start, ts_end, precision, kwargs, rule_strings = parse_basic_metric_options(config_obj, section)
  #TODO: Make user specify metric_type in config and not infer from section
  metric_type = section.split('-')[0]
  if metric_type in metric_classes: # regular metrics
    new_metric = metric_classes[metric_type](section, infile, hostname, outdir_default, resource_path, label, ts_start, ts_end, rule_strings, **kwargs)
  elif metric_type in aggregate_metric_classes:       #aggregate metrics     
    new_metric = aggregate_metric_classes[metric_type](section, aggr_hosts, aggr_metrics, metrics, outdir_default, resource_path, label, ts_start, ts_end, rule_strings, **kwargs)
  else:            # new metrics. 
    new_metric = Metric(section, infile, hostname, outdir_default, resource_path, label, ts_start, ts_end, rule_strings, **kwargs)

  if config_obj.has_option(section, 'ignore') and config_obj.getint(section, 'ignore') == 1:
    new_metric.ignore = True
  if config_obj.has_option(section, 'calc_metrics'):
    new_metric.calc_metrics = config_obj.get(section, 'calc_metrics')
  new_metric.precision = precision
  return new_metric

def parse_run_step_section(config_obj, section):
  """
  Parse a RUN-STEP section in the config to return a Run_Step object
  :param config_obj: ConfigParser objection
  :param section: Section name
  :return: an initialized Run_Step object
  """
  run_type = config_obj.get(section, 'run_type')
  run_cmd = config_obj.get(section, 'run_cmd')
  if config_obj.has_option(section, 'call_type'):
    call_type = config_obj.get(section, 'call_type')
  else:
    call_type = 'local'
  if call_type == 'local':
    run_step_obj = Local_Cmd(run_type, run_cmd, call_type)
  else:
    logger.warning('Unsupported RUN_STEP supplied, call_type should be local')
    run_step_obj = None
  return run_step_obj

def parse_graph_section(config_obj, section, outdir_default, indir_default):
  """
  Parse the GRAPH section of the config to extract useful values
  :param config_obj: ConfigParser object
  :param section: Section name
  :param outdir_default: Default output directory passed in args
  :param indir_default: Default input directory passed in args
  :return: List of options extracted from the GRAPH section
  """
  graph_timezone = None
  graphing_library = 'matplotlib'
  crossplots = []

  if config_obj.has_option(section, 'graphing_library'):
    graphing_library = config_obj.get(section, 'graphing_library')
  if config_obj.has_option(section, 'graphs'):
    graphs_string = config_obj.get(section, 'graphs')
    crossplots = graphs_string.split()
    # Supporting both outdir and output_dir
  if config_obj.has_option(section, 'outdir'):
    outdir_default = config_obj.get(section, 'outdir')
  if config_obj.has_option(section, 'output_dir'):
    outdir_default = config_obj.get(section, 'output_dir')
  if config_obj.has_option(section, 'input_dir'):
    indir_default = config_obj.get(section, 'input_dir')
  if config_obj.has_option(section, 'graph_timezone'):
    graph_timezone = config_obj.get(section, 'graph_timezone')
    if graph_timezone not in ("UTC", "PST", "PDT"):
      logger.warn('Unsupported timezone ' + graph_timezone + ' specified in option graph_timezone. Will use UTC instead')
      graph_timezone = "UTC"
  return graphing_library, crossplots, outdir_default, indir_default, graph_timezone

def reconcile_timezones(begin_ts, ts_timezone, graph_timezone):
  if not graph_timezone:
    return begin_ts
  # Converting timestamp strings to be in timezone: graph_timezone
  # We only support UTC and PDT
  if graph_timezone != ts_timezone:
    utc = pytz.utc
    pst = timezone('US/Pacific')
    if graph_timezone == "UTC":
      # Assume timezone is PDT
      try:
        dt = pst.localize(datetime.datetime.strptime(begin_ts,"%Y-%m-%d %H:%M:%S"))
      except ValueError:
        dt = pst.localize(datetime.datetime.strptime(begin_ts,"%Y-%m-%d %H:%M:%S.%f"))
      begin_ts = dt.astimezone(utc).strftime("%Y-%m-%d %H:%M:%S.%f")
    else:
      # Assume timezone is UTC since graph_timezone is PDT
      try:
        dt = utc.localize(datetime.datetime.strptime(begin_ts,"%Y-%m-%d %H:%M:%S"))
      except ValueError:
        dt = utc.localize(datetime.datetime.strptime(begin_ts,"%Y-%m-%d %H:%M:%S.%f"))
      begin_ts = dt.astimezone(pst).strftime("%Y-%m-%d %H:%M:%S.%f")
  return begin_ts

def convert_to_unixts(ts_string):
  try:
    dt_obj = datetime.datetime.strptime(ts_string, "%Y-%m-%d %H:%M:%S.%f")
  except ValueError:
    dt_obj = datetime.datetime.strptime(ts_string, "%Y-%m-%d %H:%M:%S")
  return float(calendar.timegm(dt_obj.utctimetuple())*1000.0 + dt_obj.microsecond/1000.0)

def is_number(string):
  try:
    float(string)
    return True
  except ValueError:
    return False

def get_all_sar_objects(metrics, indir, hostname, output_directory, label, ts_start, ts_end, options):
  metrics = []
  sar_types = ('device', 'cpuusage', 'cpuhz', 'memory', 'memutil', 'paging')
  for sar_metric_type in sar_types:
    #infile = indir + '/' + 'sar.' + sar_metric_type + '.out'
    infile = os.path.join(indir, 'sar.' + sar_metric_type + '.out')
    if os.path.exists(infile):
      obj_type = 'SAR-' + sar_metric_type
      metric = SARMetric(obj_type, infile, hostname, output_directory, label, ts_start, ts_end, options)
      metrics.append(metric)
  return metrics

def sanitize_string(string):
  string = string.replace('/', '-per-')
  if string.startswith('%'):
    string = string.replace('%', 'percent-')
  else:
    string = string.replace('.%', '.percent-') #handle the cases of "all.%sys"
    string = string.replace('%', '-percent-')
  return string

def get_default_csv(output_directory, val):
  val = sanitize_string(val)
  return os.path.join(output_directory, val + '.csv')

def convert_to_24hr_format(ts):
  words = ts.split()
  if len(words) == 1:
    return ts
  if words[1] == 'PM':
    tmp = words[0].split(':')
    if tmp[0] != '12':
      hour = int(tmp[0]) + 12
      tmp[0] = str(hour)
    ts = ":".join(tmp)
  elif words[1] == 'AM':
    tmp = words[0].split(':')
    if tmp[0] == '12':
      tmp[0] = '00'
    ts = ":".join(tmp)
  return ts

def get_merged_csvname(output_directory, vals):
  return os.path.join(output_directory, '-'.join(vals) + '.csv')

def get_merged_charttitle(vals):
  return " vs ".join(vals)

def get_merged_plot_link_name(vals):
  return '-'.join(vals)

def get_merged_png_name(vals):
  # The merged_png_name format is relied upon by naarad.reporting.report.is_correlated_image method.
  return '-'.join(vals)

def generate_html_report(output_directory, html_string):
  htmlfilename = os.path.join(output_directory, 'Report.html')
  with open(htmlfilename, 'w') as htmlf:
    header = '<html><head><title>naarad analysis report</title>'
    dygraphs_include = '''<script type='text/javascript'
      src='http://dygraphs.com/dygraph-combined.js'></script>
      '''
    sorttable_include = '<script type="text/javascript" src="http://www.kryogenix.org/code/browser/sorttable/sorttable.js"></script>'
    body = '</head><body>'
    footer = '</body></html>'
    htmlf.write(header)
    htmlf.write(sorttable_include)
    htmlf.write(dygraphs_include)
    htmlf.write(body)
    htmlf.write(html_string)
    htmlf.write(footer)

def tscsv_nway_file_merge(outfile, filelist, filler):
  logger.info('called nway merge with %s', filelist)
  with open(outfile, 'w') as outf:
    filehandlers = [None] * len(filelist)
    currlines = [None] * len(filelist)
    for i in range(len(filelist)):
      try:
        filehandlers[i] = open(filelist[i], 'r')
      except IOError:
        logger.error('Cannot open: ' +  filelist[i])
        return
      currlines[i] = filehandlers[i].readline().strip()
    while True:
      # Assuming logs won't have far future dates - 1 yr max since sometimes people have logs in near future dates
      future_time = str( datetime.datetime.utcnow() + datetime.timedelta(days=365))
      min_ts = future_time
      for i in range(len(currlines)):
        if currlines[i] == "":
          continue
        ts = currlines[i].split(',')[0]
        if ts < min_ts:
          min_ts = ts
      if min_ts == future_time:
        break
      outwords = []
      outwords.append(min_ts)
      for i in range(len(currlines)):
        if currlines[i] == "":
          outwords.append(filler)
        else:
          ts = currlines[i].split(',')[0]
          val = currlines[i].split(',')[1]
          if ts == min_ts:
            outwords.append(val)
            currlines[i] = filehandlers[i].readline().strip()
          else:
            outwords.append(filler)
      outf.write( ','.join(outwords) + '\n' )

def nway_plotting(crossplots, metrics, output_directory, resource_path):
  listlen = len(crossplots)
  if listlen == 0:
    return ''
  i = 0
  correlated_plots = []
  #GC.appstop,all GC.alloc,GC.alloc-rate GC.promo,GC.gen0t,GC.gen0sys
  while i < listlen:
    plot = crossplots[i]
    vals = plot.split(',')
    i += 1
    if not 'all' in vals:
      plot_data = []
      for val in vals:
        csv_file = get_default_csv(output_directory, val)
        plot_data.append(PlotData(input_csv=csv_file, csv_column=1, series_name=sanitize_string(val), y_label=sanitize_string(val), precision=None, graph_height=500, graph_width=1200, graph_type='line'))
      png_name = get_merged_plot_link_name(vals)
      graphed, div_file = Metric.graphing_modules['matplotlib'].graph_data(plot_data, output_directory, resource_path, png_name)
      if graphed:
        correlated_plots.append(div_file)
    else:
      vals.remove('all')
      for metric in metrics:
        for csv in metric.csv_files:
          csv_filename = csv.split('/')[-1]
          metric_name = '.'.join(csv_filename.split('.')[0:-1])
          if metric_name in vals:
            continue
          new_val = []
          new_val.extend(vals)
          new_val.append(metric_name)
          new_val_str = ','.join(new_val)
          crossplots.append(new_val_str)
          listlen += 1
  return correlated_plots

def normalize_float_for_display(data_val):
  try:
    data_val = float(data_val)
  except ValueError:
    return data_val
  if data_val > 1:
    return '%.2f' % round(data_val, 2)
  else:
    return '%s' % float('%.2g' % data_val)

def calculate_stats(data_list, stats_to_calculate = ['mean', 'std'], percentiles_to_calculate = []):
  """
  Calculate statistics for given data.

  :param list data_list: List of floats
  :param list stats_to_calculate: List of strings with statistics to calculate. Supported stats are defined in constant stats_to_numpy_method_map
  :param list percentiles_to_calculate: List of floats that defined which percentiles to calculate.
  :return: tuple of dictionaries containing calculated statistics and percentiles
  """
  stats_to_numpy_method_map = {
      'mean' : numpy.mean,
      'avg' : numpy.mean,
      'std' : numpy.std,
      'standard_deviation' : numpy.std,
      'median' : numpy.median,
      'min' : numpy.amin,
      'max' : numpy.amax
      }
  calculated_stats = {}
  calculated_percentiles = {}
  for stat in stats_to_calculate:
    if stat in stats_to_numpy_method_map.keys():
      calculated_stats[stat] = stats_to_numpy_method_map[stat](data_list)
    else:
      logger.error("Unsupported stat : " + str(stat))
  for percentile in percentiles_to_calculate:
    if isinstance(percentile, float) or isinstance(percentile, int):
      calculated_percentiles[percentile] = numpy.percentile(data_list, percentile)
    else:
      logger.error("Unsupported percentile requested (should be int or float): " + str(percentile))
  return calculated_stats, calculated_percentiles

def is_valid_file(filename):
  """
  Check if the specifed file exists and is not empty

  :param filename: full path to the file that needs to be checked
  :return: Status, Message
  """
  if os.path.exists(filename):
    if not os.path.getsize(filename):
      logger.warning('%s : file is empty.', filename)
      return False
  else:
    logger.warning('%s : file does not exist.', filename)
    return False
  return True

def detect_timestamp_format(timestamp):
  """
  Given an input timestamp string, determine what format is it likely in.

  :param string timestamp: the timestamp string for which we need to determine format
  :return: best guess timestamp format
  """
  time_formats = {'epoch': re.compile(r'^[0-9]{10}$'), 'epoch_ms': re.compile(r'^[0-9]{13}$'),
                  '%Y-%m-%d %H:%M:%S': re.compile(r'^[0-9]{4}-[0-1][0-9]-[0-3][0-9] [0-2][0-9]:[0-5][0-9]:[0-5][0-9]$'),
                  '%Y-%m-%dT%H:%M:%S': re.compile(r'^[0-9]{4}-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]$'),
                  '%Y-%m-%d_%H:%M:%S': re.compile(r'^[0-9]{4}-[0-1][0-9]-[0-3][0-9]_[0-2][0-9]:[0-5][0-9]:[0-5][0-9]$'),
                  '%Y-%m-%d %H:%M:%S.%f': re.compile(r'^[0-9]{4}-[0-1][0-9]-[0-3][0-9] [0-2][0-9]:[0-5][0-9]:[0-5][0-9].[0-9]+$'),
                  '%Y-%m-%dT%H:%M:%S.%f': re.compile(r'^[0-9]{4}-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9].[0-9]+$'),
                  '%Y-%m-%d_%H:%M:%S.%f': re.compile(r'^[0-9]{4}-[0-1][0-9]-[0-3][0-9]_[0-2][0-9]:[0-5][0-9]:[0-5][0-9].[0-9]+$'),
                  '%Y%m%d %H:%M:%S': re.compile(r'^[0-9]{4}[0-1][0-9][0-3][0-9] [0-2][0-9]:[0-5][0-9]:[0-5][0-9]$'),
                  '%Y%m%dT%H:%M:%S': re.compile(r'^[0-9]{4}[0-1][0-9][0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]$'),
                  '%Y%m%d_%H:%M:%S': re.compile(r'^[0-9]{4}[0-1][0-9][0-3][0-9]_[0-2][0-9]:[0-5][0-9]:[0-5][0-9]$'),
                  '%Y%m%d %H:%M:%S.%f': re.compile(r'^[0-9]{4}[0-1][0-9][0-3][0-9] [0-2][0-9]:[0-5][0-9]:[0-5][0-9].[0-9]+$'),
                  '%Y%m%dT%H:%M:%S.%f': re.compile(r'^[0-9]{4}[0-1][0-9][0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9].[0-9]+$'),
                  '%Y%m%d_%H:%M:%S.%f': re.compile(r'^[0-9]{4}[0-1][0-9][0-3][0-9]_[0-2][0-9]:[0-5][0-9]:[0-5][0-9].[0-9]+$'),
                  '%H:%M:%S': re.compile(r'^[0-2][0-9]:[0-5][0-9]:[0-5][0-9]$'),
                  '%H:%M:%S.%f': re.compile(r'^[0-2][0-9]:[0-5][0-9]:[0-5][0-9].[0-9]+$'),
                  '%Y-%m-%dT%H:%M:%S.%f%z': re.compile(r'^[0-9]{4}-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9].[0-9]+[+-][0-9]{4}$'),
  }
  for time_format in time_formats:
    if re.match(time_formats[time_format],timestamp):
      return time_format
  return 'unknown'

def get_standardized_timestamp(timestamp, ts_format):
  """
  Given a timestamp string, return a time stamp in the format YYYY-MM-DD HH:MM:SS.sss. If no date is present in
  timestamp then today's date will be added as a prefix
  """
  if not timestamp:
    return None
  if timestamp == 'now':
    timestamp = str(datetime.datetime.now())
  if not ts_format:
    ts_format = detect_timestamp_format(timestamp)

  if ts_format == '%Y-%m-%d %H:%M:%S.%f':
    return timestamp
  elif ts_format == 'unknown':
    logger.error('Unable to determine timestamp format for : %s', timestamp)
    return -1
  elif ts_format == 'epoch':
    ts = datetime.datetime.utcfromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S.%f')
  elif ts_format == 'epoch_ms':
    ts = datetime.datetime.utcfromtimestamp(int(timestamp) / 1000).strftime('%Y-%m-%d %H:%M:%S.%f')
  elif ts_format in ('%H:%M:%S', '%H:%M:%S.%f'):
    date_today = str(datetime.date.today())
    ts = datetime.datetime.strptime(date_today + ' ' + timestamp,'%Y-%m-%d ' + ts_format).strftime('%Y-%m-%d %H:%M:%S.%f')
  else:
    ts = datetime.datetime.strptime(timestamp,ts_format).strftime('%Y-%m-%d %H:%M:%S.%f')
  return ts
