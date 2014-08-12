#!/usr/bin/env python
# coding=utf-8
"""
© 2014 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
import numpy

from luminol.algorithms.correlator_algorithms import CorrelatorAlgorithm
import luminol.constants as constants
from luminol.modules.correlation_result import CorrelationResult


class CrossCorrelator(CorrelatorAlgorithm):
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
    super(CrossCorrelator, self).__init__(self.__class__.__name__, time_series_a, time_series_b)
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
      r = s / denom if denom != 0 else s
      correlations.append([delay, r])
    max_correlation = max(correlations, key=lambda k: k[1])
    self.correlation_result = CorrelationResult(*max_correlation)