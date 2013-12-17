# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0
 
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
import logging
import os
import shutil
import glob
import naarad.utils
from jinja2 import Template, Environment, PackageLoader, FileSystemLoader

logger = logging.getLogger('naarad.reporting.Report')

class Report(object):

  def __init__(self, report_name, output_directory, metric_list, correlated_plots,  **other_options):
    self.report_templates = {
      'header': 'default_report_header.html',
      'summary': 'default_summary_page.html',
      'summary_content': 'default_summary_content.html',
      'metric': 'default_metric_page.html',
      'footer': 'default_report_footer.html',
      'client_charting': 'default_client_charting_page.html'
    }
    if report_name == '':
      self.report_name = 'naarad analysis report'
    else:
      self.report_name = report_name
    self.output_directory = output_directory
    self.metric_list = metric_list
    self.correlated_plots = correlated_plots
    self.stylesheet_includes = []
    self.javascript_includes = ['sorttable.js', 'dygraph-combined.js']
    if other_options:
      for (key, val) in other_options.iteritems():
        setattr(self, key, val)
      if 'header_template' in other_options:
        self.report_templates['header'] = self.header_template
      if 'footer_template' in other_options:
        self.report_templates['footer'] = self.footer_template
      if 'metric_template' in other_options:
        self.report_templates['metric'] = self.metric_template
      if 'summary_template' in other_options:
        self.report_templates['summary'] = self.summary_template
      if 'summary_content_template' in other_options:
        self.report_templates['summary_content'] = self.summary_template

  def copy_local_includes(self):
    resource_folder = self.get_resources_location()
    for stylesheet in self.stylesheet_includes:
      if ('http' not in stylesheet) and naarad.utils.is_valid_file(os.path.join(resource_folder,stylesheet)):
        shutil.copy(os.path.join(resource_folder,stylesheet),self.output_directory)
    for javascript in self.javascript_includes:
      if ('http' not in javascript) and naarad.utils.is_valid_file(os.path.join(resource_folder,javascript)):
        shutil.copy(os.path.join(resource_folder,javascript), self.output_directory)
    return None


  def get_summary_table(self, summary_stats_file):
    summary_stats = []
    with open(summary_stats_file,'r') as stats_file:
      header = stats_file.readline().rstrip().rsplit(',')
      summary_stats.append(header)
      for line in stats_file:
        summary_stats.append(line.rstrip().rsplit(','))
    return summary_stats

  def is_correlated_image(self, image):
    if os.path.basename(image) in self.correlated_plots:
      return True
    else:
      return False

  def validate_file_list(self, files_list):
    for file_name in files_list:
      if naarad.utils.is_valid_file(file_name):
        return True
    return False

  def enable_summary_tab(self):
    for metric in self.metric_list:
      for stats_file in metric.important_stats_files:
        if naarad.utils.is_valid_file(stats_file):
          return True
    if self.validate_file_list(self.correlated_plots):
        return True
    else:
        return False

  def generate_summary_page(self, template_environment, summary_html_content, coplot_html_content):
    summary_html = template_environment.get_template(self.report_templates['header']).render(custom_stylesheet_includes=self.stylesheet_includes, custom_javascript_includes=self.javascript_includes) + '\n'
    summary_html += template_environment.get_template(self.report_templates['summary']).render(metric_list=sorted(self.metric_list), summary_html_content=summary_html_content, correlated_plot_content=coplot_html_content) + '\n'
    summary_html += template_environment.get_template(self.report_templates['footer']).render()
    return summary_html

  def strip_file_extension(self, file_name):
    filename = file_name.split('.')
    return '.'.join(filename[0:-1])

  def generate_client_charting_page(self, template_environment, data_csv_list, summary_enabled):
    client_charting_html = template_environment.get_template(self.report_templates['header']).render(custom_stylesheet_includes=self.stylesheet_includes, custom_javascript_includes=self.javascript_includes) + '\n'
    client_charting_html += template_environment.get_template(self.report_templates['client_charting']).render(metric_list=sorted(self.metric_list),metric_data=sorted(data_csv_list),summary_enabled=summary_enabled) + '\n'
#    client_charting_html += template_environment.get_template(self.report_templates['footer']).render()
    return client_charting_html

  def get_resources_location(self):
    return os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'resources'))

  def generate(self):
    template_loader = FileSystemLoader(self.get_resources_location())
    self.copy_local_includes()
    template_environment = Environment(loader=template_loader)
    summary_html_content = ''
    coplot_html_content = ''
    metric_html = ''
    summary_enabled = self.enable_summary_tab()
    client_charting_data = []

    for metric in self.metric_list:
      client_charting_data.extend(map(self.strip_file_extension,map(os.path.basename,metric.csv_files)))
      div_html = ''
      for plot_div in sorted(metric.plot_files):
        with open(plot_div,'r') as div_file:
            div_html += '\n' + div_file.read()

      for summary_stats_file in metric.important_stats_files:
        if naarad.utils.is_valid_file(summary_stats_file):
          summary_stats = self.get_summary_table(summary_stats_file)
          summary_html_content += template_environment.get_template(self.report_templates['summary_content']).render(metric_stats=summary_stats, metric=metric) + '\n'

      for metric_stats_file in metric.stats_files:
        if naarad.utils.is_valid_file(metric_stats_file) or len(metric.plot_files) > 0:
          metric_stats = self.get_summary_table(metric_stats_file)
          metric_html = template_environment.get_template(self.report_templates['header']).render(custom_stylesheet_includes=self.stylesheet_includes, custom_javascript_includes=self.javascript_includes)
          metric_html += template_environment.get_template(self.report_templates['metric']).render(metric_stats=metric_stats, plot_div_content=div_html, metric=metric.label, metric_list=sorted(self.metric_list), summary_enabled=summary_enabled)
          metric_html += template_environment.get_template(self.report_templates['footer']).render()
      if metric_html != '':
        with open(os.path.join(self.output_directory, metric.label + '_report.html'), 'w') as metric_report:
          metric_report.write(metric_html)

    for coplot in self.correlated_plots:
      with open(coplot,'r') as coplot_file:
        coplot_html_content += coplot_file.read()

    if summary_enabled:
      with open(os.path.join(self.output_directory, 'summary_report.html'),'w') as summary_report:
        summary_report.write(self.generate_summary_page(template_environment, summary_html_content, coplot_html_content))

    with open(os.path.join(self.output_directory, 'client_charting.html'),'w') as client_charting_report:
      client_charting_report.write(self.generate_client_charting_page(template_environment, client_charting_data, summary_enabled))

    return True
