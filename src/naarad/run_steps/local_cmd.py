# coding=utf-8
"""
Copyright 2013 LinkedIn Corp. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import logging
import shlex
import subprocess
import time
from threading import Timer
from naarad.run_steps.run_step import Run_Step
import naarad.naarad_constants as CONSTANTS

logger = logging.getLogger('naarad.run_steps.local_cmd')


class Local_Cmd(Run_Step):
  """
  Class for a local command as run step.
  This type will be most likely used when running workload from the same machine running naarad
  """

  def __init__(self, run_type, run_cmd, call_type, run_order, run_rank, should_wait=True, kill_after_seconds=None):
    Run_Step.__init__(self, run_type, run_cmd, call_type, run_order, run_rank, should_wait, kill_after_seconds)
    self.process = None

  def run(self):
    """
    Run the command, infer time period to be used in metric analysis phase.
    :return: None
    """
    cmd_args = shlex.split(self.run_cmd)
    logger.info('Local command RUN-STEP starting with rank %d', self.run_rank)
    logger.info('Running subprocess command with following args: ' + str(cmd_args))

    # TODO: Add try catch blocks. Kill process on CTRL-C
    # Infer time period for analysis. Assume same timezone between client and servers.
    self.ts_start = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
      self.process = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
      if self.kill_after_seconds:
        self.timer = Timer(self.kill_after_seconds, self.kill)
        self.timer.start()
      # Using 2nd method here to stream output:
      # http://stackoverflow.com/questions/2715847/python-read-streaming-input-from-subprocess-communicate
      for line in iter(self.process.stdout.readline, b''):
        logger.info(line.strip())
      self.process.communicate()
    except KeyboardInterrupt:
      logger.warning('Handling keyboard interrupt (Ctrl-C)')
      self.kill()
    if self.timer:
      self.timer.cancel()
    self.ts_end = time.strftime("%Y-%m-%d %H:%M:%S")
    logger.info('subprocess finished')
    logger.info('run_step started at ' + self.ts_start + ' and ended at ' + self.ts_end)

  def kill(self):
    """
    If run_step needs to be killed, this method will be called
    :return: None
    """
    try:
      logger.info('Trying to terminating run_step...')
      self.process.terminate()
      time_waited_seconds = 0
      while self.process.poll() is None and time_waited_seconds < CONSTANTS.SECONDS_TO_KILL_AFTER_SIGTERM:
        time.sleep(0.5)
        time_waited_seconds += 0.5
      if self.process.poll() is None:
        self.process.kill()
        logger.warning('Waited %d seconds for run_step to terminate. Killing now....', CONSTANTS.SECONDS_TO_KILL_AFTER_SIGTERM)
    except OSError, e:
      logger.error('Error while trying to kill the subprocess: %s', e)
