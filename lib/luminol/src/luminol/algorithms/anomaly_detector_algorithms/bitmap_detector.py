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
from collections import defaultdict
import math

from luminol.algorithms.anomaly_detector_algorithms import AnomalyDetectorAlgorithm
import luminol.constants as constants
from luminol.exceptions import *
from luminol.modules.time_series import TimeSeries


class BitmapDetector(AnomalyDetectorAlgorithm):
  """
  Bitmap Algorithm.
  This method breaks time series into chunks and uses the frequency of similar chunks
  to determine anomaly scores.
  The ideas are from this paper:
  Assumption-Free Anomaly Detection in Time Series(http://alumni.cs.ucr.edu/~ratana/SSDBM05.pdf).
  """
  def __init__(self, time_series, baseline_time_series=None, precision=None, lag_window_size=None,
    future_window_size=None, chunk_size=None):
    """
    Initializer
    :param TimeSeries time_series: a TimeSeries object.
    :param TimeSeries baseline_time_series: baseline TimeSeries.
    :param int precision: how many sections to categorize values.
    :param int lag_window_size: lagging window size.
    :param int future_window_size: future window size.
    :param int chunk_size: chunk size.
    """
    super(BitmapDetector, self).__init__(self.__class__.__name__, time_series, baseline_time_series)
    self.precision = precision if precision and precision > 0 else constants.DEFAULT_BITMAP_PRECISION
    self.chunk_size = chunk_size if chunk_size and chunk_size > 0 else constants.DEFAULT_BITMAP_CHUNK_SIZE
    if lag_window_size:
      self.lag_window_size = lag_window_size
    else:
      self.lag_window_size = int(self.time_series_length * constants.DEFAULT_BITMAP_LAGGING_WINDOW_SIZE_PCT)
    if future_window_size:
      self.future_window_size = future_window_size
    else:
      self.future_window_size = int(self.time_series_length * constants.DEFAULT_BITMAP_LEADING_WINDOW_SIZE_PCT)
    self._sanity_check()

  def _sanity_check(self):
    """
    Check if there are enough data points.
    """
    windows = self.lag_window_size + self.future_window_size
    if (not self.lag_window_size or not self.future_window_size
      or self.time_series_length < windows or windows < constants.DEFAULT_BITMAP_MINIMAL_POINTS_IN_WINDOWS):
        raise NotEnoughDataPoints

  def _generate_SAX_single(self, sections, value):
    """
    Generate SAX representation(Symbolic Aggregate approXimation) for a single data point.
    Read more about it here: Assumption-Free Anomaly Detection in Time Series(http://alumni.cs.ucr.edu/~ratana/SSDBM05.pdf).
    :param dict sections: value sections.
    :param float value: value to be categorized.
    :return str: a SAX representation.
    """
    sax = 0
    for section_number in sections.keys():
      section_lower_bound = sections[section_number]
      if value >= section_lower_bound:
        sax = section_number
      else:
        break
    return str(sax)

  def _generate_SAX(self):
    """
    Generate SAX representation for all values of the time series.
    """
    sections = dict()
    self.value_min = self.time_series.min()
    self.value_max = self.time_series.max()
    # Break the whole value range into different sections.
    section_height = (self.value_max - self.value_min) / self.precision
    for section_number in range(self.precision):
      sections[section_number] = self.value_min + section_number * section_height
    # Generate SAX representation.
    self.sax = ''.join(self._generate_SAX_single(sections, value) for value in self.time_series.values)

  def _construct_SAX_chunk_dict(self, sax):
    """
    Form a chunk frequency dictionary from a SAX representation.
    :param str sax: a SAX representation.
    :return dict: frequency dictionary for chunks in the SAX representation.
    """
    frequency = defaultdict(int)
    chunk_size = self.chunk_size
    length = len(sax)
    for i in range(length):
      if i + chunk_size < length:
        chunk = sax[i: i + chunk_size]
        frequency[chunk] += 1
    return frequency

  def _compute_anom_score_between_two_windows(self, lag_window_sax, future_window_sax):
    """
    Compute distance difference between two windows' chunk frequencies,
    which is then marked as the anomaly score of the data point on the window boundary in the middle.
    :param str lag_window_sax: SAX representation of values in the lagging window.
    :param str future_window_sax: SAX representation of values in the future window.
    :return float: the anomaly score.
    """
    lag_window_chunk_dict = self._construct_SAX_chunk_dict(lag_window_sax)
    future_window_chunk_dict = self._construct_SAX_chunk_dict(future_window_sax)
    score = 0
    for chunk in lag_window_chunk_dict:
      if chunk in future_window_chunk_dict:
        score += math.pow(future_window_chunk_dict[chunk] - lag_window_chunk_dict[chunk], 2)
      else:
        score += math.pow(lag_window_chunk_dict[chunk], 2)
    for chunk in future_window_chunk_dict:
      if chunk not in lag_window_chunk_dict:
        score += math.pow(future_window_chunk_dict[chunk], 2)
    return score

  def _set_scores(self):
    """
    Compute anomaly scores for the time series by sliding both lagging window and future window.
    """
    anom_scores = dict()
    self._generate_SAX()
    for timestamp in self.time_series.iterkeys():
      index = self.time_series.timestamps.index(timestamp)
      if index < self.lag_window_size or index > self.time_series_length - self.future_window_size:
        anom_scores[timestamp] = 0
      else:
        lag_window_sax = self.sax[index - self.lag_window_size: index + 1]
        future_window_sax = self.sax[index: index + self.future_window_size]
        anom_scores[timestamp] = self._compute_anom_score_between_two_windows(lag_window_sax, future_window_sax)
    self.anom_scores = TimeSeries(anom_scores)