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

import argparse
import calendar
import ConfigParser
import datetime
import imp
import logging
import numpy
import os
import pytz
from pytz import timezone
import re
import sys
import time
import urllib
from naarad.naarad_imports import metric_classes, aggregate_metric_classes
from naarad.sla import SLA
from naarad.metrics.sar_metric import SARMetric
from naarad.metrics.metric import Metric
from naarad.graphing.plot_data import PlotData
from naarad.run_steps.local_cmd import Local_Cmd
import naarad.naarad_constants as CONSTANTS

logger = logging.getLogger('naarad.utils')


def import_modules(module_dict, is_class_type=True):
  return_dict = {}
  for module_name, module_string in module_dict.items():
    try:
      if is_class_type:
        file_name, class_name = module_string.rsplit('.', 1)
        mod = __import__(file_name, fromlist=[class_name])
        return_dict[module_name] = getattr(mod, class_name)
      else:
        return_dict[module_name] = __import__(module_string, fromlist=[module_string])
    except ImportError:
      pass
  return return_dict


def parse_user_defined_metric_classes(config_obj, metric_classes):
  """
  Parse the user defined metric class information
  :param config_obj: ConfigParser object
  :param metric_classes: list of metric classes to be updated
  :return:
  """
  user_defined_metric_list = config_obj.get('GLOBAL', 'user_defined_metrics').split()
  for udm_string in user_defined_metric_list:
    try:
      metric_name, metric_class_name, metric_file = udm_string.split(':')
    except ValueError:
      logger.error('Bad user defined metric specified')
      continue
    module_name = os.path.splitext(os.path.basename(metric_file))[0]
    try:
      new_module = imp.load_source(module_name, metric_file)
      new_class = getattr(new_module, metric_class_name)
      if metric_name in metric_classes.keys():
        logger.warn('Overriding pre-defined metric class definition for ', metric_name)
      metric_classes[metric_name] = new_class
    except ImportError:
      logger.error('Something wrong with importing a user defined metric class. Skipping metric: ', metric_name)
      continue


def is_valid_url(url):
  """
  Check if a given string is in the correct URL format or not

  :param str url:
  :return: True or False
  """
  regex = re.compile(r"^(http|https|ftp)://[A-Za-z0-9]+(-[A-Za-z0-9]+)*([:][A-Za-z0-9]+(-[A-Za-z0-9]+)*){0,1}"
                     r"([@][A-Za-z0-9]+(-[A-Za-z0-9]+)*){0,1}(\.[A-Za-z0-9]+(-[A-Za-z0-9]+)*)*"
                     r"(:[0-9]{1,5}){0,1}(/[A-Za-z0-9=]*[A-Za-z0-9-._\(\)]*)*([?#&].*)*$")
  if regex.match(url):
    logger.info("URL given as config")
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
  reg = re.compile('^[a-zA-Z0-9\.\-\_]+$')
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
  init_ts_start = get_standardized_timestamp('now', None)
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


def get_rule_strings(config_obj, section):
  """
  Extract rule strings from a section
  :param config_obj: ConfigParser object
  :param section: Section name
  :return: the rule strings
  """
  rule_strings = {}
  kwargs = dict(config_obj.items(section))
  for key in kwargs.keys():
    if key.endswith('.sla'):
      rule_strings[key.replace('.sla', '')] = kwargs[key]
      del kwargs[key]
  return rule_strings, kwargs


def extract_diff_sla_from_config_file(obj, options_file):
  """
  Helper function to parse diff config file, which contains SLA rules for diff comparisons
  """
  rule_strings = {}
  config_obj = ConfigParser.ConfigParser()
  config_obj.optionxform = str
  config_obj.read(options_file)
  for section in config_obj.sections():
    rule_strings, kwargs = get_rule_strings(config_obj, section)
    for (key, val) in rule_strings.iteritems():
      set_sla(obj, section, key, val)


def parse_basic_metric_options(config_obj, section):
  """
  Parse basic options from metric sections of the config
  :param config_obj: ConfigParser object
  :param section: Section name
  :return: all the parsed options
  """
  infile = {}
  aggr_hosts = None
  aggr_metrics = None
  ts_start = None
  ts_end = None
  precision = None
  hostname = "localhost"
  rule_strings = {}
  important_sub_metrics = None
  anomaly_detection_metrics = None

  try:
    if config_obj.has_option(section, 'important_sub_metrics'):
      important_sub_metrics = config_obj.get(section, 'important_sub_metrics').split()
      config_obj.remove_option(section, 'important_sub_metrics')

    if config_obj.has_option(section, 'hostname'):
      hostname = config_obj.get(section, 'hostname')
      config_obj.remove_option(section, 'hostname')

    # 'infile' is not mandatory for aggregate metrics
    if config_obj.has_option(section, 'infile'):
      infile = config_obj.get(section, 'infile').split()
      config_obj.remove_option(section, 'infile')

    label = sanitize_string_section_name(section)
    if config_obj.has_option(section, 'ts_start'):
      ts_start = get_standardized_timestamp(config_obj.get(section, 'ts_start'), None)
      config_obj.remove_option(section, 'ts_start')
    if config_obj.has_option(section, 'ts_end'):
      ts_end = get_standardized_timestamp(config_obj.get(section, 'ts_end'), None)
      config_obj.remove_option(section, 'ts_end')
    if config_obj.has_option(section, 'precision'):
      precision = config_obj.get(section, 'precision')
      config_obj.remove_option(section, 'precision')
    # support aggregate metrics, which take aggr_hosts and aggr_metrics
    if config_obj.has_option(section, 'aggr_hosts'):
      aggr_hosts = config_obj.get(section, 'aggr_hosts')
      config_obj.remove_option(section, 'aggr_hosts')
    if config_obj.has_option(section, 'aggr_metrics'):
      aggr_metrics = config_obj.get(section, 'aggr_metrics')
      config_obj.remove_option(section, 'aggr_metrics')
    if config_obj.has_option(section, 'anomaly_detection_metrics'):
      anomaly_detection_metrics = config_obj.get(section, 'anomaly_detection_metrics').split()
      config_obj.remove_option(section, 'anomaly_detection_metrics')
    rule_strings, other_options = get_rule_strings(config_obj, section)
  except ConfigParser.NoOptionError:
    logger.exception("Exiting.... some mandatory options are missing from the config file in section: " + section)
    sys.exit()
  return (hostname, infile, aggr_hosts, aggr_metrics, label, ts_start, ts_end, precision, other_options, rule_strings,
          important_sub_metrics, anomaly_detection_metrics)


def parse_metric_section(config_obj, section, metric_classes, metrics, aggregate_metric_classes, outdir_default, resource_path):
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
  (hostname, infile, aggr_hosts, aggr_metrics, label, ts_start, ts_end, precision, other_options,
   rule_strings, important_sub_metrics, anomaly_detection_metrics) = parse_basic_metric_options(config_obj, section)

  # TODO: Make user specify metric_type in config and not infer from section
  metric_type = section.split('-')[0]
  if metric_type in aggregate_metric_classes:
    new_metric = initialize_aggregate_metric(section, aggr_hosts, aggr_metrics, metrics, outdir_default, resource_path, label, ts_start, ts_end, rule_strings,
                                             important_sub_metrics, anomaly_detection_metrics, other_options)
  else:
    new_metric = initialize_metric(section, infile, hostname, outdir_default, resource_path, label, ts_start, ts_end, rule_strings, important_sub_metrics,
                                   anomaly_detection_metrics, other_options)

  if config_obj.has_option(section, 'ignore') and config_obj.getint(section, 'ignore') == 1:
    new_metric.ignore = True
  if config_obj.has_option(section, 'calc_metrics'):
    new_metric.calc_metrics = config_obj.get(section, 'calc_metrics')
  new_metric.precision = precision
  return new_metric


def parse_global_section(config_obj, section):
  """
  Parse GLOBAL section in the config to return global settings
  :param config_obj: ConfigParser object
  :param section: Section name
  :return: ts_start and ts_end time
  """
  ts_start = None
  ts_end = None
  if config_obj.has_option(section, 'ts_start'):
    ts_start = get_standardized_timestamp(config_obj.get(section, 'ts_start'), None)
    config_obj.remove_option(section, 'ts_start')
  if config_obj.has_option(section, 'ts_end'):
    ts_end = get_standardized_timestamp(config_obj.get(section, 'ts_end'), None)
    config_obj.remove_option(section, 'ts_end')
  return ts_start, ts_end


def parse_run_step_section(config_obj, section):
  """
  Parse a RUN-STEP section in the config to return a Run_Step object
  :param config_obj: ConfigParser objection
  :param section: Section name
  :return: an initialized Run_Step object
  """
  kill_after_seconds = None
  try:
    run_cmd = config_obj.get(section, 'run_cmd')
    run_rank = int(config_obj.get(section, 'run_rank'))
  except ConfigParser.NoOptionError:
    logger.exception("Exiting.... some mandatory options are missing from the config file in section: " + section)
    sys.exit()
  except ValueError:
    logger.error("Bad run_rank %s specified in section %s, should be integer. Exiting.", config_obj.get(section, 'run_rank'), section)
    sys.exit()
  if config_obj.has_option(section, 'run_type'):
    run_type = config_obj.get(section, 'run_type')
  else:
    run_type = CONSTANTS.RUN_TYPE_WORKLOAD
  if config_obj.has_option(section, 'run_order'):
    run_order = config_obj.get(section, 'run_order')
  else:
    run_order = CONSTANTS.PRE_ANALYSIS_RUN
  if config_obj.has_option(section, 'call_type'):
    call_type = config_obj.get(section, 'call_type')
  else:
    call_type = 'local'
  if config_obj.has_option(section, 'kill_after_seconds'):
    try:
      kill_after_seconds = int(config_obj.get(section, 'kill_after_seconds'))
    except ValueError:
      logger.error("Bad kill_after_seconds %s specified in section %s, should be integer.", config_obj.get(section, 'kill_after_seconds'), section)

  if call_type == 'local':
    run_step_obj = Local_Cmd(run_type, run_cmd, call_type, run_order, run_rank, kill_after_seconds=kill_after_seconds)
  else:
    logger.error('Unsupported RUN_STEP supplied, call_type should be local')
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
  graphing_library = CONSTANTS.DEFAULT_GRAPHING_LIBRARY
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


def parse_report_section(config_obj, section):
  """
  parse the [REPORT] section of a config file to extract various reporting options to be passed to the Report object
  :param: config_obj : configparser object for the config file passed in to naarad
  :param: section: name of the section. 'REPORT' should be passed in here
  :return: report_kwargs: dictionary of Reporting options and values specified in config.
  """
  report_kwargs = {}
  if config_obj.has_option(section, 'stylesheet_includes'):
    report_kwargs['stylesheet_includes'] = config_obj.get(section, 'stylesheet_includes')
  if config_obj.has_option(section, 'javascript_includes'):
    report_kwargs['javascript_includes'] = config_obj.get(section, 'javascript_includes')
  if config_obj.has_option(section, 'header_template'):
    report_kwargs['header_template'] = config_obj.get(section, 'header_template')
  if config_obj.has_option(section, 'footer_template'):
    report_kwargs['footer_template'] = config_obj.get(section, 'footer_template')
  if config_obj.has_option(section, 'summary_content_template'):
    report_kwargs['summary_content_template'] = config_obj.get(section, 'summary_content_template')
  if config_obj.has_option(section, 'summary_page_template'):
    report_kwargs['summary_page_template'] = config_obj.get(section, 'summary_page_template')
  if config_obj.has_option(section, 'metric_page_template'):
    report_kwargs['metric_page_template'] = config_obj.get(section, 'metric_page_template')
  if config_obj.has_option(section, 'client_charting_template'):
    report_kwargs['client_charting_template'] = config_obj.get(section, 'client_charting_template')
  if config_obj.has_option(section, 'diff_client_charting_template'):
    report_kwargs['diff_client_charting_template'] = config_obj.get(section, 'diff_client_charting_template')
  if config_obj.has_option(section, 'diff_page_template'):
    report_kwargs['diff_page_template'] = config_obj.get(section, 'diff_page_template')
  return report_kwargs


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
        dt = pst.localize(datetime.datetime.strptime(begin_ts, "%Y-%m-%d %H:%M:%S"))
      except ValueError:
        dt = pst.localize(datetime.datetime.strptime(begin_ts, "%Y-%m-%d %H:%M:%S.%f"))
      begin_ts = dt.astimezone(utc).strftime("%Y-%m-%d %H:%M:%S.%f")
    else:
      # Assume timezone is UTC since graph_timezone is PDT
      try:
        dt = utc.localize(datetime.datetime.strptime(begin_ts, "%Y-%m-%d %H:%M:%S"))
      except ValueError:
        dt = utc.localize(datetime.datetime.strptime(begin_ts, "%Y-%m-%d %H:%M:%S.%f"))
      begin_ts = dt.astimezone(pst).strftime("%Y-%m-%d %H:%M:%S.%f")
  return begin_ts


def convert_to_unixts(ts_string):
  try:
    dt_obj = datetime.datetime.strptime(ts_string, "%Y-%m-%d %H:%M:%S.%f")
  except ValueError:
    dt_obj = datetime.datetime.strptime(ts_string, "%Y-%m-%d %H:%M:%S")
  return float(calendar.timegm(dt_obj.utctimetuple()) * 1000.0 + dt_obj.microsecond / 1000.0)


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
    # infile = indir + '/' + 'sar.' + sar_metric_type + '.out'
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
    string = string.replace('.%', '.percent-')  # handle the cases of "all.%sys"
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
        logger.error('Cannot open: ' + filelist[i])
        return
      currlines[i] = filehandlers[i].readline().strip()
    while True:
      # Assuming logs won't have far future dates - 1 yr max since sometimes people have logs in near future dates
      future_time = str(datetime.datetime.utcnow() + datetime.timedelta(days=365))
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
      outf.write(','.join(outwords) + '\n')


def nway_plotting(crossplots, metrics, output_directory, resource_path, graphing_library):
  listlen = len(crossplots)
  if listlen == 0:
    return ''
  i = 0
  correlated_plots = []
  # GC.appstop,all GC.alloc,GC.alloc-rate GC.promo,GC.gen0t,GC.gen0sys
  while i < listlen:
    plot = crossplots[i]
    vals = plot.split(',')
    i += 1
    if 'all' not in vals:
      plot_data = []
      for val in vals:
        csv_file = get_default_csv(output_directory, val)
        plot_data.append(PlotData(input_csv=csv_file, csv_column=1, series_name=sanitize_string(val), y_label=sanitize_string(val), precision=None,
                                  graph_height=500, graph_width=1200, graph_type='line'))
      png_name = get_merged_plot_link_name(vals)
      graphed, div_file = Metric.graphing_modules[graphing_library].graph_data(plot_data, output_directory, resource_path, png_name)
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


def calculate_stats(data_list, stats_to_calculate=['mean', 'std'], percentiles_to_calculate=[]):
  """
  Calculate statistics for given data.

  :param list data_list: List of floats
  :param list stats_to_calculate: List of strings with statistics to calculate. Supported stats are defined in constant stats_to_numpy_method_map
  :param list percentiles_to_calculate: List of floats that defined which percentiles to calculate.
  :return: tuple of dictionaries containing calculated statistics and percentiles
  """
  stats_to_numpy_method_map = {
      'mean': numpy.mean,
      'avg': numpy.mean,
      'std': numpy.std,
      'standard_deviation': numpy.std,
      'median': numpy.median,
      'min': numpy.amin,
      'max': numpy.amax
  }
  calculated_stats = {}
  calculated_percentiles = {}
  if len(data_list) == 0:
    return calculated_stats, calculated_percentiles
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
  time_formats = {
      'epoch': re.compile(r'^[0-9]{10}$'),
      'epoch_ms': re.compile(r'^[0-9]{13}$'),
      'epoch_fraction': re.compile(r'^[0-9]{10}\.[0-9]{3,9}$'),
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
      '%Y-%m-%dT%H:%M:%S.%f%z': re.compile(r'^[0-9]{4}-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9].[0-9]+[+-][0-9]{4}$')
  }
  for time_format in time_formats:
    if re.match(time_formats[time_format], timestamp):
      return time_format
  return 'unknown'


def get_standardized_timestamp(timestamp, ts_format):
  """
  Given a timestamp string, return a time stamp in the epoch ms format. If no date is present in
  timestamp then today's date will be added as a prefix before conversion to epoch ms
  """
  if not timestamp:
    return None
  if timestamp == 'now':
    timestamp = str(datetime.datetime.now())
  if not ts_format:
    ts_format = detect_timestamp_format(timestamp)
  try:
    if ts_format == 'unknown':
      logger.error('Unable to determine timestamp format for : %s', timestamp)
      return -1
    elif ts_format == 'epoch':
      ts = int(timestamp) * 1000
    elif ts_format == 'epoch_ms':
      ts = timestamp
    elif ts_format == 'epoch_fraction':
      ts = int(timestamp[:10]) * 1000 + int(timestamp[11:])
    elif ts_format in ('%H:%M:%S', '%H:%M:%S.%f'):
      date_today = str(datetime.date.today())
      dt_obj = datetime.datetime.strptime(date_today + ' ' + timestamp, '%Y-%m-%d ' + ts_format)
      ts = calendar.timegm(dt_obj.utctimetuple()) * 1000 + dt_obj.microsecond / 1000
    else:
      dt_obj = datetime.datetime.strptime(timestamp, ts_format)
      ts = calendar.timegm(dt_obj.utctimetuple()) * 1000 + dt_obj.microsecond / 1000
  except ValueError:
    return -1
  return str(ts)


def set_sla(obj, metric, sub_metric, rules):
  """
  Extract SLAs from a set of rules
  """
  if not hasattr(obj, 'sla_map'):
    return False
  rules_list = rules.split()
  for rule in rules_list:
    if '<' in rule:
      stat, threshold = rule.split('<')
      sla = SLA(metric, sub_metric, stat, threshold, 'lt')
    elif '>' in rule:
      stat, threshold = rule.split('>')
      sla = SLA(metric, sub_metric, stat, threshold, 'gt')
    else:
      if hasattr(obj, 'logger'):
        obj.logger.error('Unsupported SLA type defined : ' + rule)
      sla = None
    obj.sla_map[metric][sub_metric][stat] = sla
    if hasattr(obj, 'sla_list'):
      obj.sla_list.append(sla)  # TODO : remove this once report has grading done in the metric tables
  return True


def check_slas(metric):
  """
  Check if all SLAs pass
  :return: 0 (if all SLAs pass) or the number of SLAs failures
  """
  if not hasattr(metric, 'sla_map'):
    return
  for metric_label in metric.sla_map.keys():
    for sub_metric in metric.sla_map[metric_label].keys():
      for stat_name in metric.sla_map[metric_label][sub_metric].keys():
        sla = metric.sla_map[metric_label][sub_metric][stat_name]
        if stat_name[0] == 'p' and hasattr(metric, 'calculated_percentiles'):
          if sub_metric in metric.calculated_percentiles.keys():
            percentile_num = int(stat_name[1:])
            if isinstance(percentile_num, float) or isinstance(percentile_num, int):
              if percentile_num in metric.calculated_percentiles[sub_metric].keys():
                if not sla.check_sla_passed(metric.calculated_percentiles[sub_metric][percentile_num]):
                  logger.info("Failed SLA for " + sub_metric)
                  metric.status = CONSTANTS.SLA_FAILED
        if sub_metric in metric.calculated_stats.keys() and hasattr(metric, 'calculated_stats'):
          if stat_name in metric.calculated_stats[sub_metric].keys():
            if not sla.check_sla_passed(metric.calculated_stats[sub_metric][stat_name]):
              logger.info("Failed SLA for " + sub_metric)
              metric.status = CONSTANTS.SLA_FAILED
  # Save SLA results in a file
  if len(metric.sla_map.keys()) > 0 and hasattr(metric, 'get_sla_csv'):
    sla_csv_file = metric.get_sla_csv()
    with open(sla_csv_file, 'w') as FH:
      for metric_label in metric.sla_map.keys():
        for sub_metric in metric.sla_map[metric_label].keys():
          for stat, sla in metric.sla_map[metric_label][sub_metric].items():
            FH.write('%s\n' % (sla.get_csv_repr()))


def parse_and_plot_single_metrics(metric, graph_timezone, outdir_default, indir_default, graphing_library,
                                  skip_plots):
  metric.graph_timezone = graph_timezone
  if metric.outdir is None:
    metric.outdir = os.path.normpath(outdir_default)

  updated_infile_list = []
  for infile in metric.infile_list:
    # handling both cases of local file or http download.
    if not infile.startswith('http://') and not infile.startswith('https://'):
      updated_infile_list.append(os.path.join(indir_default, infile))
    else:
      updated_infile_list.append(infile)
  metric.infile_list = updated_infile_list

  if not metric.ignore:
    if metric.collect():
      if metric.parse():
        metric.calc()
        metric.calculate_stats()
        check_slas(metric)
        metric.detect_anomaly()
        if not skip_plots:
          metric.graph(graphing_library)
      else:
        logger.error('Parsing failed for metric: ' + metric.label)
    else:
      logger.error('Fetch/Collect failed for metric: ' + metric.label)


def init_logging(logger, log_file, log_level):
  """
  Initialize the naarad logger.
  :param: logger: logger object to initialize
  :param: log_file: log file name
  :param: log_level: log level (debug, info, warn, error)
  """
  with open(log_file, 'w'):
    pass
  numeric_level = getattr(logging, log_level.upper(), None) if log_level else logging.INFO
  if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % log_level)
  logger.setLevel(logging.DEBUG)
  fh = logging.FileHandler(log_file)
  fh.setLevel(logging.DEBUG)
  ch = logging.StreamHandler()
  ch.setLevel(numeric_level)
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  fh.setFormatter(formatter)
  ch.setFormatter(formatter)
  logger.addHandler(fh)
  logger.addHandler(ch)
  return CONSTANTS.OK


def get_argument_parser():
  """
  Initialize list of valid arguments accepted by Naarad CLI
  :return: arg_parser: argeparse.ArgumentParser object initialized with naarad CLI parameters
  """
  arg_parser = argparse.ArgumentParser()
  arg_parser.add_argument('-c', '--config', help="file with specifications for each metric and graphs")
  arg_parser.add_argument('--start', help="Start time in the format of HH:MM:SS or YYYY-mm-dd_HH:MM:SS")
  arg_parser.add_argument('--end', help="End time in the format of HH:MM:SS or YYYY-mm-dd_HH:MM:SS")
  arg_parser.add_argument('-i', '--input_dir', help="input directory used to construct full path name of the metric infile")
  arg_parser.add_argument('-o', '--output_dir', help="output directory where the plots and Report.html will be generated")
  arg_parser.add_argument('-V', '--variables', action="append",
                          help="User defined variables (in form key=value) for substitution in the config file. "
                               "Config should have the variable names in format %%(key)s")
  arg_parser.add_argument('-s', '--show_config', help="Print config associated with the provided template name", action="store_true")
  arg_parser.add_argument('-l', '--log', help="log level")
  arg_parser.add_argument('-d', '--diff', nargs=2,
                          help="Specify the location of two naarad reports to diff separated by a space. Can be local or http(s) "
                               "locations. The first report is used as a baseline.", metavar=("report-1", "report-2"))
  arg_parser.add_argument('-n', '--no_plots',
                          help="Don't generate plot images. Useful when you only want SLA calculations. Note that on-demand charts can "
                               "still be generated through client-charting.", action="store_true")
  arg_parser.add_argument('-e', '--exit_code', help="optional argument to enable exit_code for naarad", action="store_true")
  # TODO(Ritesh) : Print a list of all templates supported with descriptions
  # arg_parser.add_argument('-l', '--list_templates', help="List all template configs", action="store_true")
  return arg_parser


def get_variables(args):
  """
  Return a dictionary of variables specified at CLI
  :param: args: Command Line Arguments namespace
  """
  variables_dict = {}
  if args.variables:
    for var in args.variables:
      words = var.split('=')
      variables_dict[words[0]] = words[1]
  return variables_dict


def validate_arguments(args):
  """
  Validate that the necessary argument for normal or diff analysis are specified.
  :param: args: Command line arguments namespace
  """
  if args.diff:
    if not args.output_dir:
      logger.error('No Output location specified')
      print_usage()
      sys.exit(0)
  # elif not (args.config and args.output_dir):
  elif not args.output_dir:
    print_usage()
    sys.exit(0)


def print_usage():
  """
  Print naarad CLI usage message
  """
  print ("Usage: "
         "\n To generate a diff report      : naarad -d report1 report2 -o <output_location> -c <optional: config-file> -e <optional: turn on exit code>"
         "\n To generate an analysis report : naarad -i <input_location> -o <output_location> -c <optional: config_file> -e <optional: turn on exit code> "
         "-n <optional: disable plotting of images>")


def discover_by_name(input_directory, output_directory):
  """
  Auto discover metric types from the files that exist in input_directory and return a list of metrics
  :param: input_directory: The location to scan for log files
  :param: output_directory: The location for the report
  """
  metric_list = []
  log_files = os.listdir(input_directory)
  for log_file in log_files:
    if log_file in CONSTANTS.SUPPORTED_FILENAME_MAPPING.keys():
      metric_list.append(initialize_metric(CONSTANTS.SUPPORTED_FILENAME_MAPPING[log_file], [log_file], None, output_directory, CONSTANTS.RESOURCE_PATH,
                                           CONSTANTS.SUPPORTED_FILENAME_MAPPING[log_file], None, None, {}, None, None, {}))
    else:
      logger.warning('Unable to determine metric type for file: %s', log_file)
  return metric_list


def initialize_metric(section, infile_list, hostname, output_directory, resource_path, label, ts_start, ts_end, rule_strings, important_sub_metrics,
                      anomaly_detection_metrics, other_options):
  """
  Initialize appropriate metric based on type of metric.
  :param: section: config section name or auto discovered metric type
  :param: infile_list: list of input log files for the metric
  :param: hostname: hostname associated with the logs origin
  :param: output_directory: report location
  :param: resource_path: resource path for report
  :param: label: label for config section or auto discovered metric type
  :param: ts_start: start time for analysis
  :param: ts_end: end time for analysis
  :param: rule_strings: list of slas
  :param: important_sub_metrics: list of important sub metrics
  :param: anomaly_detection_metrics: list of metrics to use for anomaly detection.
  :param: other_options: kwargs
  :return: metric object
  """
  bin_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'bin'))
  metric = None
  metric_type = section.split('-')[0]
  if metric_type in metric_classes:
    if 'SAR' in metric_type:
      metric = metric_classes['SAR'](section, infile_list, hostname, output_directory, resource_path, label, ts_start, ts_end, rule_strings,
                                     important_sub_metrics, anomaly_detection_metrics, **other_options)
    else:
      metric = metric_classes[metric_type](section, infile_list, hostname, output_directory, resource_path, label, ts_start, ts_end, rule_strings,
                                           important_sub_metrics, anomaly_detection_metrics, **other_options)
  else:
    metric = Metric(section, infile_list, hostname, output_directory, resource_path, label, ts_start, ts_end, rule_strings, important_sub_metrics,
                    anomaly_detection_metrics, **other_options)
  metric.bin_path = bin_path
  return metric


def initialize_aggregate_metric(section, aggr_hosts, aggr_metrics, metrics, outdir_default, resource_path, label, ts_start, ts_end, rule_strings,
                                important_sub_metrics, anomaly_detection_metrics, other_options):
  """
  Initialize aggregate metric
  :param: section: config section name
  :param: aggr_hosts: list of hostnames to aggregate
  :param: aggr_metrics: list of metrics to aggregate
  :param: metrics: list of metric objects associated with the current naarad analysis
  :param: outdir_default: report location
  :param: resource_path: resource path for report
  :param: label: label for config section
  :param: ts_start: start time for analysis
  :param: ts_end: end time for analysis
  :param: rule_strings: list of slas
  :param: important_sub_metrics: list of important sub metrics
  :param: other_options: kwargs
  :return: metric object
  """
  bin_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'bin'))
  metric = None
  metric_type = section.split('-')[0]
  metric = aggregate_metric_classes[metric_type](section, aggr_hosts, aggr_metrics, metrics, outdir_default, resource_path, label, ts_start, ts_end,
                                                 rule_strings, important_sub_metrics, anomaly_detection_metrics, **other_options)
  metric.bin_path = bin_path
  return metric
