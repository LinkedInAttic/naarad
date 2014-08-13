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
from luminol.exceptions import *

__all__ = ['bitmap_detector', 'derivative_detector', 'exp_avg_detector']


class AnomalyDetectorAlgorithm(object):
  """
  Base Class for AnomalyDetector algorithm.
  """
  def __init__(self, class_name, time_series, baseline_time_series=None):
    """
    Initializer
    :param str class_name: extended class name.
    :param TimeSeries time_series: a TimeSeries object.
    :param TimeSeries baseline_time_series: baseline TimeSeries.
    """
    self.class_name = class_name
    self.time_series = time_series
    self.time_series_length = len(time_series)
    self.baseline_time_series = baseline_time_series

  def run(self):
    """
    Run the algorithm to get anomalies.
    return list: a list of Anomaly objects.
    """
    self._set_scores()
    return self.anom_scores

  # Need to be extended.
  def _set_scores(self):
    """
    Compute anomaly scores for the time series.
    """
    raise NotImplementedError

  def get_scores(self):
    """
    Get anomaly scores for the time series.
    :return TimeSeries: a TimeSeries representation of the anomaly scores.
    """
    return self.anom_scores