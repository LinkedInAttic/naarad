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

from luminol.algorithms.anomaly_detector_algorithms import *
from luminol.algorithms.correlator_algorithms import *

anomaly_detector_algorithms = {
  'bitmap_detector': bitmap_detector.BitmapDetector,
  'derivative_detector': derivative_detector.DerivativeDetector,
  'exp_avg_detector': exp_avg_detector.ExpAvgDetector
}

correlator_algorithms = {
  'cross_correlator':cross_correlator.CrossCorrelator
}
