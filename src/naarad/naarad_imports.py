# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""

from naarad.metrics.linkedin_android_rum_metric import LinkedInAndroidRumMetric
from naarad.metrics.gc_metric import GCMetric
from naarad.metrics.innotop_metric import INNOMetric
from naarad.metrics.jmeter_metric import JmeterMetric
from naarad.metrics.procvmstat_metric import ProcVmstatMetric
from naarad.metrics.procmeminfo_metric import ProcMeminfoMetric
from naarad.metrics.proczoneinfo_metric import ProcZoneinfoMetric
from naarad.metrics.sar_metric import SARMetric
from naarad.reporting.report import Report
from naarad.metrics.cluster_metric import ClusterMetric
from naarad.metrics.netstat_metric import NetstatMetric

#Custom metrics
metric_classes = {
    #'MyMetric' : MyMetricParserClass
    'GC' : GCMetric,
    'INNOTOP' : INNOMetric,
    'JMETER' : JmeterMetric,
    'LINKEDINANDROIDRUM' : LinkedInAndroidRumMetric,
    'PROCVMSTAT' : ProcVmstatMetric,
    'PROCMEMINFO' : ProcMeminfoMetric, 
    'PROCZONEINFO' : ProcZoneinfoMetric,
    'SAR' : SARMetric, 
    'NETSTAT' : NetstatMetric
    }

#Custom metrics;  aggregate_metric can only processed after regular metrics are done
aggregate_metric_classes = {    
    'CLUSTER' : ClusterMetric,
    }    

graphing_modules = {}
try:
  from naarad.graphing import matplotlib_naarad
except ImportError:
  pass
else:
  graphing_modules['matplotlib'] = matplotlib_naarad

try:
  from naarad.graphing import pygal_naarad
except ImportError:
  pass
else:
  graphing_modules['svg'] = pygal_naarad

reporting_modules = {
    'report': Report
}
