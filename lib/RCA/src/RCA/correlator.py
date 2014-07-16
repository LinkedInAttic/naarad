"""
API for Correlator Module
"""
import settings
from algorithm import correlator_algorithms
import utils


class Correlator(object):
  def __init__(self, time_series_a, time_series_b):
    """
    initializer
    :param time_series_a: a python timeseries list(list) or a path to a csv file(str).
    :param time_series_b: a python timeseries list(list) or a path to a csv file(str).
    """
    if isinstance(time_series_a, list):
      self.time_series_a = time_series_a
    else:
      self.time_series_a = utils.read_csv(time_series_a)
    if isinstance(time_series_b, list):
      self.time_series_b = time_series_b
    else:
      self.time_series_b = utils.read_csv(time_series_b)
    self._sanity_check(self.time_series_a, self.time_series_a)
    self._correlate()

  def _sanity_check(self, time_series_a, time_series_b):
    """
    check if the timeseries have more than two data points
    :param time_series_a: timeseries a
    :param time_series_b: timeseries b
    """
    if len(time_series_a) < 2 or len(time_series_b) < 2:
      raise Exception("RCA.correlator: Too few data points!")

  def _correlate(self):
    """
    get correlation
    :return: correlation object"
    """
    alg = getattr(correlator_algorithms, settings.CORRELATOR_ALGORITHM)
    a = alg(self.time_series_a, self.time_series_b)
    self.correlation = a.run()

  def get_correlation(self):
    return self.correlation

  def is_correlated(self, threshold=None):
    """
    compare with a threshould to answer weather two timeseries correlate
    :return: correlation object if two series correlate otherwise false
    """
    return self.correlation if self.correlation.coefficient >= threshold else False