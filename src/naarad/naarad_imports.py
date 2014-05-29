# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""

from naarad.reporting.report import Report
from naarad.metrics.cluster_metric import ClusterMetric

metric_classes = {}
metric_imports_dict = {
  'GC' : 'naarad.metrics.gc_metric.GCMetric',
  'INNOTOP' : 'naarad.metrics.innotop_metric.INNOMetric',
  'JMETER' : 'naarad.metrics.jmeter_metric.JmeterMetric',
  'LINKEDINANDROIDRUM' : 'naarad.metrics.linkedin_android_rum_metric.LinkedInAndroidRumMetric',
  'PROCVMSTAT' : 'naarad.metrics.procvmstat_metric.ProcVmstatMetric',
  'PROCMEMINFO' : 'naarad.metrics.procmeminfo_metric.ProcMeminfoMetric',
  'PROCZONEINFO' : 'naarad.metrics.proczoneinfo_metric.ProcZoneinfoMetric',
  'SAR' : 'naarad.metrics.sar_metric.SARMetric',
  'NETSTAT' : 'naarad.metrics.netstat_metric.NetstatMetric'
}

for metric_name in metric_imports_dict.keys():
  try:
    file_name, class_name = metric_imports_dict[metric_name].rsplit('.', 1)
    mod = __import__(file_name, fromlist=[class_name])
    metric_classes[metric_name] = getattr(mod, class_name)
  except ImportError:
    pass

graphing_modules = {}
graphing_imports_dict = {
  'matplotlib':'naarad.graphing.matplotlib_naarad',
  'svg':'naarad.graphing.pygal_naarad'
}

for graphing_module_name in graphing_imports_dict.keys():
  try:
    graphing_modules[graphing_module_name] = __import__(graphing_imports_dict[graphing_module_name], globals(), locals(), [graphing_module_name], -1)
  except ImportError:
    pass

aggregate_metric_classes = {
  'CLUSTER' : ClusterMetric,
}

reporting_modules = {
  'report': Report
}
