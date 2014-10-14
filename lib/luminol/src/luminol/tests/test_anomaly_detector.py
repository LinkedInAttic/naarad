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

from luminol import exceptions
from luminol import Luminol
from luminol.anomaly_detector import AnomalyDetector
from luminol.correlator import Correlator
from luminol.modules.time_series import TimeSeries

class TestAnomalyDetector(unittest.TestCase):

  def setUp(self):
    self.s1 = {0: 0, 1: 0, 2: 0, 3: 0, 4: 1, 5: 2, 6: 2, 7: 2, 8: 0}
    self.s2 = {0: 0, 1: 1, 2: 2, 3: 2, 4: 2, 5: 0, 6: 0, 7: 0, 8: 0}
    self.detector1 = AnomalyDetector(self.s1)
    self.detector2 = AnomalyDetector(self.s2)

  def test_diff_percent_threshold_algorithm(self):
    """
    Test "diff percent threshold" algorithm with a threshold of 20%
    """
    detector = AnomalyDetector(self.s1, baseline_time_series=self.s2, algorithm_name='diff_percent_threshold',
                               algorithm_params={'percent_threshold_upper': 20, 'percent_threshold_lower': -20})
    anomalies = detector.get_anomalies()
    self.assertTrue(anomalies is not None)
    self.assertTrue(len(anomalies) > 0)
    print ';'.join(str(anomaly) for anomaly in anomalies)
    print detector.get_all_scores()
    print self.s1
    print self.s2

  def test_absolute_threshold_algorithm(self):
    """
    Test "absolute threshold" algorithm with a threshold of 0.2
    """
    detector = AnomalyDetector(self.s1, algorithm_name='absolute_threshold',
                               algorithm_params={'absolute_threshold_value': 0.2})
    anomalies = detector.get_anomalies()
    self.assertTrue(anomalies is not None)
    self.assertTrue(len(anomalies) > 0)

  def test_threshold(self):
    """
    Test score threshold=0
    """
    detector = AnomalyDetector(self.s1, score_threshold=0)
    self.assertTrue(len(detector.get_anomalies()) == 1)
    self.assertTrue(detector.get_anomalies() is not None)

  def test_score_only(self):
    """
    Test that score_only parameter doesn't give anomalies
    """
    detector = AnomalyDetector(self.s1, score_only=True, algorithm_name='derivative_detector')
    detector2 = AnomalyDetector(self.s1, algorithm_name='derivative_detector')
    self.assertTrue(detector2.get_anomalies() is not None)
    self.assertTrue(len(detector.get_anomalies()) == 0)

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
    self.assertRaises(ValueError, lambda: AnomalyDetector(self.s1, algorithm_name='exp_avg_detector', algorithm_params='0'))
    detector = AnomalyDetector(self.s1, algorithm_name="exp_avg_detector", algorithm_params={'smoothing_factor': 0.3})
    self.assertNotEqual(self.detector1.get_all_scores().values, detector.get_all_scores().values)

  def test_anomaly_threshold(self):
    """
    Test if score_percentile_threshold works as expected.
    """
    detector = AnomalyDetector(self.s1, score_percent_threshold=0.1, algorithm_name='exp_avg_detector')
    detector1 = AnomalyDetector(self.s1, score_percent_threshold=0.1, algorithm_name='derivative_detector')
    self.assertNotEqual(detector1.get_anomalies(), detector.get_anomalies())

if __name__ == '__main__':
  unittest.main()
