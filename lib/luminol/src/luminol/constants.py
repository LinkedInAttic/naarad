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
"""
Constants to use for luminol
"""

"""
Detector Constants
"""
# Indicate which algorithm to use to calculate anomaly scores.
ANOMALY_DETECTOR_ALGORITHM = 'bitmap_detector'

# Indicate which algorithm to use to get refined maximal score within each anomaly.
ANOMALY_DETECTOR_REFINE_ALGORITHM = 'exp_avg_detector'

# Default percentile threshold value on anomaly score above which is considered an anomaly.
DEFAULT_SCORE_PERCENTILE_THRESHOLD = 0.1

# Constants for BitmapDetector.
# Window sizes as percentiles of the whole data length.
DEFAULT_BITMAP_LEADING_WINDOW_SIZE_PCT = 0.2 / 16

DEFAULT_BITMAP_LAGGING_WINDOW_SIZE_PCT = 0.2 / 16

DEFAULT_BITMAP_MINIMAL_POINTS_IN_WINDOWS = 50

# Chunk size.
# Data points form chunks and frequencies of similar chunks are used to determine anomaly scores.
DEFAULT_BITMAP_CHUNK_SIZE = 2

DEFAULT_BITMAP_PRECISION = 4

# Constants for ExpAvgDetector.
DEFAULT_EMA_SMOTHING_FACTOR = 0.2

DEFAULT_EMA_WINDOW_SIZE_PCT = 0.2

"""
Correlator Constants
"""
CORRELATOR_ALGORITHM = 'cross_correlator'

# Since anomalies take time to propagate between two different timeseries,
# similar irregularities may happen close in time but not exactly at the same point in time.
# To take this into account, when correlates, we allow a "shift room".
DEFAULT_ALLOWED_SHIFT_SECONDS = 180

# The threshold above which is considered "correlated".
DEFAULT_CORRELATE_THRESHOLD = 0.7
