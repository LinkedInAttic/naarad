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


class Luminol(object):
  def __init__(self, anomalies, correlations):
    """
    Initializer
    :param list anomalies: a list of anomalies.
    :param dict correlations: a dict represents correlated metrics to each anomaly.
    """
    self.anomalies = anomalies
    self.correlations = correlations
    self._analyze_root_causes()

  # Need to be modified.
  def _analyze_root_causes(self):
    """
    Conduct root cause analysis.
    """
    causes = dict()
    for a in self.anomalies:
      causes[a] = self.correlations[a][0]
    self.causes = causes

  def get_root_causes(self):
    """
    Get root causes.
    :return dict: a dict represents root causes for each anomaly.
    """
    return getattr(self, 'causes', None)