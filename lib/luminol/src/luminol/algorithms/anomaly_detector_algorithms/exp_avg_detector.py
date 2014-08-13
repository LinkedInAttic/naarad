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
import luminol.constants as constants
from luminol.exceptions import *
from luminol.modules.time_series import TimeSeries
import luminol.utils as utils


class ExpAvgDetector(AnomalyDetectorAlgorithm):
  """
  Exponential Moving Average.
  This method uses a data point's deviation from the exponential moving average of a lagging window
  to determine its anomaly score.
  """
  def __init__(self, time_series, baseline_time_series=None, smoothing_factor=None, lag_window_size=None):
    """
    Initializer
    :param TimeSeries time_series: a TimeSeries object.
    :param TimeSeries baseline_time_series: baseline TimeSeries.
    :param float smoothing_factor: smoothing factor for computing exponential moving average.
    :param int lag_window_size: lagging window size.
    """
    super(ExpAvgDetector, self).__init__(self.__class__.__name__, time_series, baseline_time_series)
    self.smoothing_factor = smoothing_factor if smoothing_factor > 0 else constants.DEFAULT_EMA_SMOTHING_FACTOR
    self.lag_window_size = lag_window_size if lag_window_size else int(self.time_series_length * constants.DEFAULT_EMA_WINDOW_SIZE_PCT)

  def _compute_anom_score(self, lag_window_points, point):
    """
    Compute anomaly score for a single data point.
    Anomaly score for a single data point(t,v) equals: abs(v - ema(lagging window)).
    :param list lag_window_points: values in the lagging window.
    :param float point: data point value.
    :return float: the anomaly score.
    """
    ema = utils.compute_ema(self.smoothing_factor, lag_window_points)[-1]
    return abs(point - ema)

  def _compute_anom_data_using_window(self):
    """
    Compute anomaly scores using a lagging window.
    """
    anom_scores = dict()
    values = self.time_series.values
    for (timestamp, value) in self.time_series.iteritems():
      index = self.time_series.timestamps.index(timestamp)
      if index < self.lag_window_size:
        anom_scores[timestamp] = self._compute_anom_score(values[:index + 1], value)
      else:
        anom_scores[timestamp] = self._compute_anom_score(values[index - self.lag_window_size: index + 1], value)
    self.anom_scores = TimeSeries(anom_scores)

  def _compute_anom_data_decay_all(self):
    """
    Compute anomaly scores using a lagging window covering all the data points before.
    """
    anom_scores = dict()
    values = self.time_series.values
    ema = utils.compute_ema(self.smoothing_factor, values)
    for (timestamp, value) in self.time_series.iteritems():
      index = self.time_series.timestamps.index(timestamp)
      anom_score = abs(value - ema[index])
      anom_scores[timestamp] = anom_score
    self.anom_scores = TimeSeries(anom_scores)

  def _set_scores(self):
    """
    Compute anomaly scores for the time series.
    Currently uses a lagging window covering all the data points before.
    """
    self._compute_anom_data_decay_all()