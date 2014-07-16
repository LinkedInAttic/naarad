"""
Settings to use for RCA
"""

"""
Detector Settings
"""
# indicate which algorithms to use to calculate anomality scores
# all the algorithm codes are in algorithm.algorithms
# this settings are kept so later if there are better algorithms, they can be easily subsitituted.
DETECTOR_ALGORITHM = 'BitmapDetector'

# Default percentile threshold value on anomaly score above which is considered an anomaly.
DEFAULT_SCORE_PERCENTILE_THRESHOLD = 0.1

# some defaults parameters for the currently algorithms

# window sizes as percents of the whole data length
# advice to have a small leading window size
DEFAULT_BITMAP_LEADING_WINDOW_SIZE_PCT = 0.2 / 16

DEFAULT_BITMAP_LAGGING_WINDOW_SIZE_PCT = 0.2 / 16

DEFAULT_BITMAP_MINIMAL_POINTS_IN_WINDOWS = 50

# how large is the chunk
# data points form chunks and frequencies of similar chunks are
# used to determine anomaly scores
DEFAULT_BITMAP_CHUNK_SIZE = 2

# how slow the data points delay
# a smaller factor gives a faster decay rate
DEFAULT_EMA_SMOTHING_FACTOR = 0.2

DEFAULT_EMA_WINDOW_SIZE_PCT = 0.2

"""
Correlator Settings
"""
# since anomalies take time to propagate between two different
# timeseries, similar irregularities may happen close but not
# exactly at the same point in time.
# To take this into account, when correlates, we allow a "shift room"
# of the timeseries
DEFAULT_ALLOWED_SHIFT_SECONDS = 180

# The threshold such that >= which is considered "correlated"
DEFAULT_CORRELATE_THRESHOLD = 0.7

CORRELATOR_ALGORITHM = 'CrossCorrelation'