"""
API for Detector Module
"""
import settings
from algorithm import detector_algorithms
import utils


class Detector(object):

  def __init__(self, current_time_series, base_time_series=None):
    """
    initializer
    :param current_time_series: a python timeseries list(list) or a path to a csv file(str).
    :param base_time_series: a python timeseries list(list) or a path to a csv file(str).
    """
    self.time_series = self._load(current_time_series)
    self.baseline = self._load(base_time_series)
    self.anomalies = None
    self._detect()

  def _load(self, time_series):
    """
    load time series of interest into detector
    :param time_series: a python timeseries list(list) or a path to a csv file(str).
    :return: updated instance of Detector.
    """
    if not time_series:
      return None
    if isinstance(time_series, list):
      return time_series
    else:
      return utils.read_csv(time_series)

  def _detect(self):
    """
    detect anomaly.
    :return: true if anomaly is found false otherwise
    """
    if self.baseline:
      # To-Do(Yarong): algorithms to use baseline
      pass
    else:
      alg = getattr(detector_algorithms, settings.DETECTOR_ALGORITHM)
      try:
        a = alg(self.time_series)
        self.anomalies = a.run()
        self.anom_scores = a.get_anom_scores()
      except:
        a = detector_algorithms.ExpAvgDetector(self.time_series)
        self.anomalies = a.run()
        self.anom_scores = a.get_anom_scores()
    return True if self.anomalies else False

  def get_anomalies(self):
    """
    get the detected anomaly data.
    :return: a list of anomaly objects
    """
    return self.anomalies

  def get_all_scores(self):
    """
    get all the anomaly scores as a timeseries
    :return: a python timeseries list
    """
    return self.anom_scores