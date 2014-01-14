__author__ = 'rmaheshw'

import logging

logger = logging.getLogger('naarad.sla')

class SLA(object):

  supported_sla_types = ('lt', '<', 'gt', '>')

  def __init__(self, sub_metric, stat_name, threshold, sla_type):
    if sla_type not in self.supported_sla_types:
      log.error('Unsupported sla type passed : ' + sla_type)
      return None
    self.sub_metric = sub_metric
    self.stat_name = stat_name
    self.threshold = threshold
    self.sla_type = sla_type
    self.is_processed = False
    self.sla_passed = None

  def __str__(self):
    return "{0} of {1}, threshold: {2}, sla_type: {3}, sla_passed: {4}".format(self.stat_name, self.sub_metric, self.threshold, self.sla_type, self.sla_passed)

  def check_sla_passed(self, stat_value):
    if self.sla_type in ('lt', '<'):
      self.grade_lt(stat_value)
    elif self.sla_type in ('gt', '>'):
      self.grade_gt(stat_value)
    else:
      logger.error('sla type is unsupported')
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
