"""
Correlation object
"""


class CorrelationResult(object):
  def __init__(self, shift, coefficient):
    """
    Construct a CorrelationResult object.
    :param int shift: the amount of shift where the coefficient is obtained.
    :param float coefficient: the correlation coefficient.
    """
    self.shift = shift
    self.coefficient = coefficient