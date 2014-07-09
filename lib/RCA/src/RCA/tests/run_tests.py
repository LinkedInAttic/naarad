import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from correlator import *

class TestCorrelator(unittest.TestCase):

	def setUp(self):
		self.s1 = [[0, 0], [1, 0], [2, 0], [3, 0], [4, 0.5], [5, 1], [6, 1], [7, 1], [8, 0]]
		self.s2 = [[0, 0], [1, 0.5], [2, 1], [3, 1], [4, 1], [5, 0], [6, 0], [7, 0], [8, 0]]
		self.s3 = self.s2[:6]

	def test_cross_correlation(self):
		self.assertEqual(cross_correlate(self.s1, self.s2), cross_correlate(self.s1, self.s3))

	def test_correlation(self):
		self.assertEqual(correlate(self.s1, self.s2), cross_correlate(self.s1, self.s2)['max'][1])

	def test_if_correlate(self):
		self.assertEqual(True, if_correlate(self.s1,self.s3))

	def test_sanity_check(self):
		self.assertRaises(Exception, sanity_check, (list(), [1]))

if __name__ == '__main__':
	unittest.main()