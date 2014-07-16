import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from RCA.correlator import Correlator

class TestCorrelator(unittest.TestCase):

  def setUp(self):
    self.s1 = [[0, 0], [1, 0], [2, 0], [3, 0], [4, 0.5], [5, 1], [6, 1], [7, 1], [8, 0]]
    self.s2 = [[0, 0], [1, 0.5], [2, 1], [3, 1], [4, 1], [5, 0], [6, 0], [7, 0], [8, 0]]
    self.s3 = self.s2[:6]
    self.correlator1 = Correlator(self.s1, self.s2)
    self.correlator2 = Correlator(self.s1, self.s3)

  def test_cross_correlation(self):
    self.assertEqual(self.correlator1.get_correlation_result().coefficient, self.correlator2.get_correlation_result().coefficient)

  def test_if_correlate(self):
    self.assertEqual(True, self.correlator2.is_correlated() is not None)

  def test_sanity_check(self):
    self.assertRaises(Exception, self.correlator1._sanity_check, (list(), [1]))

if __name__ == '__main__':
  unittest.main()