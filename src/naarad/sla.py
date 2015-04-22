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

import logging

logger = logging.getLogger('naarad.sla')


class SLA(object):

  supported_sla_types = ('lt', '<', 'gt', '>', 'eq', '=')

  def __init__(self, metric, sub_metric, stat_name, threshold, sla_type):
    if sla_type not in self.supported_sla_types:
      logger.error('Unsupported sla type passed : ' + sla_type)
      return None
    self.metric = metric
    self.sub_metric = sub_metric
    self.stat_name = stat_name
    self.sla_type = sla_type
    self.is_processed = False
    self.threshold = None
    self.display = None
    if '%' in threshold:
      self.threshold = float(threshold.translate(None, '%'))
      self.display = '%'
    else:
      self.threshold = float(threshold)
      self.display = ''
    self.sla_passed = None
    self.stat_value = None

  def __str__(self):
    return "{0} of {1}, threshold: {2}, sla_type: {3}, sla_passed: {4}, display: {5}".format(self.stat_name, self.sub_metric, self.threshold, self.sla_type,
                                                                                             self.sla_passed, self.display)

  def get_csv_repr(self):
    return "{0},{1},{2},{3},{4},{5}".format(self.sub_metric, self.stat_name, self.threshold, self.sla_type, self.stat_value, self.sla_passed)

  def check_sla_passed(self, stat_value):
    if self.sla_type in ('lt', '<'):
      self.grade_lt(stat_value)
    elif self.sla_type in ('gt', '>'):
      self.grade_gt(stat_value)
    elif self.sla_type in ('eq', '='):
      self.grade_eq(stat_value)
    else:
      logger.error('sla type is unsupported')
    self.stat_value = stat_value
    return self.sla_passed

  def grade_lt(self, stat_value):
    self.is_processed = True
    if stat_value >= self.threshold:
      self.sla_passed = False
    else:
      self.sla_passed = True

  def grade_gt(self, stat_value):
    self.is_processed = True
    if stat_value <= self.threshold:
      self.sla_passed = False
    else:
      self.sla_passed = True

  def grade_eq(self, stat_value):
    self.is_processed = True
    if stat_value == self.threshold:
      self.sla_passed = True
    else:
      self.sla_passed = False
