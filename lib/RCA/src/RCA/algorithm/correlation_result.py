"""
Correlation object
"""

class CorrelationResult(object):
  def __init__(self, shift, coefficient):
    """
    construct a correlation object
    :param float coefficient: the correlation coefficient
    :param int shift: the amount of shift where the coefficient is given
    """
    self.shift = shift
    self.coefficient = coefficient