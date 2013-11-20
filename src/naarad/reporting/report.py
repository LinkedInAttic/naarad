# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0
 
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
import logging
from jinja2 import Template, Environment, PackageLoader, FileSystemLoader


logger = logging.getLogger('naarad.reporting.Report')

class Report(object):

  def __init__(self, report_name, output_directory, metric_list, **other_options):
    if report_name == '':
      self.report_name = 'naarad analysis report'
    else:
      self.report_name = report_name
    self.output_directory = output_directory
    self.metric_list = metric_list
    if other_options:
      for (key, val) in other_options.iteritems():
        setattr(self, key, val)

  def generate(self):
    templateLoader = FileSystemLoader('/home/sgandhi/workspace/naarad/templates')
    templateEnv = Environment( loader=templateLoader )
    templates = {
      'header': templateEnv.get_template('default_report_header.html'),
      'summary': templateEnv.get_template('default_summary_page.html'),
      'metric': templateEnv.get_template('default_metric_page.html'),
      'footer': templateEnv.get_template('default_report_footer.html')
    }
    html = reduce(dict.__getitem__, ['summary'], templates).render()

    logger.info(html)
