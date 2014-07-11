"""
API for Anomaly Detection Module
"""
import settings
from algorithm import algorithms
import utils

class detector(object):

  def __init__(self):
    """
    initializer
    """
    self.anomalies = None
    self.anom_scores = None
    self.baseline = None
    self.data = None

  def load(self, data_or_data_path):
    """
    load data of interest into detector
    :param data_or_data_path: a python timeseries list(list) or a path to a csv file(str).
    :return: updated instance of Detector.
    """
    if isinstance(data_or_data_path, list):
      self.data = data
    else:
      self.data = utils.read_csv(data_or_data_path)
    return self

  def load_baseline(data_or_data_path):
    """
    load a baseline time series into detector.
    which will be used when conducting anomaly detection.
    :param data_or_data_path: a python timeseries list(list) or a path to a csv file(str).
    :return: updated instance of Detector.
    """
    if isinstance(data_or_data_path, list):
      self.baseline = data
    else:
      self.baseline = utils.read_csv(data_or_data_path)
    return self

  def detect(self, use_baseline=False):
    """
    detect anomaly.
    :return: true if anomaly is found false otherwise
    """
    if use_baseline:
      if self.baseline:
        # To-Do(Yarong):algorithms to use baseline/could be applied as a filter on top of the original one
        pass
      else:
        raise Exception("RCA.detector: baseline timeseries not loaded!")
    else:
      alg = getattr(algorithms, settings.ANOMALY_SCORE_ALGORITHM)
      try:
        self.anom_scores = alg(self.data)
      except:
        self.anom_scores = algorithms.Ema(self.data)
      alg = getattr(algorithms, settings.ANOMALY_IDENTIFY_ALGORITHM)
      self.anomalies = alg(self.anom_scores)
    return True if self.anomalies else False

  def get_anomaly(self):
    """
    get the detected anomaly data.
    :return: a list of dic with the following info:
    {
      str start_time: when this anomaly starts
      str end_time:   when this anomaly ends
      int score:      anomaly score(0-100)
      str time_point: a timestamp indicating when the anomaly likely happened.
    }
    """
    return self.anomalies

  def get_all_scores(csv=None):
    """
    get all the anomaly scores as a timeseries
    :param str csv: a path to a csv file will the scores should be written to.
    :return: a python timeseries list
    """
    return self.anom_scores
