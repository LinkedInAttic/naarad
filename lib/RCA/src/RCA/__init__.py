"""
API for Root Cause Analyzer Module
"""


class RCA(object):
  def __init__():
    """
    initializer
    """

  def analyze(matrix, related_matrixes):
    """
    analyze if matrix has anomaly.
    if anomaly is found, determine if it correlates with any of related_metrixes
    :param list matrix: main timeseries of interest
    :param list related_metrixes: a list of related timeseries data
    :return: (bool if_anomly, list correlated_matrixes)
    """