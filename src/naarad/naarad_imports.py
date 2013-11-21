# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0
 
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""

from naarad.graphing import matplotlib_naarad
from naarad.metrics.jmeter_metric import JmeterMetric
from naarad.reporting.report import Report

#Custom metrics
metric_classes = {
    #'MyMetric' : MyMetricParserClass
    'JMETER' : JmeterMetric
    }
graphing_modules = {
    'matplotlib' : matplotlib_naarad
    }
reporting_modules = {
    'report' : Report
}
