import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import utils
import settings


class Anomaly(object):
  def __init__(self, start_time, end_time, score, exact_time):
    """
    construct an anomaly object
    :param:start_time: start time of the anomaly period
    :param:end_time: end time of the anomaly period
    :param:score: the score of the anomaly
    :param:exact_time: the time point in the period where the anomaly likely happened
    """
    self.start_time = start_time
    self.end_time = end_time
    self.score = score
    self.exact_time = exact_time

  def get_time_window(self):
    """
    get handler for the time window
    :return list: a time window
    """
    return [self.start_time, self.end_time]

  def serialize(self):
    """
    serializer
    """
    return [self.start_time, self.end_time, self.score, self.exact_time]


class DetectorAlgo(object):
  """
  Base Class for detector algorithms
  """
  def __init__(self, name, data, baseline_data=None):
    """
    initializer
    """
    self.name = name
    self.data = data
    self.data_length = len(data)
    self.anom_scores = list()
    self.baseline_data = baseline_data
    self.anomlies = list()

  def run(self):
    """
    run the algorithm to get anomlies
    return list: a list of anomaly project
    """
    self.set_anom_scores()
    self.set_anomlies()
    return self.get_anomlies()

  def set_anom_scores(self):
    """
    function to compute anomaly score timeseries
    need to be extended
    """
    self.anom_scores = list()

  def get_anom_scores(self):
    """
    get handler for anom_scores
    :return list: a timeseries of anomaly scores
    """
    return self.anom_scores

  def set_anomlies(self):
    """
    function to compute anomlies from anomaly score timeseries
    current algorithm draws a threshold on the ten percent value
    """
    data = self.anom_scores
    itv = list()
    anomalies = list()
    start_t = None
    end_t = None
    v_max = max(utils.get_values(data))
    ten = v_max * 0.1
    for [t, v] in data:
      if v > ten:
        end_t = t
        if not start_t:
          start_t = t
      elif start_t and end_t:
        itv.append([start_t, end_t])
        start_t = None
        end_t = None
    if start_t:
      itv.append([start_t, end_t])
    for p in itv:
      d = utils.filter_data(data, p[0], p[1])
      e = ExpAvgDetector(d)
      e.set_anom_scores()
      scores = e.get_anom_scores()
      s_max = max(scores, key=lambda k: k[1])
      anomalies.append(Anomaly(p[0], p[1], s_max[1], s_max[0]))
    self.anomalies = anomalies

  def get_anomlies(self):
    """
    get handler for anomlies
    :return list: a list of anomly project
    """
    return self.anomalies


class ExpAvgDetector(DetectorAlgo):
  """
  METHOD 1: Exponential Moving Avgs
  this method uses a data point's deviation from the expoential moving avg of a lagging lag window
  to determine the anomaly score
  """
  def __init__(self, data, baseline_data=None, smoothing_factor=None, lag_window_size=None):
    """
    initializer
    :param float smoothing_factor: smoothing factor
    :param int lag_window_size: lag window size
    """
    super(ExpAvgDetector, self).__init__(self.__class__.__name__, data, baseline_data)
    self.smoothing_factor = smoothing_factor if smoothing_factor > 0 else settings.DEFAULT_EMA_SMOTHING_FACTOR
    self.lag_window_size = lag_window_size if lag_window_size else int(self.data_length * settings.DEFAULT_EMA_WINDOW_SIZE_PCT)

  def _compute_anom_score(self, lag_window_points, point):
    """
    compute anom score for a single point:point - ema(lag_window)
    :param float point: point value
    :param lag_window_points: values in lag window
    :return float: score
    """
    ema = utils.computer_ema(self.smoothing_factor, lag_window_points)[-1]
    return abs(point - ema)

  def _compute_anom_data_using_window(self):
    """
    compute anom scores using a sliding window
    :return list: the anomal score timeseries
    """
    anom_scores = list()
    points = utils.get_values(self.data)
    for i in range(1, self.data_length):
      point = points[i]
      if i < self.lag_window_size:
        entry = [self.data[i][0], self._compute_anom_score(points[:i + 1], point)]
      else:
        entry = [self.data[i][0], self._compute_anom_score(points[i - self.lag_window_size: i + 1], point)]
      anom_scores.append(entry)
    self.anom_scores = anom_scores

  def _compute_anom_data_decay_all(self):
    """
    compute anomaly scores as value(i) - ema(i)
    return list: the anomaly score timeseries
    """
    anom_scores = list()
    points = utils.get_values(self.data)
    ema = utils.computer_ema(self.smoothing_factor, points)
    for (i, [timestamp, value]) in enumerate(self.data):
      entry = [timestamp]
      score = abs(value - ema[i])
      entry.append(score)
      anom_scores.append(entry)
    self.anom_scores = anom_scores

  def set_anom_scores(self):
    self._compute_anom_data_decay_all()


class BitmapDetector(DetectorAlgo):
  """
  METHOD 2: Bitmap Detector
  this method breaks time series into chunks and use frequency of similar chuncks
  to determine anomaly and anomaly score
  """
  def __init__(self, data, baseline_data=None, precision=4, lag_window_size=None, future_window_size=None, chunk_size=None):
    """
    initializer
    :param precision: break into how many value ranges
    :param int lag_window_size: lag window size
    :param int future_window_size: future window size
    :param int chunk_size: how many points in a SAX pattern
    """
    super(BitmapDetector, self).__init__(self.__class__.__name__, data, baseline_data)
    self.precision = precision if precision and precision > 0 else 4
    self.lag_window_size = lag_window_size if lag_window_size else int(self.data_length * settings.DEFAULT_BITMAP_LAGGING_WINDOW_SIZE_PCT)
    self.chunk_size = chunk_size if chunk_size and chunk_size > 0 else settings.DEFAULT_BITMAP_CHUNK_SIZE
    self.future_window_size = future_window_size if future_window_size else int(self.data_length * settings.DEFAULT_BITMAP_LEADING_WINDOW_SIZE_PCT)
    self._sanity_check()

  def _sanity_check(self):
    """
    check if there is enough data points
    """
    windows = self.lag_window_size + self.future_window_size
    if not self.lag_window_size or not self.future_window_size or self.data_length < windows or windows < settings.DEFAULT_BITMAP_MINIMAL_POINTS_IN_WINDOWS:
      raise Exception("RCA.detector:Not Enough Data Points!")

  def _generate_SAX_single(self, sections, section_height, value):
    """
    generating SAX representation for a single data point
    :param list sections: value range sections
    :param float section_height: section height
    :param float value: value
    :return: a SAX representation
    """
    sax = 0
    for s in sections:
      if value >= sections[s]:
        sax = s
      else:
        break
    return sax

  def _generate_SAX(self):
    """
    generating SAX representation for the timeseries
    :return: SAX representation
    """
    sections = dict()
    sax = str()
    # set global min and global max
    points = utils.get_values(self.data)
    self.data_min = min(points)
    self.data_max = max(points)
    # break data value range into different sections
    section_height = (self.data_max - self.data_min) / self.precision
    for s in range(0, self.precision):
      sections[s] = self.data_min + s * section_height
    # generate SAX for each data point
    for entry in self.data:
      sax += str(self._generate_SAX_single(sections, section_height, entry[1]))
    self.sax = sax

  def _count_SAX(self, sax):
    """
    form a frequency dictionary from SAX representation
    :param string sax: the SAX representation
    :return: frequency dictionary
    """
    freq = dict()
    chunk_size = self.chunk_size
    s_len = len(sax)
    for i in range(0, s_len):
      if i + chunk_size < s_len:
        chunk = sax[i:i + chunk_size]
        freq = utils.auto_increment(freq, chunk)
    return freq

  def _compute_anom_score_between_two_windows(self, lag_window_points, future_window_points):
    """
    compute distance difference between two windows' frequency dicts
    :param list lag_window_points: lag window points
    :param list future_window_points: future_window_points
    :return: a distance score
    """
    lag_freq = self._count_SAX(lag_window_points)
    fut_freq = self._count_SAX(future_window_points)
    score = 0
    for i in lag_freq:
      if i in fut_freq:
        score += math.pow(fut_freq[i] - lag_freq[i], 2)
      else:
        score += math.pow(lag_freq[i], 2)
    for i in fut_freq:
      if i not in lag_freq:
        score += math.pow(fut_freq[i], 2)
    return score

  def set_anom_scores(self):
    """
    compute anom score using two sliding windows
    :return: anomaly score timeseries
    """
    chunk_size = self.chunk_size
    anom_scores = list()
    self._generate_SAX()
    for i in range(chunk_size + 1, len(self.sax)):
      if i < self.lag_window_size * 2:
        score = 0
      else:
        lag_window_points = self.sax[i - 2 * self.lag_window_size:i - self.lag_window_size]
        future_window_points = self.sax[i - self.lag_window_size:i + 1]
        score = self._compute_anom_score_between_two_windows(lag_window_points, future_window_points)
      anom_scores.append([self.data[i - self.lag_window_size][0], score])
    self.anom_scores = anom_scores


class DetrivativeDetector(DetectorAlgo):
  '''
  METHOD 3: Detrivative
  this method is the derivative version of METHOD 1
  '''
  def __init__(self, data, baseline_data=None, smoothing_factor=0.2, lag_window_size=None):
    """
    initializer
    :param float smoothing_factor: smoothing factor
    :param int lag_window_size: lag window size
    """
    super(DetrivativeDetector, self).__init__(self.__class__.__name__, data, baseline_data)
    self.smoothing_factor = smoothing_factor if smoothing_factor is not None else 0.2
    self.lag_window_size = lag_window_size if lag_window_size is not None else int(self.data_length * 0.2)

  def _compute_derivative(self):
    """
    compute derivatives of the timeseries
    """
    deriv = list()
    for (i, [timestamp, value]) in enumerate(self.data):
      if i > 0:
        pre_point = self.data[i - 1]
        # compute derivative
        t1 = utils.to_epoch(timestamp)
        t2 = utils.to_epoch(pre_point[0])
        v1 = value
        v2 = pre_point[1]
        td = t2 - t1
        td_seconds = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10 ** 6) / 10 ** 6
        df = (v2 - v1) / td_seconds if td_seconds != 0 else v2 - v1
        deriv.append(df)
      else:
        # the last point is assigned the same derivative as the second-last point
        deriv.append(deriv[-1])
    self.deriv = deriv

  def _compute_anom_score(self, dfs, df):
    """
    compute anom score of a single point: df(i) - ema_df(i)
    :param list dfs: a list of derivatives
    :param float df: df(i)
    :return: anom score(i)
    """
    abs_dfs = list()
    for i in dfs:
      abs_dfs.append(abs(i))
    ema = utils.computer_ema(self.smoothing_factor, abs_dfs)[-1]
    return abs(abs(df) - ema)

  def set_anom_scores(self):
    """
    compute anom scores for the timeseries
    """
    self._compute_derivative()
    anom_scores = list()
    for (i, [timestamp, value]) in enumerate(self.data):
      if i == 0:
        continue
      if i < self.lag_window_size:
        entry = [timestamp, self._compute_anom_score(self.deriv[:i + 1], self.deriv[i])]
      else:
        entry = [timestamp, self._compute_anom_score(self.deriv[i - self.lag_window_size:i + 1], self.deriv[i])]
      anom_scores.append(entry)
    self.anom_scores = anom_scores