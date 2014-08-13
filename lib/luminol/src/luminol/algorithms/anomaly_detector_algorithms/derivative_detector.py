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
from luminol.algorithms.anomaly_detector_algorithms import AnomalyDetectorAlgorithm
from luminol.exceptions import *
from luminol.modules.time_series import TimeSeries
import luminol.utils as utils


class DerivativeDetector(AnomalyDetectorAlgorithm):
  '''
  Derivative Algorithm.
  This method is the derivative version of Method 1.
  Instead of data point value, it uses the derivative of the data point.
  '''
  def __init__(self, time_series, baseline_time_series=None, smoothing_factor=0.2, lag_window_size=None):
    """
    Initializer
    :param TimeSeries time_series: a TimeSeries object.
    :param TimeSeries baseline_time_series: baseline TimeSeries.
    :param float smoothing_factor: smoothing factor.
    :param int lag_window_size: lagging window size.
    """
    super(DerivativeDetector, self).__init__(self.__class__.__name__, time_series, baseline_time_series)
    self.smoothing_factor = (smoothing_factor or 0.2)
    self.lag_window_size = (lag_window_size or int(self.time_series_length * 0.2))

  def _compute_derivatives(self):
    """
    Compute derivatives of the time series.
    """
    derivatives = list()
    for (timestamp, value) in self.time_series.iteritems():
      index = self.time_series.timestamps.index(timestamp)
      if index > 0:
        pre_item = self.time_series.items()[index - 1]
        pre_timestamp = pre_item[0]
        pre_value = pre_item[1]
        td = timestamp - pre_timestamp
        derivative = (value - pre_value) / td if td != 0 else value - pre_value
        derivative = abs(derivative)
        derivatives.append(derivative)
    # First timestamp is assigned the same derivative as the second timestamp.
    derivatives.insert(0, derivatives[0])
    self.derivatives = derivatives

  def _set_scores(self):
    """
    Compute anomaly scores for the time series.
    """
    anom_scores = dict()
    self._compute_derivatives()
    derivatives_ema = utils.compute_ema(self.smoothing_factor, self.derivatives)
    for (timestamp, value) in self.time_series.iteritems():
      index = self.time_series.timestamps[timestamp]
      anom_scores[timestamp] = abs(self.derivatives[index] - derivatives_ema[index])
    self.anom_scores = TimeSeries(anom_scores)