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

from collections import defaultdict
import ConfigParser
import errno
import logging
import os
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
  def __init__(self, ts_start, config, test_id=None):
    self.ts_start = ts_start
    self.ts_end = None
    self.test_id = test_id
    self.config = config
    self.description = ''
    self.input_directory = None
    self.output_directory = None
    self.resource_path = 'resources'
    self.status = CONSTANTS.OK
    self.sla_data = {}
    self.stats_data = {}
    self.variables = None


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
    self.return_exit_code = False
    self.skip_plots = False
    self.available_graphing_modules = graphing_modules
    logger.info('Available graphing modules: %s ', ','.join(self.available_graphing_modules.keys()))
    naarad.metrics.metric.Metric.graphing_modules = self.available_graphing_modules
    naarad.reporting.diff.Diff.graphing_modules = self.available_graphing_modules
    naarad.metrics.metric.Metric.device_types = CONSTANTS.device_type_metrics

  def signal_start(self, config, test_id=None, **kwargs):
    """
    Initialize an analysis object and set ts_start for the analysis represented by test_id
    :param test_id: integer that represents the analysis
    :param config: config can be a ConfigParser.ConfigParser object or a string specifying local or http(s) location
     for config
    :return: test_id
    """
    if not test_id:
      self._default_test_id += 1
      test_id = self._default_test_id
    self._analyses[test_id] = _Analysis(naarad.utils.get_standardized_timestamp('now', None), config,
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
    if test_id is None:
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
    Get sla data from each metric and set it in the _Analysis object specified by test_id to make it available
    for retrieval
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
    Get summary stats data from each metric and set it in the _Analysis object specified by test_id to make it available
    for retrieval
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

  def _run_pre(self, analysis, run_steps):
    """
    If Naarad is run in CLI mode, execute any pre run steps specified in the config. ts_start/ts_end are set based on
    workload run steps if any.
    :param: analysis: The analysis object being processed
    :param: run_steps: list of post run steps
    """
    workload_run_steps = []
    for run_step in sorted(run_steps, key=lambda step: step.run_rank):
      run_step.run()
      if run_step.run_type == CONSTANTS.RUN_TYPE_WORKLOAD:
        workload_run_steps.append(run_step)
    # Get analysis time period from workload run steps
    if len(workload_run_steps) > 0:
      analysis.ts_start, analysis.ts_end = naarad.utils.get_run_time_period(workload_run_steps)
    return CONSTANTS.OK

  def _run_post(self, run_steps):
    """
    If Naarad is run in CLI mode, execute any post run steps specified in the config
    :param: run_steps: list of post run steps
    """
    for run_step in sorted(run_steps, key=lambda step: step.run_rank):
      run_step.run()
    return CONSTANTS.OK

  def _process_args(self, analysis, args):
    """
    When Naarad is run in CLI mode, get the CL arguments and update the analysis
    :param: analysis: The analysis being processed
    :param: args: Command Line Arguments received by naarad
    """
    if args.exit_code:
      self.return_exit_code = args.exit_code
    if args.no_plots:
      self.skip_plots = args.no_plots
    if args.start:
      analysis.ts_start = naarad.utils.get_standardized_timestamp(args.start, None)
    if args.end:
      analysis.ts_end = naarad.utils.get_standardized_timestamp(args.end, None)
    if args.variables:
      analysis.variables = naarad.utils.get_variables(args)
    return CONSTANTS.OK

  def analyze(self, input_directory, output_directory, **kwargs):
    """
    Run all the analysis saved in self._analyses, sorted by test_id
    :param: input_directory: location of log files
    :param: output_directory: root directory for analysis output
    :param: **kwargs: Optional keyword args
    :return: int: status code.
    """
    is_api_call = True
    if len(self._analyses) == 0:
      if 'config' not in kwargs.keys():
        return CONSTANTS.ERROR
      self._analyses[0] = _Analysis(None, kwargs['config'], test_id=0)
    if 'args' in kwargs:
      self._process_args(self._analyses[0], kwargs['args'])
      is_api_call = False
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
      if('config' in kwargs.keys()) and (not self._analyses[test_id].config):
        self._analyses[test_id].config = kwargs['config']
      self._create_output_directories(self._analyses[test_id])
      self._analyses[test_id].status = self.run(self._analyses[test_id], is_api_call, **kwargs)
      if self._analyses[test_id].status != CONSTANTS.OK:
        error_count += 1
    if error_count > 0:
      return CONSTANTS.ERROR
    else:
      return CONSTANTS.OK

  def run(self, analysis, is_api_call, **kwargs):
    """
    :param analysis: Run naarad analysis for the specified analysis object
    :param **kwargs: Additional keyword args can be passed in here for future enhancements
    :return:
    """
    threads = []
    crossplots = []
    report_args = {}
    metrics = defaultdict()
    run_steps = defaultdict(list)
    discovery_mode = False
    graph_timezone = None
    graphing_library = None

    if isinstance(analysis.config, str):
      if not naarad.utils.is_valid_file(analysis.config):
        return CONSTANTS.INVALID_CONFIG
      config_object = ConfigParser.ConfigParser(analysis.variables)
      config_object.optionxform = str
      config_object.read(analysis.config)
    elif isinstance(analysis.config, ConfigParser.ConfigParser):
      config_object = analysis.config
    else:
      if is_api_call:
        return CONSTANTS.INVALID_CONFIG
      else:
        metrics['metrics'] = naarad.utils.discover_by_name(analysis.input_directory, analysis.output_directory)
        if len(metrics['metrics']) == 0:
          logger.warning('Unable to auto detect metrics in the specified input directory: %s', analysis.input_directory)
          return CONSTANTS.ERROR
        else:
          discovery_mode = True
          metrics['aggregate_metrics'] = []
    if not discovery_mode:
      metrics, run_steps, crossplots, report_args, graph_timezone, graphing_library = self._process_naarad_config(config_object, analysis)

    if graphing_library is None:
      graphing_library = CONSTANTS.DEFAULT_GRAPHING_LIBRARY
    # If graphing libraries are not installed, skip static images
    if graphing_library not in self.available_graphing_modules.keys():
      logger.error("Naarad cannot import graphing library %s on your system. Will not generate static charts", graphing_library)
      self.skip_plots = True

    if not is_api_call:
      self._run_pre(analysis, run_steps['pre'])
    for metric in metrics['metrics']:
      if analysis.ts_start:
        metric.ts_start = analysis.ts_start
      if analysis.ts_end:
        metric.ts_end = analysis.ts_end
      thread = threading.Thread(target=naarad.utils.parse_and_plot_single_metrics,
                                args=(metric, graph_timezone, analysis.output_directory, analysis.input_directory, graphing_library, self.skip_plots))
      thread.start()
      threads.append(thread)
    for t in threads:
      t.join()
    for metric in metrics['aggregate_metrics']:
      thread = threading.Thread(target=naarad.utils.parse_and_plot_single_metrics,
                                args=(metric, graph_timezone, analysis.output_directory, analysis.input_directory, graphing_library, self.skip_plots))
      thread.start()
      threads.append(thread)
    for t in threads:
      t.join()
    self._set_sla_data(analysis.test_id, metrics['metrics'] + metrics['aggregate_metrics'])
    self._set_stats_data(analysis.test_id, metrics['metrics'] + metrics['aggregate_metrics'])
    if len(crossplots) > 0 and not self.skip_plots:
      correlated_plots = naarad.utils.nway_plotting(crossplots, metrics['metrics'] + metrics['aggregate_metrics'],
                                                    os.path.join(analysis.output_directory, analysis.resource_path),
                                                    analysis.resource_path, graphing_library)
    else:
      correlated_plots = []
    rpt = reporting_modules['report'](None, analysis.output_directory, os.path.join(analysis.output_directory, analysis.resource_path), analysis.resource_path,
                                      metrics['metrics'] + metrics['aggregate_metrics'], correlated_plots=correlated_plots, **report_args)
    rpt.generate()
    if not is_api_call:
      self._run_post(run_steps['post'])

    if self.return_exit_code:
      for metric in metrics['metrics'] + metrics['aggregate_metrics']:
        if metric.status == CONSTANTS.SLA_FAILED:
          return CONSTANTS.SLA_FAILURE

    return CONSTANTS.OK

  def diff(self, test_id_1, test_id_2, config=None, **kwargs):
    """
    Create a diff report using test_id_1 as a baseline
    :param: test_id_1: test id to be used as baseline
    :param: test_id_2: test id to compare against baseline
    :param: config file for diff (optional)
    :param: **kwargs: keyword arguments
    """
    output_directory = os.path.join(self._output_directory, 'diff_' + str(test_id_1) + '_' + str(test_id_2))
    if kwargs:
      if 'output_directory' in kwargs.keys():
        output_directory = kwargs['output_directory']
    diff_report = Diff([NaaradReport(self._analyses[test_id_1].output_directory, None),
                        NaaradReport(self._analyses[test_id_2].output_directory, None)],
                       'diff', output_directory, os.path.join(output_directory, self._resource_path),
                       self._resource_path)
    if config:
      naarad.utils.extract_diff_sla_from_config_file(diff_report, config)
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
    diff_report = Diff([NaaradReport(report1_location, None), NaaradReport(report2_location, None)], 'diff',
                       output_directory, os.path.join(output_directory, self._resource_path), self._resource_path)
    if config:
      naarad.utils.extract_diff_sla_from_config_file(diff_report, config)
    diff_report.generate()
    if diff_report.sla_failures > 0:
      return CONSTANTS.SLA_FAILURE
    if diff_report.status != 'OK':
      return CONSTANTS.ERROR
    return CONSTANTS.OK

  def _process_naarad_config(self, config, analysis):
    """
    Process the config file associated with a particular analysis and return metrics, run_steps and crossplots.
    Also sets output directory and resource_path for an anlaysis
    """
    graph_timezone = None
    output_directory = analysis.output_directory
    resource_path = analysis.resource_path
    run_steps = defaultdict(list)
    metrics = defaultdict(list)
    indir_default = ''
    crossplots = []
    report_args = {}
    graphing_library = None
    ts_start, ts_end = None, None

    if config.has_section('GLOBAL'):
      ts_start, ts_end = naarad.utils.parse_global_section(config, 'GLOBAL')
      if config.has_option('GLOBAL', 'user_defined_metrics'):
        naarad.utils.parse_user_defined_metric_classes(config, metric_classes)
      config.remove_section('GLOBAL')

    if config.has_section('REPORT'):
      report_args = naarad.utils.parse_report_section(config, 'REPORT')
      config.remove_section('REPORT')

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
          logger.critical('Section name %s is invalid! Only letters, digits, dot(.), dash(-), underscore(_) are allowed'
                          % section)
          return CONSTANTS.CRITICAL_FAILURE
        if section == 'SAR-*':
          hostname, infile, label, ts_start, ts_end, precision, kwargs, rule_strings = \
              naarad.utils.parse_basic_metric_options(config, section)
          sar_metrics = naarad.utils.get_all_sar_objects(metrics, infile, hostname, output_directory, label, ts_start,
                                                         ts_end, None)
          for sar_metric in sar_metrics:
            if sar_metric.ts_start is None and (sar_metric.ts_end is None or sar_metric.ts_end > ts_start):
              sar_metric.ts_start = ts_start
            if sar_metric.ts_end is None and (sar_metric.ts_start is None or ts_end > sar_metric.ts_start):
              sar_metric.ts_end = ts_end
          metrics['metrics'].extend(sar_metrics)
        else:
          new_metric = naarad.utils.parse_metric_section(config, section, metric_classes, metrics['metrics'],
                                                         aggregate_metric_classes, output_directory, resource_path)
          if new_metric.ts_start is None and (new_metric.ts_end is None or new_metric.ts_end > ts_start):
            new_metric.ts_start = ts_start
          if new_metric.ts_end is None and (new_metric.ts_start is None or ts_end > new_metric.ts_start):
            new_metric.ts_end = ts_end
          new_metric.bin_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(
              os.path.dirname(os.path.abspath(__file__)))), 'bin'))
          metric_type = section.split('-')[0]
          if metric_type in aggregate_metric_classes:
            metrics['aggregate_metrics'].append(new_metric)
          else:
            metrics['metrics'].append(new_metric)
    return metrics, run_steps, crossplots, report_args, graph_timezone, graphing_library
