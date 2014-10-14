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
__author__ = 'rmaheshw'

from luminol import utils
from luminol.algorithms.anomaly_detector_algorithms import AnomalyDetectorAlgorithm
from luminol.constants import *
from luminol.modules.time_series import TimeSeries

class AbsoluteThreshold(AnomalyDetectorAlgorithm):
  """
  Anomalies are those data points that are above a pre-specified threshold value.
  This algorithm does not take baseline time series.
  """
  def __init__(self, time_series, absolute_threshold_value, baseline_time_series=None):
    """

    :param time_series:
    :param absolute_threshold_value:
    :return:
    """
    super(AbsoluteThreshold, self).__init__(self.__class__.__name__, time_series, baseline_time_series)
    self.absolute_threshold_value = absolute_threshold_value

  def _set_scores(self):
    """
    Compute anomaly scores for the time series
    This algorithm just takes the diff of threshold with current value as anomaly score
    """
    anom_scores = {}
    for timestamp, value in self.time_series.items():
      if value > self.absolute_threshold_value:
        anom_scores[timestamp] = value - self.absolute_threshold_value
    self.anom_scores = TimeSeries(self._denoise_scores(anom_scores))

