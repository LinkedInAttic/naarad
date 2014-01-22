# coding=utf-8
"""
© 2014 LinkedIn Corp. All rights reserved.

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
"""
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

from module import Module
from perf_imports import Global
import utility

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("config", help="Please provide a config file")
  args = parser.parse_args()
  config_file = args.config

  # create all perf modules
  utility.create_modules(config_file)
  
  #Peoridical invoking all modules and create threads;   
  do_loop = True
  while do_loop:
    # perform log rolling
    utility.check_logdir()
    utility.log_rolling()  
    
    # create threads for each enabled module and run them
    utility.invoke_modules()
    
    #wait for all threads to complete for this period
    for t in Global.threads: 
      t.join()   
    
    # debugging only; it should run forever  
    #do_loop = False
