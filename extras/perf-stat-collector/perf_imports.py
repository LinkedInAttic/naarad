
# log path; all logs will be under the same path such as:  logs_2014_01_01; 
# passed in from config file; 
# each sub_directory will have a bunch of text files, corresponding to each module
# # log history

class Global(object):  
  DIRECTORY = '/tmp'   
  PERIOD = 450
  INTERVAL = 2
 
  KEEP_DAYS = 8  
  
  # the sub directory will be 'perf-results-2014-01-02'
  SUBDIR_PREFIX='perf-results-'  
  
  # contains all modules, read from config_file
  config_file = ''    # config file
  modules = []
  threads = []  # each module is a thread to run ; 
  
