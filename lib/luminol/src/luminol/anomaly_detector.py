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
"""
API for Anomaly Detector Module
This module detects anomalies in a single time series.
"""

from luminol.algorithms import anomaly_detector_algorithms
import luminol.constants as constants
import luminol.exceptions as exceptions
from luminol.modules.time_series import TimeSeries
from luminol.modules.anomaly import Anomaly
import luminol.utils as utils


class AnomalyDetector(object):

  def __init__(self, time_series, baseline_time_series=None, score_percentile_threshold=None, algorithm_name=None, algorithm_params=None,
    refine_algorithm_name=None, refine_algorithm_params=None):
    """
    Initializer
    :param time_series: a TimeSeries, a dictionary or a path to a csv file(str).
    :param baseline_time_series: a TimeSeries, a dictionary or a path to a csv file(str).
    :param float score_percentile_threshold: percentile threshold on anomaly score above which is considered an anomaly.
    :param str algorithm_name: name of the algorithm to use(file name).
    :param dict algorithm_params: additional params for the specific algorithm.
    :param str refine_algorithm_name: name of the refine algorithm to use(file name).
    :param dict refine_algorithm_params: additional params for the specific refine algorithm.
    """
    self.time_series = self._load(time_series)
    self.baseline_time_series = self._load(baseline_time_series)
    if score_percentile_threshold:
      self.score_percentile_threshold = score_percentile_threshold
    else:
      self.score_percentile_threshold = constants.DEFAULT_SCORE_PERCENTILE_THRESHOLD
    if not algorithm_name:
      algorithm_name = constants.ANOMALY_DETECTOR_ALGORITHM
    if not refine_algorithm_params:
      refine_algorithm_name = constants.ANOMALY_DETECTOR_REFINE_ALGORITHM
    # Prepare algorithms and parameters.
    self.algorithm = self._get_algorithm(algorithm_name)
    self.refine_algorithm = self._get_algorithm(refine_algorithm_name)
    self.algorithm_params = {'time_series': self.time_series, 'baseline_time_series': self.baseline_time_series}
    self.algorithm_params = self._prepare_params(algorithm_params, self.algorithm_params)
    self.refine_algorithm_params = self._prepare_params(refine_algorithm_params)
    # Detect anomalies.
    self._detect()

  def _load(self, time_series):
    """
    Load time series.
    :param time_series: a TimeSeries, a dictionary or a path to a csv file(str).
    :return TimeSeries: a TimeSeries object.
    """
    if not time_series:
      return None
    if isinstance(time_series, TimeSeries):
      return time_series
    if isinstance(time_series, dict):
      return TimeSeries(time_series)
    return TimeSeries(utils.read_csv(time_series))

  def _get_algorithm(self, algorithm_name):
    """
    Get the specific algorithm.
    :param str algorithm_name: name of the algorithm to use(file name).
    :return: algorithm object.
    """
    try:
      algorithm = anomaly_detector_algorithms[algorithm_name]
    except KeyError:
      raise exceptions.AlgorithmNotFound('luminol.AnomalyDetector: ' + str(algorithm_name) + ' not found.')
    return algorithm

  def _prepare_params(self, algorithm_params, additional_params={}):
    """
    Format parameter dict.
    :param dict algorithm_params: algorithm parameter dict.
    :param dict additional_params: additional parameter dict.
    :return dict: parameter dict.
    """
    algorithm_params = algorithm_params or {}
    if not isinstance(algorithm_params, dict) or not isinstance(additional_params, dict):
      raise exceptions.InvalidDataFormat('luminol.AnomalyDetector: algorithm parameters passed are not in a dictionary.')
    return dict(algorithm_params.items() + additional_params.items())

  def _detect(self):
    """
    Detect anomaly periods.
    """
    if self.baseline_time_series:
      # To-Do(Yarong): algorithms to use baseline.
      pass
    else:
      try:
        a = self.algorithm(**self.algorithm_params)
        self.anom_scores = a.run()
      except exceptions.NotEnoughDataPoints:
        a = anomaly_detector_algorithms['exp_avg_detector'](self.time_series)
        self.anom_scores = a.run()
    self._detect_anomalies()

  def _detect_anomalies(self):
    """
    Detect anomalies using a threshold on anomaly scores.
    """
    anom_scores = self.anom_scores
    anomaly_intervals, anomalies = list(), list()
    maximal_anom_score = anom_scores.max()
    if maximal_anom_score:
      threshold = maximal_anom_score * self.score_percentile_threshold
      # Find all the anomaly intervals.
      start_timestamp, end_timestamp = None, None
      for (timestamp, value) in anom_scores.iteritems():
        if value > threshold:
          end_timestamp = timestamp
          if not start_timestamp:
            start_timestamp = timestamp
        elif start_timestamp and end_timestamp:
          anomaly_intervals.append([start_timestamp, end_timestamp])
          start_timestamp = None
          end_timestamp = None
      if start_timestamp:
        anomaly_intervals.append([start_timestamp, end_timestamp])
      # Locate the exact anomaly point within each anomaly interval.
      for anomaly_interval in anomaly_intervals:
        anomaly_interval_start_timestamp = anomaly_interval[0]
        anomaly_interval_end_timestamp = anomaly_interval[1]
        anomaly_interval_time_series = anom_scores.crop(anomaly_interval_start_timestamp, anomaly_interval_end_timestamp)
        self.refine_algorithm_params['time_series'] = anomaly_interval_time_series
        e = self.refine_algorithm(**self.refine_algorithm_params)
        scores = e.run()
        maximal_expAvg_score = scores.max()
        # Get the timestamp of the maximal score.
        maximal_expAvg_timestamp = scores.timestamps[scores.values.index(maximal_expAvg_score)]
        anomaly = Anomaly(anomaly_interval_start_timestamp, anomaly_interval_end_timestamp,
          maximal_expAvg_score, maximal_expAvg_timestamp)
        anomalies.append(anomaly)
    self.anomalies = anomalies

  def get_anomalies(self):
    """
    Get anomalies.
    :return list: a list of Anomaly objects.
    """
    return self.anomalies if self.anomalies else None

  def get_all_scores(self):
    """
    Get anomaly scores.
    :return: a TimeSeries object represents anomaly scores.
    """
    return self.anom_scores if self.anom_scores else None