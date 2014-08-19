#!/usr/bin/env python
# coding=utf-8
"""
© 2014 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from luminol import Luminol
from luminol.anomaly_detector import AnomalyDetector
from luminol.correlator import Correlator
import luminol.exceptions as exceptions
from luminol.modules.time_series import TimeSeries


class TestCorrelator(unittest.TestCase):

  def setUp(self):
    self.s1 = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0.5, 5: 1, 6: 1, 7: 1, 8: 0}
    self.s2 = {0: 0, 1: 0.5, 2: 1, 3: 1, 4: 1, 5: 0, 6: 0, 7: 0, 8: 0}
    self.s3 = {0: 0, 1: 0.5, 2: 1, 3: 1, 4: 1, 5: 0}
    self.correlator1 = Correlator(self.s1, self.s2)
    self.correlator2 = Correlator(self.s1, self.s3)

  def test_use_anomaly_score(self):
    """
    Test if use_anomaly_score works as expected.
    """
    correlator1 = Correlator(self.s1, self.s2, use_anomaly_score=True)
    self.assertNotEqual(self.correlator1.get_correlation_result().coefficient, correlator1.get_correlation_result().coefficient)

  def test_cross_correlation(self):
    """
    Test if CrossCorrelation algorithm gives same results as expected.
    """
    self.assertEqual(self.correlator1.get_correlation_result().coefficient, self.correlator2.get_correlation_result().coefficient)
    self.assertEqual(self.correlator1.get_correlation_result().shift, self.correlator2.get_correlation_result().shift)

  def test_if_correlate(self):
    """
    Test if function is_correlated gives same result as function get_correlation_result
    when there is a correlation.
    """
    self.assertEqual(True, self.correlator2.is_correlated() is not None)
    self.assertEqual(self.correlator2.get_correlation_result(), self.correlator2.is_correlated())

  def test_algorithm(self):
    """
    Test if optional parameter algorithm works as expected.
    """
    self.assertRaises(exceptions.AlgorithmNotFound, lambda: Correlator(self.s1, self.s2, algorithm_name='NotValidAlgorithm'))
    correlator = Correlator(self.s1, self.s2, algorithm_name='cross_correlator')
    self.assertEqual(self.correlator2.get_correlation_result().coefficient, correlator.get_correlation_result().coefficient)
    self.assertEqual(self.correlator2.get_correlation_result().shift, correlator.get_correlation_result().shift)

  def test_algorithm_params(self):
    """
    Test if optional parameter algorithm_params works as expected.
    """
    self.assertRaises(exceptions.InvalidDataFormat, lambda: Correlator(self.s1, self.s2, algorithm_name='cross_correlator', algorithm_params=1))
    correlator = Correlator(self.s1, self.s2, algorithm_name='cross_correlator', algorithm_params={'max_shift_seconds': 180})
    self.assertEqual(self.correlator2.get_correlation_result().coefficient, correlator.get_correlation_result().coefficient)

  def test_maximal_shift_seconds(self):
    """
    Test if parameter max_shift_seconds works as expected.
    """
    correlator = Correlator(self.s1, self.s2, algorithm_name='cross_correlator', algorithm_params={'max_shift_seconds': 0})
    self.assertNotEqual(self.correlator2.get_correlation_result().coefficient, correlator.get_correlation_result().coefficient)

  def test_sanity_check(self):
    """
    Test if exception NotEnoughDataPoints is raised as expected.
    """
    s4 = {0: 0}
    self.assertRaises(exceptions.NotEnoughDataPoints, lambda: Correlator(s4, self.s1))

  def test_time_series_format(self):
    """
    Test if exception InvalidDataFormat is raised as expected.
    """
    self.assertRaises(exceptions.InvalidDataFormat, lambda: Correlator(list(), 1))


class TestAnomalyDetector(unittest.TestCase):

  def setUp(self):
    self.s1 = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0.5, 5: 1, 6: 1, 7: 1, 8: 0}
    self.s2 = {0: 0, 1: 0.5, 2: 1, 3: 1, 4: 1, 5: 0, 6: 0, 7: 0, 8: 0}
    self.detector1 = AnomalyDetector(self.s1)
    self.detector2 = AnomalyDetector(self.s2)

  def test_threshold(self):
    detector = AnomalyDetector(self.s1, score_threshold=0)
    self.assertTrue(len(detector.get_anomalies()) == 1)
    self.assertTrue(detector.get_anomalies() is not None)

  def test_score_only(self):
    detector = AnomalyDetector(self.s1, score_only=True, algorithm_name='derivative_detector')
    detector2 = AnomalyDetector(self.s1, algorithm_name='derivative_detector')
    self.assertTrue(detector2.get_anomalies() is not None)
    self.assertTrue(detector.get_anomalies() is None)

  def test_get_all_scores(self):
    """
    Test if function get_all_scores works as expected.
    """
    self.assertTrue(isinstance(self.detector1.get_all_scores(), TimeSeries))
    self.assertEqual(len(self.detector1.get_all_scores()), len(self.detector1.time_series))

  def test_get_anomalies(self):
    """
    Test if anomaly is found as expected.
    """
    self.assertTrue(self.detector1.get_anomalies() is not None)

  def test_algorithm_DefaultDetector(self):
    """
    Test if optional parameter algorithm works as expected.
    """
    detector = AnomalyDetector(self.s1, algorithm_name='default_detector')
    self.assertEqual(detector.get_all_scores().timestamps, self.detector1.get_all_scores().timestamps)
    self.assertEqual(detector.get_all_scores().values, self.detector1.get_all_scores().values)

  def test_algorithm(self):
    """
    Test if exception AlgorithmNotFound is raised as expected.
    """
    self.assertRaises(exceptions.AlgorithmNotFound, lambda: AnomalyDetector(self.s1, algorithm_name='NotValidAlgorithm'))

  def test_algorithm_params(self):
    """
    Test if optional parameter algorithm_params works as expected.
    """
    self.assertRaises(exceptions.InvalidDataFormat, lambda: AnomalyDetector(self.s1, algorithm_name='exp_avg_detector', algorithm_params='0'))
    detector = AnomalyDetector(self.s1, algorithm_name="exp_avg_detector", algorithm_params={'smoothing_factor': 0.3})
    self.assertNotEqual(self.detector1.get_all_scores().values, detector.get_all_scores().values)

  def test_anomaly_threshold(self):
    """
    Test if score_percentile_threshold works as expected.
    """
    detector = AnomalyDetector(self.s1, score_percentile_threshold=0.1, algorithm_name='exp_avg_detector')
    detector1 = AnomalyDetector(self.s1, score_percentile_threshold=0.1, algorithm_name='derivative_detector')
    self.assertNotEqual(detector1.get_anomalies(), detector.get_anomalies())


class TestLuminol(unittest.TestCase):
  def setUp(self):
    self.anomaly = ['A', 'B']
    self.correlation = {
      'A': ['m1', 'm2', 'm3'],
      'B': ['m2', 'm1', 'm3']
    }
    self.luminol = Luminol(self.anomaly, self.correlation)

  def test_get_result(self):
    self.assertTrue(isinstance(self.luminol.get_root_causes(), dict))
    self.assertEqual(self.luminol.get_root_causes()['A'], 'm1')
    self.assertEqual(self.luminol.get_root_causes()['B'], 'm2')

if __name__ == '__main__':
  unittest.main()
