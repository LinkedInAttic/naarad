# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License");?you may not use this file except in compliance with the License.?You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software?distributed under the License is distributed on an "AS IS" BASIS,?WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""

from collections import defaultdict
import ConfigParser
import errno
import logging
import os
import sys
import threading
import naarad.utils
import naarad.naarad_constants as CONSTANTS
from naarad_imports import metric_classes
from naarad_imports import aggregate_metric_classes
from naarad_imports import graphing_modules
from naarad_imports import reporting_modules
from naarad.reporting.diff import Diff
from naarad.reporting.diff import NaaradReport

logger = logging.getLogger('naarad')

class _Analysis(object):
  """
  Class that saves state for analysis to be conducted
  """
  def __init__(self, ts_start, config_file_location, test_id=None):
    self.ts_start = ts_start
    self.ts_end = None
    self.test_id = test_id
    self.config_file_location = config_file_location
    self.description = ''
    self.input_directory = None
    self.output_directory = None
    self.resource_path = 'resources'
    self.status = CONSTANTS.OK
    self.sla_data = {}
    self.stats_data = {}

class Naarad(object):
  """
  Naarad base class that will let the caller run multiple naarad analysis
  """

  def __init__(self):
    self._default_test_id = -1
    self._analyses = {}
    self._resource_path = 'resources'
    self._input_directory = None
    self._output_directory = None
    naarad.metrics.metric.Metric.graphing_modules = graphing_modules
    naarad.metrics.metric.Metric.device_types = CONSTANTS.device_type_metrics
    naarad.reporting.diff.Diff.graphing_modules = graphing_modules


  def signal_start(self, config_file_location, test_id=None, **kwargs):
    """
    Initialize an analysis object and set ts_start for the analysis represented by test_id
    :param test_id: integer that represents the analysis
    :param config_file_location: local or http location of the naarad config used for this analysis
    :return: test_id
    """
    if not test_id:
      self._default_test_id += 1
      test_id = self._default_test_id
    self._analyses[test_id] = _Analysis(naarad.utils.get_standardized_timestamp('now', None), config_file_location,
                                      test_id=test_id)
    if kwargs:
      if 'description' in kwargs.keys():
        self._analyses[test_id].description = kwargs['description']
      if 'input_directory' in kwargs.keys():
        self._analyses[test_id].input_directory = kwargs['input_directory']
      if 'output_directory' in kwargs.keys():
        self._analyses[test_id].output_directory = kwargs['output_directory']
    return test_id

  def signal_stop(self, test_id=None):
    """
    Set ts_end for the analysis represented by test_id
    :param test_id: integer that represents the analysis
    :return: test_id
    """
    if not test_id:
      test_id = self._default_test_id
    if self._analyses[test_id].ts_end:
      return CONSTANTS.OK
    self._analyses[test_id].ts_end = naarad.utils.get_standardized_timestamp('now', None)
    return CONSTANTS.OK

  def get_failed_analyses(self):
    """
    Returns a list of test_id for which naarad analysis failed
    :return: list of test_ids
    """
    failed_analyses = []
    for test_id in self._analyses.keys():
      if self._analyses[test_id].status != CONSTANTS.OK:
        failed_analyses.append(test_id)
    return failed_analyses

  def get_sla_data(self, test_id):
    """
    Returns sla data for all the metrics associated with a test_id
    :return: dict of form { metric.label:metric.sla_map}
    """
    return self._analyses[test_id].sla_data

  def _set_sla_data(self, test_id, metrics):
    """
    Get sla data from each metric and set it in the _Analysis object specified by test_id to make it available for retrieval
    :return: currently always returns CONSTANTS.OK. Maybe enhanced in future to return additional status
    """
    for metric in metrics:
      self._analyses[test_id].sla_data[metric.label] = metric.sla_map
    return CONSTANTS.OK

  def get_stats_data(self, test_id):
    """
    Returns summary stats data for all the metrics associated with a test_id
    :return: dict of form { metric.label:metric.summary_stats}
    """
    return self._analyses[test_id].stats_data

  def _set_stats_data(self, test_id, metrics):
    """
    Get summary stats data from each metric and set it in the _Analysis object specified by test_id to make it available for retrieval
    :return: currently always returns CONSTANTS.OK. Maybe enhanced in future to return additional status
    """
    for metric in metrics:
      self._analyses[test_id].stats_data[metric.label] = metric.summary_stats
    return CONSTANTS.OK

  def _create_output_directories(self, analysis):
    """
    Create the necessary output and resource directories for the specified analysis
    :param: analysis: analysis associated with a given test_id
    """
    try:
      os.makedirs(analysis.output_directory)
    except OSError as exception:
      if exception.errno != errno.EEXIST:
        raise
    try:
      resource_directory = os.path.join(analysis.output_directory, analysis.resource_path)
      os.makedirs(resource_directory)
    except OSError as exception:
      if exception.errno != errno.EEXIST:
        raise

  def analyze(self, input_directory, output_directory, **kwargs):
    """
    Run all the analysis saved in self._analyses, sorted by test_id
    :param: input_directory: location of log files
    :param: output_directory: root directory for analysis output
    :param: **kwargs: Optional keyword args
    :return: int: status code.
    """
    if len(self._analyses) == 0:
      if 'config_file_location' not in kwargs:
        return CONSTANTS.ERROR
      self._analyses[0] = _Analysis(None, kwargs['config_file_location'])
    error_count = 0
    self._input_directory = input_directory
    self._output_directory = output_directory
    for test_id in sorted(self._analyses.keys()):
      if not self._analyses[test_id].input_directory:
        self._analyses[test_id].input_directory = input_directory
      if not self._analyses[test_id].output_directory:
        if len(self._analyses) > 1:
          self._analyses[test_id].output_directory = os.path.join(output_directory, str(test_id))
        else:
          self._analyses[test_id].output_directory = output_directory
      if('config_file_location' in kwargs.keys()) and (not self._analyses[test_id].config_file_location):
        self._analyses[test_id].config_file_location = kwargs['config_file_location']
      self._create_output_directories(self._analyses[test_id])
      self._analyses[test_id].status = self.run(self._analyses[test_id], **kwargs)
      if self._analyses[test_id].status != CONSTANTS.OK:
        error_count += 1
    if error_count > 0:
      return CONSTANTS.ERROR
    else:
      return CONSTANTS.OK

  def run(self, analysis, **kwargs):
    """
    :param analysis: Run naarad analysis for the specified analysis object
    :param **kwargs: Additional keyword args can be passed in here for future enhancements
    :return:
    """
    threads = []
    if not naarad.utils.is_valid_file(analysis.config_file_location):
      return CONSTANTS.INVALID_CONFIG
    config_object = ConfigParser.ConfigParser(kwargs)
    config_object.optionxform = str
    config_object.read(analysis.config_file_location)
    metrics, run_steps, crossplots = self._process_naarad_config(config_object, analysis)
    graph_lock = threading.Lock()

    for metric in metrics['metrics']:
      if analysis.ts_start and not metric.ts_start:
        metric.ts_start = analysis.ts_start
      if analysis.ts_end and not metric.ts_end:
        metric.ts_end = analysis.ts_end
      thread = threading.Thread(target=naarad.utils.parse_and_plot_single_metrics, args=(metric, 'UTC', analysis.output_directory, analysis.input_directory, 'matplotlib', graph_lock, True))
      thread.start()
      threads.append(thread)
    for t in threads:
      t.join()
    for metric in metrics['aggregate_metrics']:
      thread = threading.Thread(target=naarad.utils.parse_and_plot_single_metrics, args=(metric, 'UTC', analysis.output_directory, analysis.input_directory, 'matplotlib', graph_lock, True))
      thread.start()
      threads.append(thread)
    for t in threads:
      t.join()

    self._set_sla_data(analysis.test_id, metrics['metrics'] + metrics['aggregate_metrics'])
    self._set_stats_data(analysis.test_id, metrics['metrics'] + metrics['aggregate_metrics'])

    if len(crossplots) > 0:
      correlated_plots = naarad.utils.nway_plotting(crossplots, metrics['metrics'] + metrics['aggregate_metrics'], os.path.join(analysis.output_directory, analysis.resource_path), analysis.resource_path)
    else:
      correlated_plots = []
    rpt = reporting_modules['report'](None, analysis.output_directory, os.path.join(analysis.output_directory, analysis.resource_path), analysis.resource_path, metrics['metrics'] + metrics['aggregate_metrics'], correlated_plots=correlated_plots)
    rpt.generate()

    return CONSTANTS.OK

  def diff(self, test_id_1, test_id_2, config=None, **kwargs):
    """
    Create a diff report using test_id_1 as a baseline
    :param: test_id_1: test id to be used as baseline
    :param: test_id_2: test id to compare against baseline
    :param: config file for diff (optional)
    :param: **kwargs: keyword arguments
    """
    output_directory = os.path.join(self._output_directory,'diff_' + str(test_id_1) + '_' + str(test_id_2))
    if kwargs:
      if 'output_directory' in kwargs.keys():
        output_directory = kwargs['output_directory']
    diff_report = Diff([NaaradReport(self._analyses[test_id_1].output_directory, None), NaaradReport(self._analyses[test_id_2].output_directory, None)], 'diff', output_directory, os.path.join(output_directory, self._resource_path), self._resource_path)
    if config:
      naarad.utils.extract_sla_from_config_file(diff_report, config)
    diff_report.generate()
    if diff_report.sla_failures > 0:
      return CONSTANTS.SLA_FAILURE
    if diff_report.status != 'OK':
      return CONSTANTS.ERROR
    return CONSTANTS.OK

  def diff_reports_by_location(self, report1_location, report2_location, output_directory, config=None, **kwargs):
    """
    Create a diff report using report1 as a baseline
    :param: report1_location: report to be used as baseline
    :param: report2_location: report to compare against baseline
    :param: config file for diff (optional)
    :param: **kwargs: keyword arguments
    """

    if kwargs:
      if 'output_directory' in kwargs.keys():
        output_directory = kwargs['output_directory']
    diff_report = Diff([NaaradReport(report1_location, None), NaaradReport(report2_location, None)], 'diff', output_directory, os.path.join(output_directory, self._resource_path), self._resource_path)
    if config:
      naarad.utils.extract_sla_from_config_file(diff_report, config)
    diff_report.generate()
    if diff_report.sla_failures > 0:
      return CONSTANTS.SLA_FAILURE
    if diff_report.status != 'OK':
      return CONSTANTS.ERROR
    return CONSTANTS.OK


  def _process_naarad_config(self, config, analysis):
    """
    Process the config file associated with a particular analysis and return metrics, run_steps and crossplots. Also sets output directory and resource_path for an anlaysis
    """
    output_directory = analysis.output_directory
    resource_path = analysis.resource_path
    run_steps = defaultdict(list)
    metrics = defaultdict(list)
    indir_default = ''

    if config.has_section('GLOBAL'):
      ts_start, ts_end = naarad.utils.parse_global_section(config, section)
      if config.has_option('GLOBAL', 'user_defined_metrics'):
        naarad.utils.parse_user_defined_metric_classes(config, metric_classes)
      config.remove_section('GLOBAL')

    for section in config.sections():
      # GRAPH section is optional
      if section == 'GRAPH':
        graphing_library, crossplots, outdir_default, indir_default, graph_timezone = \
          naarad.utils.parse_graph_section(config, section, output_directory, indir_default)
      elif section.startswith('RUN-STEP'):
        run_step = naarad.utils.parse_run_step_section(config, section)
        if not run_step:
          logger.error('Ignoring section %s, could not parse it correctly', section)
          continue
        if run_step.run_order == CONSTANTS.PRE_ANALYSIS_RUN:
          run_steps['pre'].append(run_step)
        # DURING_ANALYSIS_RUN not supported yet
        elif run_step.run_order == CONSTANTS.DURING_ANALYSIS_RUN:
          run_steps['in'].append(run_step)
        elif run_step.run_order == CONSTANTS.POST_ANALYSIS_RUN:
          run_steps['post'].append(run_step)
        else:
          logger.error('Unknown RUN-STEP run_order specified')
      else:
        # section name is used to create sub-directories, so enforce it.
        if not naarad.utils.is_valid_metric_name(section):
          logger.critical('Section name %s is invalid! Only letters, digits, dot(.), dash(-), underscore(_) are allowed' % section)
          return CONSTANTS.CRITICAL_FAILURE
        if section == 'SAR-*':
          hostname, infile, label, ts_start, ts_end, precision, kwargs, rule_strings = \
            naarad.utils.parse_basic_metric_options(config, section)
          sar_metrics = naarad.utils.get_all_sar_objects(metrics, infile, hostname, output_directory, label, ts_start,
                                                         ts_end, None)
          metrics['metrics'].extend(sar_metrics)
        else:
          new_metric = naarad.utils.parse_metric_section(config, section, metric_classes, metrics, aggregate_metric_classes, output_directory, resource_path)
          new_metric.bin_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),'bin'))
          metric_type = section.split('-')[0]
          if metric_type in aggregate_metric_classes:
            metrics['aggregate_metrics'].append(new_metric)
          else:
            metrics['metrics'].append(new_metric)
    return metrics, run_steps, crossplots
