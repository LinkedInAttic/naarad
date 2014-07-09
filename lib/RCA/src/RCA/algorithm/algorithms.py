import algorithms_ipm
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils

"""
Algorithms that compute anomaly scores for timeseries
corresponding constant in setting.py: ANOMALY_SCORE_ALGORITHM
algorithm should take a timeseries as input, and return a timeseries
with the values as the anomaly scores
"""

def Bitmap(data):
  a = algorithms_ipm.BitmapDetector(data)
  a.detect_anom_use_both_lag_and_future_window()
  return a.get_anomaly_data()

"""
Algorithms that identifies anomaly using anomaly scores
corresponding constant in setting.py: ANOMALY_IDENTIFY_ALGORITHM
algorithm should take a anomaly score timeseries as input, and return
a formated anomaly
"""

def Ten_percent(data):
  itv = list()
  anomalies =list()
  start_t = None
  end_t = None

  def f(x): return x[1]

  v_max = max(data, key=f)
  ten = v_max*0.1
  for [t, v] in data:
    if v > ten:
      end_t = t
      if not start_t:
        start_t =t
    else:
      itv.append([start_t, end_t])
      start_t = None
      end_t = None
  for p in itv:
    d = filter_data(data, p[0], p[1])
    e = algorithms_ipm.expAvgDetector(d)
    e.compute_anom_data_decay_all()
    scores = e.get_anomaly_data()
    s_max = max(scores, key=f)
    anomalies.append([p[0], p[1], s_max[1], s_max[0]])
  return anomalies