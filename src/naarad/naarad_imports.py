# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""

def import_modules(modules_dict, is_class_type=True):
  return_dict = {}
  for module_name, module_string in modules_dict.items():
    try:
      if is_class_type:
        file_name, class_name = module_string.rsplit('.', 1)
        mod = __import__(file_name, fromlist=[class_name])
        return_dict[module_name] = getattr(mod, class_name)
      else:
        return_dict[module_name] = __import__(module_string, fromlist=[module_string])
    except ImportError:
      pass
  return return_dict

metric_imports_dict = {
  'GC' : 'naarad.metrics.gc_metric.GCMetric',
  'INNOTOP' : 'naarad.metrics.innotop_metric.INNOMetric',
  'JMETER' : 'naarad.metrics.jmeter_metric.JmeterMetric',
  'LINKEDINANDROIDRUM' : 'naarad.metrics.linkedin_android_rum_metric.LinkedInAndroidRumMetric',
  'PROCVMSTAT' : 'naarad.metrics.procvmstat_metric.ProcVmstatMetric',
  'PROCMEMINFO' : 'naarad.metrics.procmeminfo_metric.ProcMeminfoMetric',
  'PROCZONEINFO' : 'naarad.metrics.proczoneinfo_metric.ProcZoneinfoMetric',
  'PROCINTERRUPTS' : 'naarad.metrics.procinterrupts_metric.ProcInterruptsMetric',
  'SAR' : 'naarad.metrics.sar_metric.SARMetric',
  'TOP' : 'naarad.metrics.top_metric.TopMetric',
  'NETSTAT' : 'naarad.metrics.netstat_metric.NetstatMetric'
}

graphing_imports_dict = {
  'matplotlib':'naarad.graphing.matplotlib_naarad',
  'svg':'naarad.graphing.pygal_naarad'
}

aggregate_metric_imports_dict = {
  'CLUSTER': 'naarad.metrics.cluster_metric.ClusterMetric'
}

reporting_imports_dict = {
  'report' : 'naarad.reporting.report.Report'
}

metric_classes = import_modules(metric_imports_dict)

graphing_modules = import_modules(graphing_imports_dict, is_class_type=False)

aggregate_metric_classes = import_modules(aggregate_metric_imports_dict)

reporting_modules = import_modules(reporting_imports_dict)
