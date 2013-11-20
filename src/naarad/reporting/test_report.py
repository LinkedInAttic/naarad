from naarad.reporting.report import Report
import logging

logger = logging.getLogger('naarad')


def init_logging(log_level):
  log_file = 'test_matplotlib.log'
  # clear the log file
  with open(log_file, 'w'):
    pass
  numeric_level = getattr(logging, log_level.upper(), None) if log_level else logging.INFO
  if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % log_level)
  logger.setLevel(logging.DEBUG)
  fh = logging.FileHandler(log_file)
  fh.setLevel(logging.DEBUG)
  ch = logging.StreamHandler()
  ch.setLevel(numeric_level)
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  fh.setFormatter(formatter)
  ch.setFormatter(formatter)
  logger.addHandler(fh)
  logger.addHandler(ch)

def main():
  init_logging('INFO')
  rpt = Report(report_name = 'test report', output_directory = '/tmp', metric_list = None )
  rpt.generate()
main()
