# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
import os.path
import csv
import errno
from jinja2 import Environment, FileSystemLoader
import logging
import os
import shutil
from collections import defaultdict
import naarad.httpdownload
import naarad.utils
import naarad.naarad_constants as CONSTANTS
import naarad.resources
from naarad.graphing.plot_data import PlotData as PD
import ConfigParser
import time

logger = logging.getLogger('naarad.reporting.diff')

class Diff(object):
  """
  Support for diff between two naarad reports is provided as a diff report implemented by this class. The two reports to
  be diffed can be local or remote (http(s)) on same or different hosts. Metrics and stats in common between the two
  reports are diffed both as absolute as well as %. Client charting is supported for time series in common between the 2
  reports. Metrics & Statistics that are not in common between the two reports are ignored.
  """

  def __init__(self, reports_list, report_name, output_directory, resource_directory, resource_path, **other_options):
    self.reports = reports_list
    if report_name == '':
      self.report_name = 'diff'
    else:
      self.report_name = report_name
    self.output_directory = output_directory
    self.resource_directory = resource_directory
    self.resource_path = resource_path
    if other_options:
      for (key, val) in other_options.iteritems():
        setattr(self, key, val)
    self.status = 'OK'
    self.stylesheet_includes = CONSTANTS.STYLESHEET_INCLUDES
    self.javascript_includes = CONSTANTS.JAVASCRIPT_INCLUDES
    self.diff_data = defaultdict(lambda : defaultdict(lambda : defaultdict(dict)))
    self.plot_files = []
    self.sla_map = defaultdict(lambda :defaultdict(lambda: defaultdict(None)))
    self.sla_failures = 0
    self.sla_failure_list = []

  def get_resources_location(self):
    """
    Return the location of the report templates and local js/css includes.
    :return: filesystem location for naarad/src/resources directory.
    """
    return naarad.resources.get_dir()

  def copy_local_includes(self):
    """
    Copy local js/css includes from naarad resources to the report/resources directory
    :return: None
    """
    resource_folder = self.get_resources_location()
    for stylesheet in self.stylesheet_includes:
      if ('http' not in stylesheet) and naarad.utils.is_valid_file(os.path.join(resource_folder,stylesheet)):
        shutil.copy(os.path.join(resource_folder,stylesheet), self.resource_directory)

    for javascript in self.javascript_includes:
      if ('http' not in javascript) and naarad.utils.is_valid_file(os.path.join(resource_folder,javascript)):
        shutil.copy(os.path.join(resource_folder,javascript), self.resource_directory)

    return None

  def generate_client_charting_page(self, data_sources):
    """
    Create the client charting page for the diff report, with time series data from the two diffed reports.
    :return: generated html to be written to disk
    """
    if not os.path.exists(self.resource_directory):
      os.makedirs(self.resource_directory)
    self.copy_local_includes()
    template_loader = FileSystemLoader(self.get_resources_location())
    template_environment = Environment(loader=template_loader)
    client_html = template_environment.get_template(CONSTANTS.TEMPLATE_HEADER).render(custom_stylesheet_includes=CONSTANTS.STYLESHEET_INCLUDES, custom_javascript_includes=CONSTANTS.JAVASCRIPT_INCLUDES, resource_path=self.resource_path, report_title='naarad diff report') + '\n'
    client_html += template_environment.get_template(CONSTANTS.TEMPLATE_DIFF_CLIENT_CHARTING).render(data_series=data_sources, resource_path=self.resource_path) + '\n'
    client_html += template_environment.get_template(CONSTANTS.TEMPLATE_FOOTER).render()
    return client_html

  def generate_diff_html(self):
    """
    Generate the summary diff report html from template
    :return: generated html to be written to disk
    """
    if not os.path.exists(self.resource_directory):
      os.makedirs(self.resource_directory)
    self.copy_local_includes()
    div_html = ''
    for plot_div in sorted(self.plot_files):
      with open(plot_div,'r') as div_file:
        div_html += '\n' + div_file.read()
    template_loader = FileSystemLoader(self.get_resources_location())
    template_environment = Environment(loader=template_loader)
    template_environment.filters['sanitize_string'] = naarad.utils.sanitize_string
    diff_html = template_environment.get_template(CONSTANTS.TEMPLATE_HEADER).render(custom_stylesheet_includes=CONSTANTS.STYLESHEET_INCLUDES, custom_javascript_includes=CONSTANTS.JAVASCRIPT_INCLUDES, resource_path=self.resource_path, report_title='naarad diff report') + '\n'
    diff_html += template_environment.get_template(CONSTANTS.TEMPLATE_DIFF_PAGE).render(diff_data=self.diff_data, plot_div_content=div_html, reports=self.reports, sla_failure_list=self.sla_failure_list, sla_map=self.sla_map) + '\n'
    diff_html += template_environment.get_template(CONSTANTS.TEMPLATE_FOOTER).render()
    return diff_html

  def discover(self, metafile):
    """
    Determine what summary stats, time series, and CDF csv exist for the reports that need to be diffed.
    :return: boolean: return whether the summary stats / time series / CDF csv summary was successfully located
    """
    for report in self.reports:
      if report.remote_location == 'local':
        if naarad.utils.is_valid_file(os.path.join(os.path.join(report.location, self.resource_path), metafile)):
          with open(os.path.join(os.path.join(report.location, self.resource_path), metafile),'r') as meta_file:
            if metafile == CONSTANTS.STATS_CSV_LIST_FILE:
              report.stats = meta_file.readlines()[0].split(',')
            elif metafile == CONSTANTS.PLOTS_CSV_LIST_FILE:
              report.datasource = meta_file.readlines()[0].split(',')
            elif metafile == CONSTANTS.CDF_PLOTS_CSV_LIST_FILE:
              report.cdf_datasource = meta_file.readlines()[0].split(',')
        else:
            report.status = 'NO_SUMMARY_STATS'
            self.status = 'ERROR'
            logger.error('Unable to access summary stats file for report :%s', report.label)
            return False
      else:
        stats_url = report.remote_location +  '/' + self.resource_path + '/' + metafile
        meta_file_data = naarad.httpdownload.stream_url(stats_url)

        if meta_file_data:
          if metafile == CONSTANTS.STATS_CSV_LIST_FILE:
            report.stats = meta_file_data.split(',')
          elif metafile == CONSTANTS.PLOTS_CSV_LIST_FILE:
            report.datasource = meta_file_data.split(',')
          elif metafile == CONSTANTS.CDF_PLOTS_CSV_LIST_FILE:
            report.cdf_datasource = meta_file_data.split(',')
        else:
          report.status = 'NO_SUMMARY_STATS'
          self.status = 'ERROR'
          logger.error('No summary stats available for report :%s', report.label)
          return False
    return True

  def collect_datasources(self):
    """
    Identify what time series exist in both the diffed reports and download them to the diff report resources directory
    :return: True/False : return status of whether the download of time series resources succeeded.
    """
    report_count = 0
    if self.status != 'OK':
      return False
    diff_datasource = sorted(set(self.reports[0].datasource) & set(self.reports[1].datasource))
    if diff_datasource:
      self.reports[0].datasource = diff_datasource
      self.reports[1].datasource = diff_datasource
    else:
      self.status = 'NO_COMMON_STATS'
      logger.error('No common metrics were found between the two reports')
      return False
    for report in self.reports:
      report.label = report_count
      report_count += 1
      report.local_location = os.path.join(self.resource_directory,str(report.label))
      try:
        os.makedirs(report.local_location)
      except OSError as exeption:
        if exeption.errno != errno.EEXIST:
          raise
      if report.remote_location != 'local':
        naarad.httpdownload.download_url_list(map(lambda x: report.remote_location + '/' + self.resource_path + '/' + x + '.csv', report.datasource), report.local_location)
      else:
        for filename in report.datasource:
          try:
            shutil.copy(os.path.join(os.path.join(report.location,self.resource_path),filename + '.csv'), report.local_location)
          except IOError as exeption:
            continue
    return True

  def collect_cdf_datasources(self):
    """
    Identify what cdf series exist in both the diffed reports and download them to the diff report resources directory
    :return: True/False : return status of whether the download of time series resources succeeded.
    """
    report_count = 0
    if self.status != 'OK':
      return False
    diff_cdf_datasource = sorted(set(self.reports[0].cdf_datasource) & set(self.reports[1].cdf_datasource))
    if diff_cdf_datasource:
      self.reports[0].cdf_datasource = diff_cdf_datasource
      self.reports[1].cdf_datasource = diff_cdf_datasource
    else:
      self.status = 'NO_COMMON_STATS'
      logger.error('No common metrics were found between the two reports')
      return False
    for report in self.reports:
      report.label = report_count
      report_count += 1
      report.local_location = os.path.join(self.resource_directory,str(report.label))
      try:
        os.makedirs(report.local_location)
      except OSError as exeption:
        if exeption.errno != errno.EEXIST:
          raise
      if report.remote_location != 'local':
        naarad.httpdownload.download_url_list(map(lambda x: report.remote_location + '/' + self.resource_path + '/' + x + '.csv', report.cdf_datasource), report.local_location)
      else:
        for filename in report.cdf_datasource:
          try:
            shutil.copy(os.path.join(os.path.join(report.location,self.resource_path),filename + '.csv'), report.local_location)
          except IOError as exeption:
            continue
    return True

  def collect(self):
    """
    Identify what summary stats exist in both the diffed reports and download them to the diff report resources directory
    :return: True/False : return status of whether the download of summary stats succeeded.
    """
    report_count = 0
    if self.status != 'OK':
      return False
    diff_stats = set(self.reports[0].stats) & set(self.reports[1].stats)
    if diff_stats:
      self.reports[0].stats = diff_stats
      self.reports[1].stats = diff_stats
    else:
      self.status = 'NO_COMMON_STATS'
      logger.error('No common metrics were found between the two reports')
      return False
    for report in self.reports:
      report.label = report_count
      report_count += 1
      report.local_location = os.path.join(self.resource_directory, str(report.label))
      try:
        os.makedirs(report.local_location)
      except OSError as exeption:
        if exeption.errno != errno.EEXIST:
          raise
      if report.remote_location != 'local':
        naarad.httpdownload.download_url_list(map(lambda x: report.remote_location + '/' + self.resource_path + '/' + x, report.stats), report.local_location)
      else:
          for filename in report.stats:
            shutil.copy(os.path.join(os.path.join(report.location,self.resource_path),filename), report.local_location)
    return True

  def plot_diff(self, graphing_library = 'matplotlib'):
    """
    Generate CDF diff plots of the submetrics
    """
    diff_datasource = sorted(set(self.reports[0].datasource) & set(self.reports[1].datasource))
    graphed = False
    for submetric in diff_datasource:
      baseline_csv = naarad.utils.get_default_csv(self.reports[0].local_location, (submetric+'.percentiles'))
      current_csv = naarad.utils.get_default_csv(self.reports[1].local_location, (submetric+'.percentiles'))
      if ((naarad.utils.is_valid_file(baseline_csv) & naarad.utils.is_valid_file(current_csv)) == False):
        continue
      baseline_plot = PD(input_csv=baseline_csv, csv_column=1, series_name=submetric, y_label=submetric, precision=None, graph_height=600, graph_width=1200, graph_type='line', plot_label='baseline', x_label='Percentiles')
      current_plot = PD(input_csv=current_csv, csv_column=1, series_name=submetric, y_label=submetric, precision=None, graph_height=600, graph_width=1200, graph_type='line', plot_label='current', x_label='Percentiles')
      graphed, div_file = Diff.graphing_modules[graphing_library].graph_data_on_the_same_graph([baseline_plot, current_plot], os.path.join(self.output_directory, self.resource_path), self.resource_path, (submetric+'.diff'))
      if graphed:
        self.plot_files.append(div_file)
    return True

  def check_sla(self, sla, diff_metric):
    """
    Check whether the SLA has passed or failed
    """
    try:
      if sla.display is '%':
        diff_val = float(diff_metric['percent_diff'])
      else:
        diff_val = float(diff_metric['absolute_diff'])
    except ValueError:
      return False
    if not (sla.check_sla_passed(diff_val)):
      self.sla_failures += 1
      self.sla_failure_list.append(DiffSLAFailure(sla, diff_metric))
    return True

  def generate(self):
    """
    Generate a diff report from the reports specified.
    :return: True/False : return status of whether the diff report generation succeeded.
    """
    if self.discover(CONSTANTS.STATS_CSV_LIST_FILE) and self.discover(CONSTANTS.PLOTS_CSV_LIST_FILE) and self.discover(CONSTANTS.CDF_PLOTS_CSV_LIST_FILE) and self.collect() and self.collect_datasources() and self.collect_cdf_datasources():
      for stats in self.reports[0].stats:
        metric_label = stats.replace('.stats.csv', '')
        stats_0 = os.path.join(self.reports[0].local_location, stats)
        stats_1 = os.path.join(self.reports[1].local_location, stats)
        report0_stats = {}
        report1_stats = {}
        if naarad.utils.is_valid_file(stats_0) and naarad.utils.is_valid_file(stats_1):
          report0 = csv.DictReader(open(stats_0))
          for row in report0:
            report0_stats[row[CONSTANTS.SUBMETRIC_HEADER]] = row
          report0_stats['__headers__'] = report0._fieldnames
          report1 = csv.DictReader(open(stats_1))
          for row in report1:
            report1_stats[row[CONSTANTS.SUBMETRIC_HEADER]] = row
          report1_stats['__headers__'] = report1._fieldnames
          common_stats = sorted(set(report0_stats['__headers__']) & set(report1_stats['__headers__']))
          common_submetrics = sorted(set(report0_stats.keys()) & set(report1_stats.keys()))
          for submetric in common_submetrics:
            if submetric != '__headers__':
              for stat in common_stats:
                if stat != CONSTANTS.SUBMETRIC_HEADER:
                  diff_metric = reduce(defaultdict.__getitem__,[stats.split('.')[0], submetric, stat], self.diff_data)
                  diff_metric[0] = float(report0_stats[submetric][stat])
                  diff_metric[1] = float(report1_stats[submetric][stat])
                  diff_metric['absolute_diff'] = naarad.utils.normalize_float_for_display(diff_metric[1] - diff_metric[0])
                  if diff_metric[0] == 0:
                    if diff_metric['absolute_diff'] == '0.0':
                      diff_metric['percent_diff'] = 0.0
                    else:
                      diff_metric['percent_diff'] = 'N/A'
                  else:
                    diff_metric['percent_diff'] = naarad.utils.normalize_float_for_display((diff_metric[1] - diff_metric[0]) * 100 / diff_metric[0])
                  # check whether there is a SLA failure
                  if (metric_label in self.sla_map.keys()) and (submetric in self.sla_map[metric_label].keys()) and (stat in self.sla_map[metric_label][submetric].keys()):
                    self.check_sla(self.sla_map[metric_label][submetric][stat], diff_metric)
    else:
      return False
    self.plot_diff()
    diff_html = ''
    if self.diff_data:
      diff_html = self.generate_diff_html()
      client_html = self.generate_client_charting_page(self.reports[0].datasource)
    if diff_html != '':
      with open(os.path.join(self.output_directory,CONSTANTS.DIFF_REPORT_FILE),'w') as diff_file:
        diff_file.write(diff_html)
      with open(os.path.join(self.output_directory,CONSTANTS.CLIENT_CHARTING_FILE),'w') as client_file:
        client_file.write(client_html)
    return True

class DiffSLAFailure:
  """
  DiffSLAFailures object tracks the information related to a SLA failure
  """
  def __init__(self, sla, diff_metric):
    self.sla = sla
    self.diff_metric = diff_metric

class NaaradReport:
  """
  NaaradReport object contains details on the the reports being diffed, such as details on available summary stats,
  timeseries and location in current diff report where the collected data is stored.
  """
  def __init__(self, location, title):
    if location.startswith('http://') or location.startswith('https://'):
      self.remote_location = location
    else:
      self.remote_location = 'local'
      self.local_location = location
    self.location = location
    if title == '':
      self.title = location
    self.status = 'OK'
    self.stats = []
    self.datasource = []
    self.cdf_datasource = []
    self.label = ''

