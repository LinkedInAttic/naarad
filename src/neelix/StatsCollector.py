#!/usr/bin/python

import optparse
import os
import paramiko
import random
import sys
import threading
import time


verbose_mode=False
global_username=None
global_password=None
global_private_key=None

class RemoteCmdExeutor(threading.Thread):
  '''
  This helper function is called by all stats collection function and it does 3 things
   1) creates a new thread to establish a ssh connection
   2) run the command on the targeted host with output on the remote host
   3) write the collected data to a file locally.
   timeout - how long this command would take to finish, default 3
  '''
  def __init__(self, hostname, cmd, timeout=3, out_file=None, notes=""):
    '''
    :param string hostname: the remote host to connect to collect stats
    :param string cmd: the stat-collecting command to run on the remote host
    :param int timeout: how many seconds this thread will block and wait for your command
    :param string out_file: if given, the output of your command will be written to this file
    :param string notes: if given, this would be printed out in verbose mode ( for debugging )
    '''
    self.hostname = hostname
    self.cmd = cmd
    self.timeout = timeout
    self.out_file = out_file
    self.notes = notes
    threading.Thread.__init__(self)

  def run(self):
    '''
    The thread's run function to create ssh connection and execute the stat-collecting command remotely
    '''
    ssh = create_ssh_conn(self.hostname)
    if ssh:
      try:
        # Start executing the command
        channel = ssh.get_transport().open_session()
        channel.set_combine_stderr(True)
        print_if_verbose('Executing cmd on %s: %s' % (self.hostname, self.cmd))
        channel.exec_command(self.cmd)

        if self.out_file:
        # block and read the output from the cmd out of the buffer until it times out
          with open(self.out_file, 'wb+') as f:
            counter = 0
            while counter < 10 and not channel.recv_ready():
              time.sleep(1)
              counter += 1

            start_time = 0
            while start_time < self.timeout:
              if channel.recv_ready():
                l = channel.recv(102400)
                if len(l) == 0: #  If a string of length zero is returned, the channel stream has closed
                  break
                f.writelines(l)
              time.sleep(1)
              start_time += 1
        else:
          time.sleep(self.timeout)
      except paramiko.SSHException as e:
        print 'Failed to execute cmd %s on ssh channel with %s. ERROR MSG: %s' % (self.cmd, self.hostname, e.message)
      finally:
        status = channel.recv_exit_status()
        channel.close()
        ssh.close()
        print_if_verbose('RemoteCmdExeutor\'s thread %s on %s exits at %s' % (self.notes, self.hostname, time.strftime("%m/%d/%Y %H:%M:%S", time.gmtime())))
        if status > 0:
          print 'WARNING: A non-zero status returned for cmd: %s on %s. status=%s' % (self.cmd,self.hostname,str(status))
    else:
      print 'Failed to establish ssh connection.  Cmd "%s" not run on %s!' % (self.cmd, self.hostname)

def print_if_verbose(msg):
  '''
  Helper function to print only in verbose mode.
  :param string msg: message to print in verbose mode
  '''
  if verbose_mode:
    print msg

def get_user_name():
    return global_username or os.environment.get('USERS')

def create_ssh_conn(hostname, retry=True):
  '''
  Creates and returns a paramiko.SSHClient object.  Returns None if it failed.
  :param string hostname: the host that you want to ssh to
  :param bool retry: if True, if it fails to establish ssh due to any reason, it will retry
  '''
  ssh = paramiko.SSHClient()
  ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
  try:
    ssh.connect(hostname, username=global_username, password=global_password, key_filename=global_private_key)
  except paramiko.SSHException as e:
    print 'Failed to establish ssh connection to %s with paramiko\'s error: \'%s\'' % (hostname,e.message)
    if retry:
      print '[RETRYING...] ssh connection on %s ...' % hostname
      time.sleep(random.randint(2,6))
      ssh = create_ssh_conn(hostname, False)
    else:
      print '[RETRY FAILED] ssh connection to %s have failed!' % hostname
      ssh = None
  except:
    print 'Failed to establish ssh connection to %s! Unknown exception.' % hostname
    ssh = None
  return ssh

def kill_orphan_processes(hosts, is_sar, is_innotop, is_gc):
  '''
  If this is running but was aborted, the remotely started processes may still be running.
  This function will remotely kill them.  You can call this function before you start.
  :param string hosts: a list of hosts, comma-separated
  :param string is_sar: if True, check for sar process started by *user* and kill if found
  :param string is_innotop: if True, check for innotop process started by *user* and kill if found
  :param string is_gc: if True, check for tail -f gc process started by *user* and kill if found
  '''
  for host in hosts.split(','):
    if is_sar:
      kill_sar = RemoteCmdExeutor(host, 'killall sar -u %s' % get_user_name(), notes='Pre-command: kill sar')
      kill_sar.start()
    if is_innotop:
      kill_innotop = RemoteCmdExeutor(host, 'killall innotop -u %s' % get_user_name(), notes='Pre-command: kill innotop')
      kill_innotop.start()
    if is_gc:
      kill_gc_tail = RemoteCmdExeutor(host, 'killall tail -u %s' % get_user_name(), notes='Pre-command: kill tail -f')
      kill_gc_tail.start()
  time.sleep(5)


def start_sar(hosts, out_dir, count, interval):
  '''
  Function to start capturing SAR metrics, and it will also create the necessary directories if needed.
  :param string hosts: a list of hosts, comma-separated
  :param string out_dir: the output directory
  :param int count: how many times to poll for sar
  :param int interval: how many seconds to wait before polling again ( frequency of polling )
  '''
  duration = float(count) * float(interval)
  sar_cmds={'sar.paging.csv' : 'sar -B %s %s' % (interval, count),\
            'sar.device.csv' : 'sar -d -p %s %s' % (interval, count),\
            'sar.memory.csv' : 'sar -R %s %s' % (interval, count),\
            'sar.memutil.csv' : 'sar -r %s %s' % (interval, count),\
            'sar.cpuusage.csv' : 'sar -u ALL %s %s' % (interval, count),\
            'sar.swapping.csv' : 'sar -W %s %s' % (interval, count),\
            'sar.csw.csv' : 'sar -w %s %s' % (interval, count)\
  }
  for host in hosts.split(','):
    cur_out_dir=os.path.join(out_dir, host, 'SAR')
    if not os.path.exists(cur_out_dir):
      os.makedirs(cur_out_dir)
    for out_file_name, cmd in sar_cmds.iteritems():
      executor = RemoteCmdExeutor(host, cmd, duration, os.path.join(cur_out_dir, out_file_name), out_file_name)
      executor.start()
    print_if_verbose('Done spawning SARs ALL cmd threads on %s. The threads will complete in %s seconds' % (host,str(duration)))


def start_innotop(hosts, out_dir, count, interval, db_user, db_pwd, sock):
  '''
  Function to start capturing MYSQL data through Innotop.
  Prerequisite" Innotop must be installed.
  :param string hosts: a list of hosts, comma-separated
  :param string out_dir: the output directory
  :param int count: how many times to poll for sar
  :param int interval: how many seconds to wait before polling again ( frequency of polling )
  :param string db_user: db user login name
  :param string db_pwd: db user password
  :param string sock: the mysql sock which innotop will try to connect
  '''
  duration = float(count) * float(interval)
  # construct the commands to call
  db_cmd_str='innotop -u%s -p%s -S %s -n --delay %s --count %s --timestamp --timestamp' % (db_user, db_pwd, sock, interval, count)
  db_cmds={'buffer.out' : '%s --mode B' % (db_cmd_str) ,\
           'command.out' : '%s --mode C' % (db_cmd_str),\
           'iostat.out' : '%s --mode I' % (db_cmd_str),\
           'replication.out' : '%s --mode M' %(db_cmd_str),\
           'record.out' : '%s --mode R' %(db_cmd_str)\
  }
  for host in hosts.split(','):
    cur_out_dir=os.path.join(out_dir, host, 'INNOTOP')
    if not os.path.exists(cur_out_dir):
      os.makedirs(cur_out_dir)
    for out_file_name, cmd in db_cmds.iteritems():
      executor = RemoteCmdExeutor(host, cmd, duration, os.path.join(cur_out_dir, out_file_name), out_file_name)
      executor.start()
    print_if_verbose('Done spawning ALL innotop cmd threads on %s. The threads will complete in %s seconds' % (host,str(duration)) )


def start_gc_capture(hosts, out_dir, gc_tail_duration, gc_file_path):
  '''
  Function to start capturing GC log given the file path and duration in second
  :param string hosts: a list of hosts, comma-separated
  :param string out_dir: the output directory
  :param int gc_tail_duration: how many seconds of capturing the gc log
  :param string gc_file_path: the gc log's file path
  '''
  gc_tail_cmd='tail -f %s' % (gc_file_path)
  kill_gc_tail_cmd='sleep %s; kill $( ps -ef | grep %s | grep "tail -f %s" | grep -v grep | awk \'{ print $2 }\' )'\
                   % (gc_tail_duration, get_user_name(), gc_file_path)
  for host in hosts.split(','):
    cur_out_dir=os.path.join(out_dir, host, 'GC')
    if not os.path.exists(cur_out_dir):
      os.makedirs(cur_out_dir)
    #Start calling the tail -f on gc log
    executor = RemoteCmdExeutor(host, gc_tail_cmd, gc_tail_duration, os.path.join(cur_out_dir,'gc.log'), 'tail -f')
    executor.start()
    #Start another cmd that sleep "gc_tail_duration" seconds, then kill tail -f
    executor = RemoteCmdExeutor(host, kill_gc_tail_cmd, gc_tail_duration, notes='kill tail -f')
    executor.start()
    print_if_verbose('Done spawning ALL gc tail threads on %s. The threads will complete in %s seconds' % (host,str(gc_tail_duration)) )


def main():
  parser=optparse.OptionParser()
  parser.add_option('-l', '--list', dest="hostnames", help="REQUIRED: List of servers, space separated")
  parser.add_option('-o', '--outdir', dest="outdir", help="REQUIRED: Output directory to place the captured logs")
  parser.add_option('-u', '--user', dest="user", default=None, help="OPTIONAL: User name")
  parser.add_option('-p', '--pwd', dest="pwd", default=None, help="OPTIONAL: User name")
  parser.add_option('-k', '--key', dest="key", default=None, help="OPTIONAL: Auth key to use for authentication")
  parser.add_option('-s', '--sar', action="store_true", dest="sar", help="OPTIONAL: Collect SAR stats ( CPU %, Memory, Disk IO )")
  parser.add_option('-g', '--gc', dest="gc", help="OPTIONAL: Path to gc file on the remote host")
  parser.add_option('--gcduration', dest="gc_duration", help="REQUIRED if -g is used, how many seconds of capturing gc log")
  parser.add_option('-d', '--db', action="store_true", dest="db", help="OPTIONAL: Collect DB INNOTOP stats")
  parser.add_option('--dbuser', dest="dbuser", default=None, help="REQUIRED if -d is used, db username.")
  parser.add_option('--dbpwd', dest="dbpwd", default=None, help="REQUIRED if -d is used, db password")
  parser.add_option('--sock', dest="sock", default=None, help="REQUIRED if -d is used, db socket to connect")
  parser.add_option('-c', '--count', dest="count", default=5, help="OPTIONAL: How many times to poll")
  parser.add_option('-i', '--interval', dest="interval", default=1, help="OPTIONAL: How frequent to poll")
  parser.add_option('-t', '--test', action="store_true", dest="test", help="FOR WAI TESTING ONLY! Pls remove!)")
  parser.add_option('-v', '--verbose', action="store_true", dest="verbose", help="If True, very verbose")
  parser.add_option('--preclean', action="store_true", dest="preclean", help="If True, it will kill existing orphan processes on remote hosts")
  (options, args) = parser.parse_args()
  global verbose_mode
  verbose_mode = options.verbose
  global global_username
  global_username = options.user
  global global_password
  global_password = options.pwd
  global global_private_key
  global_private_key = options.key
  # Check for input arguments
  if not options.hostnames or not options.outdir:
    print 'ERROR: Missing required arguments! Both -h and -o are required.'
    parser.print_help()
    sys.exit()
  if not options.sar and not options.gc and not options.db:
    print 'Doing nothing! you should specify at least one of -s, -g or -d to collect some perf data.'
    parser.print_help()
    sys.exit()
  if options.preclean:
    kill_orphan_processes(options.hostnames, options.sar, options.db, options.gc)
  print_if_verbose('INFO: hostnames=%s, outdir=%s, user=%s, sar=%s gc=%s db=%s count=%s interval=%s' % \
           (options.hostnames, options.outdir, options.user, options.sar, options.gc, options.db, options.count, options.interval))
  print_if_verbose(time.strftime("%m/%d/%Y %H:%M:%S", time.gmtime()))
  # start kicking off remote commands
  if options.sar:
    print 'Starting remote SAR collections count=%s, interval=%s' % (options.count, options.interval)
    start_sar(options.hostnames, options.outdir, options.count, options.interval)
  if options.db:
    if options.dbuser and options.dbpwd and options.sock:
      print 'Starting remote Innotop collections count=%s, interval=%s' % (options.count, options.interval)
      start_innotop(options.hostnames, options.outdir, options.count, options.interval, options.dbuser, options.dbpwd, options.sock)
    else:
      print 'Missing required arguments for -d!  You entered -d for db stats, please specify required --db_user, --db_pwd and --sock'
  if options.gc:
    if options.gc_duration:
      print 'Starting GC tail at %s for seconds' % options.gc_duration
      start_gc_capture(options.hostnames, options.outdir, options.gc_duration, options.gc)
    else:
      duration = float(options.interval) * float( options.count)
      print 'Starting GC tail at %s for %s seconds' % (options.gc, duration)
      start_gc_capture(options.hostnames, options.outdir, duration, options.gc)
    # wait for all the collection threads to finish
  print_if_verbose('Done starting all threads.  Waiting for them to finish.')

# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == '__main__':
  main()
