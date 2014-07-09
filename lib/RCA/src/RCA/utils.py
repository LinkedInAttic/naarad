"""
Utilities for luminol
"""
import csv
import sys
from datetime import datetime
import time

def read_csv(csv_name):
  """
  read data from csv in to a list
  :param str csv_name: path to csv file
  :return: a python timeseries list(list)
  """
  data = []
  with open(csv_name, 'r') as csv_data:
    reader = csv.reader(csv_data, delimiter=',', quotechar='|')
    for row in reader:
      try:
        row[1] = float(row[1])
        data.append(row[:2])
      except ValueError:
        pass
  return data

def to_epoch(t_str):
  """
  covert a timestamp string to epoch num
  :param str t_str: a timestamp string
  :return int: epoch num of the timestamp
  """
  try:
    t = time.mktime(time.strptime(t_str, "%Y-%m-%d %H:%M:%S.%f"))
  except:
    try:
      t = time.mktime(time.strptime(t_str, "%Y-%m-%d %H:%M:%S"))
    except:
      return float(t_str)
  return t

def filter_data(data, start_t, end_t):
  """
  filter a timeseries using a start time and an end time
  :param list data: timeseries data to be filtered
  :param str start_t: timestamp indicates the start time
  :param str end_t: timestamp indicates the end time
  :return list: the filtered timeseries
  """
  filtered = list()
  for [t, v] in data:
    if t >= start_t and t <= end_t:
      filtered.append([t, v])
    elif t > end_t:
      break
  return filtered

def align_two_timeseries((s1, s2)):
  """
  align two timeseries according to their timestamps
  fill in the gaps
  :param tuple (s1, s2): the two timeseries to be aligned
  :return tuple: the adjusted two timeseries
  """
  s1_rv = list()
  s2_rv = list()
  i = 0
  j = 0
  while i < len(s1) and j < len(s2):
    if s1[i][0] == s2[j][0]:
      s1_rv.append(s1[i])
      s2_rv.append(s2[j])
      i+=1
      j+=1
    elif s1[i][0] < s2[j][0]:
      s1_rv.append(s1[i])
      s2_rv.append([s1[i][0], s2[j][1]])
      i+=1
    else:
      s2_rv.append(s2[j])
      s1_rv.append([s2[j][0],s1[i][1]])
      j+=1
  while i < len(s1):
    s1_rv.append(s1[i])
    s2_rv.append([s1[i][0], s2[-1][1]])
    i+=1
  while j < len(s2):
    s2_rv.append(s2[j])
    s1_rv.append([s2[j][0],s1[-1][1]])
    j+=1
  return s1_rv, s2_rv

def get_values(ts):
  """
  given a timeseries, return all the values in a list
  :param list ts: a timeseries
  :return list: all the values of the timeseries in a list
  """
  values = list()
  for [t, v] in ts:
    values.append(v)
  return values

def write_data(csv_name, data):
  '''
  write data to a csv file from a list
  '''
  with open(csv_name, 'w+') as csv_file:
    writer = csv.writer(csv_file)
    for row in data:
      writer.writerow(row)

def auto_increment(lst, key):
  '''
  auto-increment a count dictionary
  :param dict lst: a count dictionary
  :param key: a key to be incremented
  :return dict: the updated dictionary
  '''
  lst[key] = lst[key]+1 if key in lst else 1
  return lst

def computer_ema(smoothing_factor, points):
  '''
  compute exponential moving average of a list of points
  :param float smoothing_factor: the smoothing factor
  :param list points: the data points
  :return list: all ema in an array
  '''
  ema  = list()
  #the initial point has a ema equal to itself
  if(len(points) > 0):
    ema.append(points[0])
  for i in range(1, len(points)):
    ema.append(smoothing_factor*points[i]+(1-smoothing_factor)*ema[i-1])
  return ema