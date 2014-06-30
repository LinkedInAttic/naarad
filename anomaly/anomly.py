import csv
import sys
import time
import statistics

import utils

"""
this two options/consts will be removed
currently kept for comparing different approaches
"""
STATIC_PATH = 'static/anom/'
CHECK_PERF = True

class Detector(object):
  """
  Base Class for Amomaly Detection
  given a path to a csv containing timeseries data or a list of [timestamp, value]
  generates a list of [timestamp, anomaly_score] or a csv containing that
  """
  def __init__(self, name, data_path_or_data):
    self.name = name
    if isinstance(data_path_or_data, list):
      #if data is given as a list
      self.data = data_path_or_data
    else:
      #if data_path is given
      self.read_data(data_path_or_data)

  def read_data(self, csv_path):
    self.data = utils.read_data(csv_path)
    self.data_length = len(self.data)
    self.csv_name = csv_path.split("/")[-1]
    self.time = time.time()

  #dummy function
  def set_anom_data(self):
    self.anom_data = list()

  def write_anom_data(self, csv_to_write_path):
    utils.write_data(csv_to_write_path, self.anom_data)
    self.anom_csv_path = csv_to_write_path

  def get_anom_data_path(self):
    if CHECK_PERF:
      return self.anom_csv_path, time.time()-self.time
    return self.anom_csv_path

  def get_anom_data(self):
    if self.anom_csv_path:
      return utils.read_data(self.anom_csv_path)
    return None


class expAvgDetector(Detector):
  """
  METHOD 1: Exponential Moving Avgs
  this method uses a data point's deviation from the expoential moving avg of a lagging lag window
  to determine the anomaly score
  """
  def __init__(self, data_path_or_data, smoothing_factor=0.2, lag_window_size=None):
    super(expAvgDetector, self).__init__(self.__class__.__name__, data_path_or_data)
    self.smoothing_factor = smoothing_factor if smoothing_factor > 0 else 0.2
    self.lag_window_size = lag_window_size if lag_window_size is not None else int(self.data_length*0.2)

  def _compute_anom_score(self, lag_window_points, point):
    stdev = statistics.stdev(lag_window_points)
    ema = utils.computer_ema(self.smoothing_factor,lag_window_points)[-1]
    return abs(point-ema)/stdev if stdev > 0 else abs(point-ema)

  def set_anom_data(self, csv_name=None):
    anom_data = list()
    points = list()
    for [timestamp, value] in self.data:
      points.append(value)
    for i in xrange(1, len(points)):
      point = points[i]
      if i < self.lag_window_size:
        entry = [self.data[i][0], self._compute_anom_score(points[:i+1], point), 3]
      else:
        entry = [self.data[i][0], self._compute_anom_score(points[i-self.lag_window_size: i+1], point), 3]
      anom_data.append(entry)
    self.anom_data = anom_data
    self.write_anom_data(STATIC_PATH+self.csv_name) if csv_name is None else self.write_anom_data(STATIC_PATH+csv_name)
    return self.get_anom_data_path()


class BitmapDetector(Detector):
  """
  METHOD 2: Bitmap Detector
  this method breaks time series into chunks and use frequency of similar chuncks
  to determine anomaly and anomaly score
  """
  def __init__(self, data_path_or_data, precision=4, lag_window_size=None, chunk_size=2):
    super(BitmapDetector, self).__init__(self.__class__.__name__, data_path_or_data)
    self.precision = precision if precision is not None and precision > 0 else 4
    self.lag_window_size = lag_window_size if lag_window_size is not None else int(self.data_length*0.2)
    self.chunk_size = chunk_size if chunk_size is not None and chunk_size > 0 else 2

  def _generate_SAX_single(self, sections, section_height, value):
    sax = 0
    for s in sections:
      if value >= sections[s]:
        sax = s
      else:
        break
    return sax

  def _generate_SAX(self):
    value_min = sys.float_info.max
    value_max = sys.float_info.min
    sections = dict()
    sax = str()
    #set global min and global max
    for entry in self.data:
      value = float(entry[1])
      value_min = value if value < value_min else value_min
      value_max = value if value > value_max else value_max
    self.data_min = value_min
    self.data_max = value_max
    #break data value range into different sections
    section_height = (value_max - value_min)/self.precision
    for s in xrange(0,self.precision):
      sections[s] = value_min+s*section_height
    #generate SAX for each data point
    for entry in self.data:
      sax += str(self._generate_SAX_single(sections, section_height, entry[1]))
    self.sax = sax

  def _compute_anom_score(self, lag_window_sax, cur_sax, chunk_size):
    freq = dict()
    s_len = len(lag_window_sax)
    for i in xrange(0, s_len):
      if i + chunk_size < s_len:
        chunk = lag_window_sax[i:i+chunk_size]
        freq = utils.auto_increment(freq, chunk)
        freq = utils.auto_increment(freq, 'total')
    freq_sorted =  sorted(freq, key = lambda k: freq[k], reverse = True)
    base_freq = freq[freq_sorted[1]]
    return 1-float(freq[cur_sax])/base_freq

  def _detect_anom_use_lag_window(self):
    chunk_size = self.chunk_size
    scores = list()
    anom_data = list()
    self._generate_SAX()
    sax_len = len(self.sax)
    for i in xrange(chunk_size+1, sax_len):
      if i < self.lag_window_size:
        score = self._compute_anom_score(self.sax[:i+1], self.sax[i-chunk_size:i], chunk_size)
      else:
        score = self._compute_anom_score(self.sax[i-self.lag_window_size:i+1], self.sax[i-chunk_size:i], chunk_size)
      anom_data.append([self.data[i][0], score])
    self.anom_data = anom_data

  def _detect_anom_use_full_range(self):
    #use the whole data set as the lagging window
    chunk_size = self.chunk_size
    scores = list()
    anom_data = list()
    freq = dict()
    self._generate_SAX()
    sax_len = len(self.sax)
    for i in xrange(0, sax_len):
      if i + chunk_size < sax_len:
        chunk = self.sax[i:i+chunk_size]
        freq = utils.auto_increment(freq, chunk)
        freq = utils.auto_increment(freq, 'total')
    for i in xrange(chunk_size+1, sax_len):
      score = 1-float(freq[self.sax[i-chunk_size:i]])/float(freq['total'])
      anom_data.append([self.data[i][0], score])
    self.anom_data = anom_data

  def set_anom_data(self, csv_name=None):
    self._detect_anom_use_full_range() if self.lag_window_size < 0 else self._detect_anom_use_lag_window()
    self.write_anom_data(STATIC_PATH+self.csv_name) if csv_name is None else self.write_anom_data(STATIC_PATH+csv_name)
    return self.get_anom_data_path()


class DetrivativeDetector(Detector):
  '''
  METHOD 3: Detrivative
  this method is the derivative version of METHOD 1
  '''
  def __init__(self, data_path_or_data, smoothing_factor=0.2, lag_window_size=None):
    super(DetrivativeDetector, self).__init__(self.__class__.__name__, data_path_or_data)
    self.smoothing_factor = smoothing_factor if smoothing_factor is not None else 0.2
    self.lag_window_size = lag_window_size if lag_window_size is not None else int(self.data_length*0.2)

  def _compute_derivative(self):
    deriv = list()
    for (i, [timestamp, value]) in enumerate(self.data):
      if i < self.data_length-1:
        next_point = self.data[i+1]
        #compute derivative
        t1 = utils.parse_timestamp_str(timestamp)
        t2 = utils.parse_timestamp_str(next_point[0])
        v1 = value
        v2 = next_point[1]
        td = t2-t1
        td_seconds = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6
        df = (v2-v1)/td_seconds if td_seconds != 0 else v2-v1
        deriv.append(df)
      else:
        #the last point is assigned the same derivative as the second-last point
        deriv.append(deriv[-1])
    self.deriv = deriv

  def _compute_anom_score(self, dfs, df):
    abs_dfs = list()
    for i in dfs:
      abs_dfs.append(abs(i))
    stdev = statistics.stdev(abs_dfs)
    ema = utils.computer_ema(self.smoothing_factor, abs_dfs)[-1]
    return abs(abs(df)-ema)/stdev if stdev !=0 else abs(abs(df)-ema)

  def set_anom_data(self, csv_name=None):
    self._compute_derivative()
    anom_data = list()
    for (i, [timestamp, value]) in enumerate(self.data):
      if i == 0:
        continue
      if i < self.lag_window_size:
        entry = [timestamp, self._compute_anom_score(self.deriv[:i+1], self.deriv[i])]
      else:
        entry = [timestamp, self._compute_anom_score(self.deriv[i-self.lag_window_size:i+1], self.deriv[i])]
      anom_data.append(entry)
    self.anom_data = anom_data
    self.write_anom_data(STATIC_PATH+self.csv_name) if csv_name is None else self.write_anom_data(STATIC_PATH+csv_name)
    return self.get_anom_data_path()