import argparse
import ConfigParser
import datetime
import errno
import logging
import os
import re
import sys
import threading
import time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))

from perf_imports import Global
from module import Module

def create_modules(config_file):
  """
  read all modules from config file
  """
  print 'using config file: ', config_file
  if not os.path.exists(config_file):
    sys.exit("ERROR: Config file " + config_file + " doesn't exist")
  
  variables_dict = {}
  config_obj = ConfigParser.ConfigParser(variables_dict)
  config_obj.read(config_file)
  
  for section in config_obj.sections():
    # handling [GLOBAL] section    
    if section == 'GLOBAL':
      if config_obj.has_option(section,'directory'):
        Global.DIRECTORY = config_obj.get(section,'directory')
      if config_obj.has_option(section,'keep_days'):
        Global.KEEP_DAYS = config_obj.get(section,'keep_days')
      if config_obj.has_option(section,'period'):
        Global.PERIOD = config_obj.get(section,'period')      
      if config_obj.has_option(section,'interval'):
        Global.INTERVAL = config_obj.get(section,'interval')    
      continue      
     
    # regular sections    
    if config_obj.has_option(section, 'name'):
      cur_name = config_obj.get(section, 'name')
    else:
      cur_name = section
      
    if config_obj.has_option(section, 'command'):
      cur_command = config_obj.get(section, 'command')
    else:
      sys.exit("Error: " + section + ' does not have COMMAND param')
      
    if config_obj.has_option(section, 'interval'):
      cur_interval = config_obj.get(section, 'interval')
    else: 
      cur_interval = Global.INTERVAL
      
    if config_obj.has_option(section, 'out_file'):
      cur_out_file= config_obj.get(section, 'out_file')
    else:
      sys.exit("Error: " + section + ' does not have out_file param')
      
    if config_obj.has_option(section, 'isOn'):
      cur_isOn = config_obj.get(section, 'isOn')
    else:
      cur_isOn = True
            
    module = Module(cur_name, cur_command, cur_interval, cur_out_file, cur_isOn)
    Global.modules.append(module) 

def runThis(module):
  """
  Invoked in the begining of each period
  One thread per module;  
  Replace the following $INTERVAL $COUNT $DIRECTORY $FILE 
  """
  cur_interval = str(module.interval)
  cur_count =  int(Global.PERIOD) / int(module.interval)
  cur_count = str(cur_count)
  str_today = time.strftime("%Y-%m-%d")  
  cur_directory = os.path.join(Global.DIRECTORY, Global.SUBDIR_PREFIX + str_today)
  cur_file = module.out_file

  cur_command = module.command.replace('$INTERVAL', cur_interval)
  cur_command = cur_command.replace('$COUNT', cur_count)
  cur_command = cur_command.replace('$DIRECTORY', cur_directory)
  cur_command = cur_command.replace('$FILE',cur_file)
  
  #print module.name, ' is running: ', cur_command
  os.system(cur_command)  
    
def invoke_modules():  
  """
  For each module, create a thread; 
  Then loop every interval seconds, till the end of the day; 
  """
  Global.threads = []     
  for module in Global.modules:
    #only consider enabled modules
    if module.isOn:
      thread = threading.Thread(target=runThis, args=(module,))
      thread.start()
      Global.threads.append(thread)
    
  #print 'created # threads = ', len(Global.threads)
  
def check_logdir():
  """
  create a new sub_directory if current date is not there;    
  """  
  str_today = time.strftime("%Y-%m-%d")  
  cur_directory = os.path.join(Global.DIRECTORY, Global.SUBDIR_PREFIX + str_today)
  
  if not os.path.exists(cur_directory):
    # readable by others
    os.makedirs(cur_directory, 0755)
    

def log_rolling():
  """
  check the time/date, to remove expired logs and create new ones.   
  """  
  # check each directory, if directory is older than KEEP_DAYS, remove them. 
  sub_dirs = os.listdir(Global.DIRECTORY)
  for sub_dir in sub_dirs:
    if sub_dir.startswith(Global.SUBDIR_PREFIX):  #perf result sub dir
      cur_date = datetime.date.today() 
      
      # get the year-month-day
      fields = sub_dir.split('-')
      size = len(fields)
      dir_date = datetime.date(int(fields[size-3]), int(fields[size-2]), int(fields[size-1]))
      diff = cur_date - dir_date
      
      #print ' current checking dir is: ' +os.path.join(Global.DIRECTORY, sub_dir)
      if diff.days > int(Global.KEEP_DAYS) and sub_dir.startswith(Global.SUBDIR_PREFIX): 
        #need to remove the sub-dir 
        os.system('rm -r -f '+ os.path.join(Global.DIRECTORY, sub_dir) )       
  

