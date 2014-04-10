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


logger = logging.getLogger('naarad')

class Analysis(object):
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
    self.sla_data = defaultdict(dict)
    self.stats_data = defaultdict(dict)


class Naarad(object):
  """
  Naarad base class that will let the caller run multiple naarad analysis
  """

  def __init__(self):
    self.default_test_id = -1
    self.analyses = {}
    naarad.metrics.metric.Metric.graphing_modules = graphing_modules
    naarad.metrics.metric.Metric.device_types = CONSTANTS.device_type_metrics


  def signal_start(self, config_file_location, test_id=None, **kwargs):
    """
    Initialize an analysis object and set ts_start for the analysis represented by test_id
    :param test_id: integer that represents the analysis
    :param config_file_location: local or http location of the naarad config used for this analysis
    :return: test_id
    """
    if not test_id:
      self.default_test_id += 1
      test_id = self.default_test_id
    self.analyses[test_id] = Analysis(naarad.utils.get_standardized_timestamp('now', None), config_file_location,
                                      test_id=test_id)
    if kwargs:
      if 'description' in kwargs.keys():
        self.analyses[test_id].description = kwargs['description']
      if 'input_directory' in kwargs.keys():
        self.analyses[test_id].input_directory = kwargs['input_directory']
      if 'output_directory' in kwargs.keys():
        self.analyses[test_id].output_directory = kwargs['output_directory']
    return test_id

  def signal_stop(self, test_id=None):
    """
    Set ts_end for the analysis represented by test_id
    :param test_id: integer that represents the analysis
    :return: test_id
    """
    if not test_id:
      test_id = self.default_test_id
    if self.analyses[test_id].ts_end:
      return CONSTANTS.OK
    self.analyses[test_id].ts_end = naarad.utils.get_standardized_timestamp('now', None)
    return CONSTANTS.OK

  def get_failed_analyses(self):
    failed_analyses = []
    for test_id in self.analyses.keys():
      if self.analyses[test_id].status != CONSTANTS.OK:
        failed_analyses.append(test_id)
    return failed_analyses

  def get_sla_data(self, test_id):
    return self.analyses[test_id].sla_data

  def set_sla_data(self, analysis, metrics):
    for metric in metrics:
      analysis.sla_data += {metric: metrics[metric].sla_map}
    return CONSTANTS.OK

  def set_stats_data(self, analysis, metrics):
    for metric in metrics:
      analysis.stats_data += {metric: metrics[metric].summary_stats}
    return CONSTANTS.OK

  def get_stats_data(self, test_id):
    return self.analyses[test_id].stats_data

  def create_output_directories(self, analysis):
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
    Run all the analysis saved in self.analyses, sorted by test_id
    :return:
    """
    if len(self.analyses) == 0:
      self.analyses[0] = Analysis(None, kwargs['config_file_location'])
    error_count = 0
    for test_id in sorted(self.analyses.keys()):
      if not self.analyses[test_id].input_directory:
        self.analyses[test_id].input_directory = input_directory
      if not self.analyses[test_id].output_directory:
        if len(self.analyses) > 1:
          self.analyses[test_id].output_directory = os.path.join(output_directory, str(test_id))
        else:
          self.analyses[test_id].output_directory = output_directory
      if('config_file_location' in kwargs.keys()) and (not self.analyses[test_id].config_file_location):
        self.analyses[test_id].config_file_location = kwargs['config_file_location']
      self.create_output_directories(self.analyses[test_id])
      self.analyses[test_id].status = self.run(self.analyses[test_id], **kwargs)
      if self.analyses[test_id].status != CONSTANTS.OK:
        error_count += 1
    if error_count > 0:
      return CONSTANTS.ERROR
    else:
      return CONSTANTS.OK

  def run(self, analysis, **kwargs):
    """
    :param analysis:
    :return:
    """
    threads = []
    if not naarad.utils.is_valid_file(analysis.config_file_location):
      return CONSTANTS.INVALID_CONFIG
    config_object = ConfigParser.ConfigParser(kwargs)
    config_object.optionxform = str
    config_object.read(analysis.config_file_location)
    metrics, run_steps, crossplots = self.process_naarad_config(config_object, analysis)
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

    self.set_sla_data(analysis, ['metrics'] + metrics['aggregate_metrics'])
    self.set_stats_data(analysis, ['metrics'] + metrics['aggregate_metrics'])

    if len(crossplots) > 0:
      correlated_plots = naarad.utils.nway_plotting(crossplots, metrics['metrics'] + metrics['aggregate_metrics'], os.path.join(analysis.output_directory, analysis.resource_path), analysis.resource_path)
    else:
      correlated_plots = []
    rpt = reporting_modules['report'](None, analysis.output_directory, os.path.join(analysis.output_directory, analysis.resource_path), analysis.resource_path, metrics['metrics'] + metrics['aggregate_metrics'], correlated_plots=correlated_plots)
    rpt.generate()

    return CONSTANTS.OK

  def process_naarad_config(self, config, analysis):
    output_directory = analysis.output_directory
    resource_path = analysis.resource_path
    run_steps = defaultdict(list)
    metrics = defaultdict(list)
    indir_default = ''
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
