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
API for Correlator Module
This module finds correlation between two time series.
"""

from luminol.algorithms import correlator_algorithms
import luminol.constants as constants
import luminol.exceptions as exceptions
from luminol.modules.time_series import TimeSeries
import luminol.utils as utils


class Correlator(object):
  def __init__(self, time_series_a, time_series_b, algorithm_name=None, algorithm_params=None):
    """
    Initializer
    :param time_series_a: a TimeSeries, a dictionary or a path to a csv file(str).
    :param time_series_b: a TimeSeries, a dictionary or a path to a csv file(str).
    :param str algorithm_name: name of the algorithm to use.
    :param dict algorithm_params: additional params for the specific algorithm.
    """
    self.time_series_a = self._load(time_series_a)
    self.time_series_b = self._load(time_series_b)
    self._sanity_check()
    self.algorithm_params = {'time_series_a': self.time_series_a, 'time_series_b': self.time_series_b}
    self._get_algorithm_and_params(algorithm_name, algorithm_params)
    self._correlate()

  def _load(self, time_series):
    """
    Load time series.
    :param timeseries: a TimeSeries, a dictionary or a path to a csv file(str).
    :return TimeSeries: a TimeSeries object.
    """
    if isinstance(time_series, TimeSeries):
      return time_series
    if isinstance(time_series, dict):
      return TimeSeries(time_series)
    return TimeSeries(utils.read_csv(time_series))

  def _get_algorithm_and_params(self, algorithm_name, algorithm_params):
    """
    Get the specific algorithm and merge the algorithm params.
    :param str algorithm: name of the algorithm to use.
    :param dict algorithm_params: additional params for the specific algorithm.
    """
    if not algorithm_name:
      algorithm_name = constants.CORRELATOR_ALGORITHM
    try:
      self.algorithm = correlator_algorithms[algorithm_name]
    except KeyError:
      raise exceptions.AlgorithmNotFound('luminol.Correlator: ' + str(algorithm_name) + ' not found.')
    # Merge parameters.
    if algorithm_params:
      if not isinstance(algorithm_params, dict):
        raise exceptions.InvalidDataFormat('luminol.Correlator: algorithm_params passed is not a dictionary.')
      else:
        self.algorithm_params = dict(algorithm_params.items() + self.algorithm_params.items())

  def _sanity_check(self):
    """
    Check if the time series have more than two data points.
    """
    if len(self.time_series_a) < 2 or len(self.time_series_b) < 2:
      raise exceptions.NotEnoughDataPoints("luminol.Correlator: Too few data points!")

  def _correlate(self):
    """
    Run correlation algorithm.
    """
    a = self.algorithm(**self.algorithm_params)
    self.correlation_result = a.run()

  def get_correlation_result(self):
    """
    Get correlation result.
    :return CorrelationResult: a CorrelationResult object.
    """
    return self.correlation_result

  def is_correlated(self, threshold=None):
    """
    Compare with a threshold to determine whether two timeseries correlate to each other.
    :return: a CorrelationResult object if two time series correlate otherwise false.
    """
    return self.correlation_result if self.correlation_result.coefficient >= threshold else False