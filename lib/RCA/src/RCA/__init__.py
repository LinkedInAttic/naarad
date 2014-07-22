"""
API for Root Cause Analyzer Module.
The module uses AnomalyDetector and Correlator to find root causes of anomalies.
"""
from collections import defaultdict


class RCA(object):
  def __init__(self, metrix, related_metrices):
    """
    Initializer
    :param metrix: a TimeSeries, a dictionary or a path to a csv file(str)
    :param list related_metrixes: a list of time series.
    """
    self.anomaly_detector = AnomalyDetector(metrix)
    self.related_metrices = related_metrices
    self.anomalies = self.anomaly_detector.get_anomalies()
    self._analyze()

  def _load(self, metrix):
    """
    Load time series.
    :param timeseries: a TimeSeries, a dictionary or a path to a csv file(str).
    :return TimeSeries: a TimeSeries object.
    """
    if isinstance(metrix, TimeSeries):
      return metrix
    if isinstance(metrix, dict):
      return TimeSeries(metrix)
    return TimeSeries(utils.read_csv(metrix))

  def _analyze(self):
    """
    Analyzes if a matrix has anomalies.
    If any anomaly is found, determine if the matrix correlates with any other matrixes.
    To be implemented.
    """
    output = defaultdict(list)
    if self.anomalies:
      for anomaly in self.anomalies:
        start_timestamp, end_timestamp = anomaly.get_time_window()
        extension = (end_timestamp - start_timestamp) / 2
        extended_start_timestamp = start_timestamp - extension
        extended_end_timestamp = end_timestamp + extension
        metrix_scores = self.anomaly_detector.get_all_scores()
        metrix_scores_cropped = metrix_scores.crop(extended_start_timestamp, extended_end_timestamp)
        for entry in self.related_metrices:
          entry_scores = AnomalyDetector(entry).get_all_scores()
          entry_scores_cropped = entry_scores.crop(extended_start_timestamp, extended_end_timestamp)
          entry_correlation_result = Correlator(metrix_scores_cropped, entry_scores_cropped).get_correlation_result()
          record = extended_start_timestamp, extended_end_timestamp, entry_correlation_result.__dict__
          output[entry].append(record)
    self.output = output

    def get_result(self):
      """
      Get the analysis results.
      return: a list represents the analysis result.
      """
      return self.output
