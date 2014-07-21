"""
Exception Classes
"""


class AlgorithmNotFound(Exception):
  """
  Raise when algorithm can not be found.
  """
  pass


class InvalidDataFormat(Exception):
  """
  Raise when data has invalid format.
  """
  pass


class NotEnoughDataPoints(Exception):
  """
  Raise when there are not enough data points.
  """
  pass