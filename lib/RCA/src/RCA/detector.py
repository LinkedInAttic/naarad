"""
API for Detector Module
"""
import settings
from algorithm import detector_algorithms
import utils

class detector(object):

  def __init__(self, data_or_data_path, base_data_or_data_path = None):
    """
    initializer
    """
    self.data = self._load(data_or_data_path)
    self.baseline = self._load(base_data_or_data_path)
    self.anomalies = None
    self._detect()

  def _load(self, data_or_data_path):
    """
    load data of interest into detector
    :param data_or_data_path: a python timeseries list(list) or a path to a csv file(str).
    :return: updated instance of Detector.
    """
    if not data_or_data_path:
      return None
    if isinstance(data_or_data_path, list):
      return data_or_data_path
    else:
      return utils.read_csv(data_or_data_path)

  def _detect(self):
    """
    detect anomaly.
    :return: true if anomaly is found false otherwise
    """
    if self.baseline:
      #To-Do(Yarong): algorithms to use baseline
      pass
    else:
      alg = getattr(detector_algorithms, settings.DETECTOR_ALGORITHM)
      try:
        a = alg(self.data)
        self.anomalies = a.run()
        self.anom_scores = a.get_anom_scores()
      except:
        a = detector_algorithms.expAvgDetector(self.data)
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