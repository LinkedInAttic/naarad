import os
import sys
import numpy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils
import settings


class correlation(object):
  def __init__(self, shift, coefficient):
    """
    construct a correlation object
    :param float coefficient: the correlation coefficient
    :param int shift: the amount of shift where the coefficient is given
    """
    self.shift = shift
    self.coefficient = coefficient


class correlator_algo(object):
  def __init__(self, name, a, b):
    """
    initializer
    :param list a: timeseries a
    :param list b: timeseries b
    """
    self.name = name
    self.a = a
    self.b = b

  #need to be extented
  def set_correlation(self):
    self.correlation = None

  def get_correlation(self):
    return self.correlation

  def run(self):
    self.set_correlation()
    return self.get_correlation()


class crossCorrelation(correlator_algo):
  def __init__(self, a, b):
    super(crossCorrelation, self).__init__(self.__class__.__name__, a, b)

  def set_correlation(self, max_shift_seconds=None):
    """
    get cross correlation coefficients for all possible shifts
    :param int max_shift_seconds: maximal allowed shift seconds when computing correlations
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
      max_shift_seconds = settings.DEFAULT_ALLOWED_SHIFT_SECONDS
    # estimate shift_room
    try:
      shift_room = int(numpy.ceil(max_shift_seconds/(a[1][0]-a[0][0])))
    except ZeroDivisionError:
      shift_room = 1
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
    self.correlation = correlation(max_correlation[0], max_correlation[1])