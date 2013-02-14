import os
import sys

#from neelix.ingraphs_metric import IngraphsMetric
#from neelix.graphing import jfreechart
from neelix.graphing import matplotlib_neelix

#Custom metrics
metric_classes = {
    #'INGRAPHS' : IngraphsMetric
    }
graphing_modules = {
    #'jfreechart' : jfreechart
    'matplotlib' : matplotlib_neelix
    }
