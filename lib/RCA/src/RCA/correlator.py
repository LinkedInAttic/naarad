"""
API for Correlator Module
"""
import settings
from algorithm import correlator_algorithms
import utils

class correlator(object):
  def __init__(self, a, b):
    if isinstance(a, list):
      self.a = a
    else:
      self.a = utils.read_csv(a)
    if isinstance(b, list):
      self.b = b
    else:
      self.b = utils.read_csv(b)
    self._sanity_check(a,b)
    self._correlate()

  def _sanity_check(self, a, b):
    """
    check if the timeseries have more than two data points
    :param a: timeseries a
    :param b: timeseries b
    """
    if len(a) < 2 or len(b) < 2:
      raise Exception("RCA.correlator: Too few data points!")

  def _correlate(self):
    """
    get correlation
    :return: correlation object
    """
    alg = getattr(correlator_algorithms, settings.CORRELATOR_ALGORITHM)
    a = alg(self.a, self.b)
    self.correlation = a.run()

  def get_correlation(self):
    return self.correlation

  def is_correlated(self,threshold=None):
    """
    compare with a threshould to answer weather two timeseries correlate
    :return: correlation object if two series correlate otherwise false
    """
    return self.correlation if self.correlation.coefficient >= threshold else False