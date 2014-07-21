from collections import defaultdict
import math

import RCA.constants as constants
from RCA.exceptions import *
from RCA.modules.anomaly import Anomaly
from RCA.modules.time_series import TimeSeries
import RCA.utils as utils


class AnomalyDetectorAlgorithm(object):
  """
  Base Class for AnomalyDetector algorithm.
  """
  def __init__(self, class_name, time_series, baseline_time_series=None, score_percentile_threshold=None):
    """
    Initializer
    :param str class_name: extended class name.
    :param TimeSeries time_series: a TimeSeries object.
    :param TimeSeries baseline_time_series: baseline TimeSeries.
    :param float score_percentile_threshold: percentile threshold on anomaly score above which is considered an anomaly.
    """
    self.class_name = class_name
    self.time_series = time_series
    self.time_series_length = len(time_series)
    self.baseline_time_series = baseline_time_series
    if score_percentile_threshold:
      self.score_percentile_threshold = score_percentile_threshold
    else:
      self.score_percentile_threshold = constants.DEFAULT_SCORE_PERCENTILE_THRESHOLD
    self.anom_scores, self.anomalies = list(), list()

  def run(self):
    """
    Run the algorithm to get anomalies.
    return list: a list of Anomaly objects.
    """
    self._set_scores()
    self._detect_anomalies()
    return self.anomalies

  # Need to be extended.
  def _set_scores(self):
    """
    Compute anomaly scores for the time series.
    """
    self.anom_scores = None

  def get_scores(self):
    """
    Get anomaly scores for the time series.
    :return TimeSeries: a TimeSeries representation of the anomaly scores.
    """
    return self.anom_scores

  def _detect_anomalies(self):
    """
    Detect anomalies using a threshold on anomaly scores.
    """
    anom_scores = self.anom_scores
    anomaly_intervals, anomalies = list(), list()
    maximal_anom_score = anom_scores.max()
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
      e = ExpAvgDetector(anomaly_interval_time_series)
      e._set_scores()
      scores = e.get_scores()
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
    return self.anomalies


class ExpAvgDetector(AnomalyDetectorAlgorithm):
  """
  Method 1: Exponential Moving Average.
  This method uses a data point's deviation from the exponential moving average of a lagging window
  to determine its anomaly score.
  """
  def __init__(self, time_series, baseline_time_series=None, score_percentile_threshold=None,
    smoothing_factor=None, lag_window_size=None):
    """
    Initializer
    :param TimeSeries time_series: a TimeSeries object.
    :param TimeSeries baseline_time_series: baseline TimeSeries.
    :param float score_percentile_threshold: percentile threshold on anomaly score above which is considered an anomaly.
    :param float smoothing_factor: smoothing factor for computing exponential moving average.
    :param int lag_window_size: lagging window size.
    :param int future_window_size: future_window_size.
    """
    super(ExpAvgDetector, self).__init__(self.__class__.__name__, time_series, baseline_time_series, score_percentile_threshold)
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


class BitmapDetector(AnomalyDetectorAlgorithm):
  """
  Method 2: Bitmap Algorithm.
  This method breaks time series into chunks and uses the frequency of similar chunks
  to determine anomaly scores.
  The ideas are from this paper:
  Assumption-Free Anomaly Detection in Time Series(http://alumni.cs.ucr.edu/~ratana/SSDBM05.pdf).
  """
  def __init__(self, time_series, baseline_time_series=None, score_percentile_threshold=None, precision=None,
    lag_window_size=None, future_window_size=None, chunk_size=None):
    """
    Initializer
    :param TimeSeries time_series: a TimeSeries object.
    :param TimeSeries baseline_time_series: baseline TimeSeries.
    :param float score_percentile_threshold: percentile threshold on anomaly score above which is considered an anomaly.
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


class DerivativeDetector(AnomalyDetectorAlgorithm):
  '''
  Method 3: Derivative Algorithm.
  This method is the derivative version of Method 1.
  Instead of data point value, it uses the derivative of the data point.
  '''
  def __init__(self, time_series, baseline_time_series=None, score_percentile_threshold=None, smoothing_factor=0.2, lag_window_size=None):
    """
    Initializer
    :param TimeSeries time_series: a TimeSeries object.
    :param TimeSeries baseline_time_series: baseline TimeSeries.
    :param float score_percentile_threshold: percentile threshold on anomaly score above which is considered an anomaly.
    :param float smoothing_factor: smoothing factor.
    :param int lag_window_size: lagging window size.
    """
    super(DerivativeDetector, self).__init__(self.__class__.__name__, time_series, baseline_time_series)
    self.smoothing_factor = smoothing_factor if smoothing_factor is not None else 0.2
    self.lag_window_size = lag_window_size if lag_window_size is not None else int(self.time_series_length * 0.2)

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