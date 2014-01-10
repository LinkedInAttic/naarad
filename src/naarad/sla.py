__author__ = 'rmaheshw'

logger = logging.getLogger('naarad.sla')

class SLA(object):

  supported_sla_types = ('lt', 'gt')

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

  def check_sla_passed(self, stat_value):
    if self.sla_type in ('lt', '<'):
      return self.grade_lt(stat_value)
    elif self.sla_type in ('tt', '>'):
      return self.grade_gt(stat_value)

  def grade_lt(self, stat_value):
    if stat_value >= self.threshold:
      return False
    else:
      return True

  def grade_gt(self, stat_value):
    if stat_value <= self.threshold:
      return False
    else:
      return True