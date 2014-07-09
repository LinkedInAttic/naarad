import algorithms_ipm
import os
import sys


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils

"""
Algorithms that compute anomaly scores for timeseries
corresponding constant in setting.py: ANOMALY_SCORE_ALGORITHM
algorithm should take a timeseries as input, and return a timeseries
with the values as the anomaly scores
"""

def Bitmap(data):
  """
  use Bitmap to compute anomaly scores
  :param list data: a timeseries
  :return: a timeseries where values are anomaly scores
  """
  a = algorithms_ipm.BitmapDetector(data)
  a.detect_anom_use_both_lag_and_future_window()
  return a.get_anomaly_data()

def Ema(data):
  """
  use ema to compute anomaly scores
  :param list data: a timeseries
  :return: a timeseries where values are anomaly scores
  """
  a = algorithms_ipm.expAvgDetector(data)
  a.compute_anom_data_decay_all()
  return a.get_anomaly_data()

"""
Algorithms that identifies anomaly using anomaly scores
corresponding constant in setting.py: ANOMALY_IDENTIFY_ALGORITHM
algorithm should take a anomaly score timeseries as input, and return
a formated anomaly
"""

def Ten_percent(data):
  """
  draw ten percent of the score range as a anomaly threshold
  :param list data: a anomaly score timeseries
  :return: a formated list of anomalies
  """
  itv = list()
  anomalies =list()
  start_t = None
  end_t = None
  v_max = max(utils.get_values(data))
  ten = v_max*0.1
  for [t, v] in data:
    if v > ten:
      end_t = t
      if not start_t:
        start_t =t
    elif start_t and end_t:
      itv.append([start_t, end_t])
      start_t = None
      end_t = None
  for p in itv:
    d = utils.filter_data(data, p[0], p[1])
    e = algorithms_ipm.expAvgDetector(d)
    e.compute_anom_data_decay_all()
    scores = e.get_anomaly_data()
    s_max = max(scores, key = lambda k : k[1])
    anomalies.append([p[0], p[1], s_max[1], s_max[0]])
  return anomalies