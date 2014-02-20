# coding=utf-8
"""
© 2013 LinkedIn Corp. All rights reserved.
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0
 
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
from jinja2 import Environment, FileSystemLoader
import logging
import os
import shutil
import naarad.utils
import naarad.naarad_constants as CONSTANTS
import naarad.resources


logger = logging.getLogger('naarad.reporting.Report')

class Report(object):

  def __init__(self, report_name, output_directory, resource_directory, resource_path, metric_list, correlated_plots,  **other_options):
    if report_name == '':
      self.report_name = CONSTANTS.DEFAULT_REPORT_TITLE
    else:
      self.report_name = report_name
    self.output_directory = output_directory
    self.resource_directory = resource_directory
    self.resource_path = resource_path
    self.metric_list = metric_list
    self.correlated_plots = correlated_plots
    self.stylesheet_includes = CONSTANTS.STYLESHEET_INCLUDES
    self.javascript_includes = CONSTANTS.JAVASCRIPT_INCLUDES
    if other_options:
      for (key, val) in other_options.iteritems():
        setattr(self, key, val)


  def copy_local_includes(self):
    resource_folder = self.get_resources_location()
    for stylesheet in self.stylesheet_includes:
      if ('http' not in stylesheet) and naarad.utils.is_valid_file(os.path.join(resource_folder,stylesheet)):
        shutil.copy(os.path.join(resource_folder,stylesheet),self.resource_directory)

    for javascript in self.javascript_includes:
      if ('http' not in javascript) and naarad.utils.is_valid_file(os.path.join(resource_folder,javascript)):
        shutil.copy(os.path.join(resource_folder,javascript), self.resource_directory)

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
    summary_html = template_environment.get_template(CONSTANTS.TEMPLATE_HEADER).render(custom_stylesheet_includes=CONSTANTS.STYLESHEET_INCLUDES, custom_javascript_includes=CONSTANTS.JAVASCRIPT_INCLUDES, resource_path=self.resource_path) + '\n'
    summary_html += template_environment.get_template(CONSTANTS.TEMPLATE_SUMMARY_PAGE).render(metric_list=sorted(self.metric_list), summary_html_content=summary_html_content, correlated_plot_content=coplot_html_content) + '\n'
    summary_html += template_environment.get_template(CONSTANTS.TEMPLATE_FOOTER).render()
    return summary_html

  def strip_file_extension(self, file_name):
    filename = file_name.split('.')
    return '.'.join(filename[0:-1])

  def generate_client_charting_page(self, template_environment, data_csv_list, summary_enabled):
    client_charting_html = template_environment.get_template(CONSTANTS.TEMPLATE_HEADER).render(custom_stylesheet_includes=CONSTANTS.STYLESHEET_INCLUDES, custom_javascript_includes=CONSTANTS.JAVASCRIPT_INCLUDES, resource_path=self.resource_path) + '\n'
    client_charting_html += template_environment.get_template(CONSTANTS.TEMPLATE_CLIENT_CHARTING).render(metric_list=sorted(self.metric_list),metric_data=sorted(data_csv_list),summary_enabled=summary_enabled, resource_path=self.resource_path) + '\n'
    with open(os.path.join(self.resource_directory,CONSTANTS.PLOTS_CSV_LIST_FILE),'w') as FH:
      FH.write(','.join(sorted(data_csv_list)))
    return client_charting_html

  def get_resources_location(self):
    return naarad.resources.get_dir()

  def generate(self):
    template_loader = FileSystemLoader(self.get_resources_location())
    self.copy_local_includes()
    template_environment = Environment(loader=template_loader)
    summary_html_content = ''
    coplot_html_content = ''
    metric_html = ''
    summary_enabled = self.enable_summary_tab()
    client_charting_data = []
    stats_files = []
    metric_html = ''

    for metric in self.metric_list:
      client_charting_data.extend(map(self.strip_file_extension,map(os.path.basename,metric.csv_files)))
      div_html = ''
      for plot_div in sorted(metric.plot_files):
        with open(plot_div,'r') as div_file:
            div_html += '\n' + div_file.read()

      for summary_stats_file in metric.important_stats_files:
        if naarad.utils.is_valid_file(summary_stats_file):
          summary_stats = self.get_summary_table(summary_stats_file)
          summary_html_content += template_environment.get_template(CONSTANTS.TEMPLATE_SUMMARY_CONTENT).render(metric_stats=summary_stats, metric=metric) + '\n'

      for metric_stats_file in metric.stats_files:
        if naarad.utils.is_valid_file(metric_stats_file) or len(metric.plot_files) > 0:
          stats_files.append(os.path.basename(metric_stats_file))
          metric_stats = self.get_summary_table(metric_stats_file)
          metric_html = template_environment.get_template(CONSTANTS.TEMPLATE_HEADER).render(custom_stylesheet_includes=CONSTANTS.STYLESHEET_INCLUDES, custom_javascript_includes=CONSTANTS.JAVASCRIPT_INCLUDES, resource_path=self.resource_path)
          metric_html += template_environment.get_template(CONSTANTS.TEMPLATE_METRIC_PAGE).render(metric_stats=metric_stats, plot_div_content=div_html, metric=metric, metric_list=sorted(self.metric_list), summary_enabled=summary_enabled)
          metric_html += template_environment.get_template(CONSTANTS.TEMPLATE_FOOTER).render()
      if metric_html != '':
        with open(os.path.join(self.output_directory, metric.label + CONSTANTS.METRIC_REPORT_SUFFIX), 'w') as metric_report:
          metric_report.write(metric_html)

    for coplot in self.correlated_plots:
      with open(coplot,'r') as coplot_file:
        coplot_html_content += coplot_file.read()

    if summary_enabled:
      with open(os.path.join(self.output_directory, CONSTANTS.SUMMARY_REPORT_FILE),'w') as summary_report:
        summary_report.write(self.generate_summary_page(template_environment, summary_html_content, coplot_html_content))

    with open(os.path.join(self.output_directory, CONSTANTS.CLIENT_CHARTING_FILE),'w') as client_charting_report:
      client_charting_report.write(self.generate_client_charting_page(template_environment, client_charting_data, summary_enabled))

    if len(stats_files) > 0 :
      with open(os.path.join(self.resource_directory,CONSTANTS.STATS_CSV_LIST_FILE),'w') as stats_file:
        stats_file.write(','.join(stats_files))

    return True
