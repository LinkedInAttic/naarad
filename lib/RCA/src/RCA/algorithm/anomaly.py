"""
Anomaly Object
"""

class Anomaly(object):
  def __init__(self, start_timestamp, end_timestamp, anomaly_score, exact_timestamp):
    """
    Construct an anomaly object.
    :param:start_timestamp: start time of the anomaly period
    :param:end_timestamp: end time of the anomaly period
    :param:anomly_score: the score of the anomaly
    :param:exact_timestamp: the time point in the period where the anomaly likely happened
    """
    self.start_timestamp = start_timestamp
    self.end_timestamp = end_timestamp
    self.anomaly_score = anomaly_score
    self.exact_timestamp = exact_timestamp

  def get_time_window(self):
    """
    get handler for the time window
    :return list: a time window
    """
    return self.start_timestamp, self.end_timestamp