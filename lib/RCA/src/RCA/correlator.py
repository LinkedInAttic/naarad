"""
API for Correlation Module
"""
import numpy
from setting import *
import utils


class correlator(object):
  def __init__(self, a, b):
    self.sanity_check(a,b)
    self.a = a
    self.b = b
    self.coefficient = None
    self.correlations = None

  def sanity_check(self, a, b):
    """
    check if the timeseries have more than two data points
    :param a: timeseries a
    :param b: timeseries b
    """
    if len(a) < 2 or len(b) < 2:
      raise Exception("RCA.correlator: Too few data points!")

  def cross_correlate(self, max_shift_seconds=None):
    """
    get cross correlation coefficients for all possible shifts
    :param int max_shift_seconds: maximal allowed shift seconds when computing correlations
    :return dict: {
      'correlations':a list of correlation coefficient each corresponding to a certain shift
      'coefficient': the max correlation can be reached [coefficient, delay]
    }
    """
    correlations = list()
    a = utils.to_epoch_ts(self.a)
    b = utils.to_epoch_ts(self.b)
    a, b = utils.align_two_timeseries((a,b))
    a = utils.nomalize_timeseries(a)
    b = utils.nomalize_timeseries(b)
    a_values = utils.get_values(a)
    b_values = utils.get_values(b)
    a_avg = numpy.mean(a_values)
    b_avg = numpy.mean(b_values)
    a_stdev = numpy.std(a_values)
    b_stdev = numpy.std(b_values)
    n = len(a)
    denom = a_stdev*b_stdev*n
    if not max_shift_seconds:
      max_shift_seconds = DEFAULT_ALLOWED_SHIFT_SECONDS
    #estimate shift_room
    shift_room = int(numpy.ceil(max_shift_seconds/(a[1][0]-a[0][0])))
    for delay in range(-shift_room, shift_room):
      s = 0
      for i in range(0, n):
        j = i+delay
        if j<0 or j>=n:
          continue
        else:
          s += ((a_values[i]-a_avg)*(b_values[j]-b_avg))
      r = s/denom
      correlations.append([delay, r])
    max_correlation = max(correlations, key = lambda k: k[1])
    self.correlations = correlations
    self.coefficient = max_correlation
    return {
      'correlations': self.correlations,
      'coefficient': self.coefficient
    }

  def correlate(self):
    """
    get Pearson product-moment correlation coefficient.
    :return: [delay, correlation coefficient]
    """
    if not self.coefficient:
      self.cross_correlate()
    return self.coefficient


  def is_correlated(self,threshold=None):
    """
    get a Y/N answer weather two timeseries correlate
    :param list a: timeseries a
    :param list b: timeseries b
    :return: [delay, correlations coefficient] if two series correlate otherwise false
    """
    if not self.coefficient:
      self.cross_correlate()
    threshold = DEFAULT_CORRELATE_THRESHOLD if threshold is None else threshold
    return self.coefficient if self.coefficient[1] >= threshold else False