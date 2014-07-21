import numpy

import RCA.constants as constants
from RCA.modules.correlation_result import CorrelationResult
from RCA.modules.time_series import TimeSeries


class CorrelatorAlgorithm(object):
  """
  Base class for Correlator algorithm.
  """
  def __init__(self, class_name, time_series_a, time_series_b):
    """
    Initializer
    :param class_name: name of extended class.
    :param TimeSeries time_series_a: TimeSeries a.
    :param TimeSeries time_series_b: TimeSeries b.
    """
    self.class_name = class_name
    self.time_series_a = time_series_a
    self.time_series_b = time_series_b

  # Need to be extended.
  def _detect_correlation(self):
    """
    Detect correlation.
    """
    self.correlation_result = None

  def get_correlation_result(self):
    """
    Get correlation result.
    :return CorrelationResult: a CorrelationResult object represents the correlation result.
    """
    return self.correlation_result

  def run(self):
    """
    Execute algorithm.
    :return CorrelationResult: a CorrelationResult object represents the correlation result.
    """
    self._detect_correlation()
    return self.correlation_result


class CrossCorrelation(CorrelatorAlgorithm):
  """
  Method 1: CrossCorrelation algorithm.
  Ideas come from Paul Bourke(http://paulbourke.net/miscellaneous/correlate/).
  """
  def __init__(self, time_series_a, time_series_b, max_shift_seconds=None):
    """
    Initializer
    :param TimeSeries time_series_a: TimeSeries a.
    :param TimeSeries time_series_b: TimeSeries b.
    :param int max_shift_seconds: allowed maximal shift seconds.
    """
    super(CrossCorrelation, self).__init__(self.__class__.__name__, time_series_a, time_series_b)
    if max_shift_seconds is not None:
      self.max_shift_seconds = max_shift_seconds
    else:
      self.max_shift_seconds = constants.DEFAULT_ALLOWED_SHIFT_SECONDS

  def _detect_correlation(self):
    """
    Detect correlation by computing correlation coefficients for all allowed shift steps,
    then take the maximum.
    """
    correlations = list()
    self.time_series_a.normalize()
    self.time_series_b.normalize()
    a, b = self.time_series_a.align(self.time_series_b)
    a_values, b_values = a.values, b.values
    a_avg, b_avg = a.average(), b.average()
    a_stdev, b_stdev = a.stdev(), b.stdev()
    n = len(a)
    denom = a_stdev * b_stdev * n
    try:
      # Estimate allowed shift steps by taking the time different between the first two timestamps
      # as the unit step length.
      allowed_shift_step = int(numpy.ceil(self.max_shift_seconds / (a.timestamps[1] - a.timestamps[0])))
      if not allowed_shift_step:
        allowed_shift_step = 1
    except ZeroDivisionError:
      allowed_shift_step = 1
    for delay in range(-allowed_shift_step, allowed_shift_step):
      s = 0
      for i in range(n):
        j = i + delay
        if j < 0 or j >= n:
          continue
        else:
          s += ((a_values[i] - a_avg) * (b_values[j] - b_avg))
      r = s / denom
      correlations.append([delay, r])
    max_correlation = max(correlations, key=lambda k: k[1])
    self.correlation_result = CorrelationResult(*max_correlation)