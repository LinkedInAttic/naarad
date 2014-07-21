"""
API for Anomaly Detector Module
This module detects anomalies in a single time series.
"""

from RCA.algorithms import anomaly_detector_algorithms
import RCA.constants as constants
import RCA.exceptions as exceptions
from RCA.modules.time_series import TimeSeries
import RCA.utils as utils


class AnomalyDetector(object):

  def __init__(self, time_series, baseline_time_series=None, algorithm=None, algorithm_params=None):
    """
    Initializer
    :param time_series: a TimeSeries, a dictionary or a path to a csv file(str).
    :param baseline_time_series: a TimeSeries, a dictionary or a path to a csv file(str).
    :param str algorithm: name of the algorithm to use.
    :param dict algorithm_params: additional params for the specific algorithm.
    """
    self.time_series = self._load(time_series)
    self.baseline_time_series = self._load(baseline_time_series)
    self.algorithm_params = {'time_series': self.time_series, 'baseline_time_series': self.baseline_time_series}
    self._get_algorithm_and_params(algorithm, algorithm_params)
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

  def _get_algorithm_and_params(self, algorithm, algorithm_params):
    """
    Get the specific algorithm and merge the algorithm params.
    :param str algorithm: name of the algorithm to use.
    :param dict algorithm_params: additional params for the specific algorithm.
    """
    if not algorithm:
      algorithm = constants.ANOMALY_DETECTOR_ALGORITHM
    try:
      self.algorithm = getattr(anomaly_detector_algorithms, algorithm)
    except AttributeError:
      raise exceptions.AlgorithmNotFound('RCA.AnomalyDetector: ' + str(algorithm) + ' not found.')
    # Construct a dictionary for algorithm parameters.
    if algorithm_params:
      if not isinstance(algorithm_params, dict):
        raise exceptions.InvalidDataFormat('RCA.AnomalyDetector: algorithm_params passed is not a dictionary.')
      else:
        self.algorithm_params = dict(algorithm_params.items() + self.algorithm_params.items())

  def _detect(self):
    """
    Detect anomalies.
    """
    if self.baseline_time_series:
      # To-Do(Yarong): algorithms to use baseline.
      pass
    else:
      try:
        a = self.algorithm(**self.algorithm_params)
        self.anomalies = a.run()
        self.anom_scores = a.get_scores()
      except exceptions.NotEnoughDataPoints:
        a = anomaly_detector_algorithms.ExpAvgDetector(self.time_series)
        self.anomalies = a.run()
        self.anom_scores = a.get_scores()

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