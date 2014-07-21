"""
Utilities for RCA
"""
import csv
import time

import exceptions

def read_csv(csv_name):
  """
  Read data from a csv file into a dictionary.
  :param str csv_name: path to a csv file.
  :return dict: a dictionary represents the data in file.
  """
  data = {}
  if not isinstance(csv_name, str):
    raise exceptions.InvalidDataFormat('RCA.utils: csv_name has to be a string!')
  with open(csv_name, 'r') as csv_data:
    reader = csv.reader(csv_data, delimiter=',', quotechar='|')
    for row in reader:
      try:
        key = to_epoch(row[0])
        value = float(row[1])
        data[key] = value
      except ValueError:
        pass
  return data

def to_epoch(t_str):
  """
  Covert a timestamp string to an epoch number.
  :param str t_str: a timestamp string.
  :return int: epoch number of the timestamp.
  """
  try:
    t = time.mktime(time.strptime(t_str, "%Y-%m-%d %H:%M:%S.%f"))
  except:
    try:
      t = time.mktime(time.strptime(t_str, "%Y-%m-%d %H:%M:%S"))
    except:
      return float(t_str)
  return t

def compute_ema(smoothing_factor, points):
  '''
  Compute exponential moving average of a list of points.
  :param float smoothing_factor: the smoothing factor.
  :param list points: the data points.
  :return list: all ema in a list.
  '''
  ema = list()
  # The initial point has a ema equal to itself.
  if(len(points) > 0):
    ema.append(points[0])
  for i in range(1, len(points)):
    ema.append(smoothing_factor * points[i] + (1 - smoothing_factor) * ema[i - 1])
  return ema