import os
import sys
import re
import urllib2
import logging
from HTMLParser import HTMLParser

import naarad.utils as utils

logger = logging.getLogger('naarad.utils')
                  
                       
def download_single_url(url, outdir, outfile=None):
  """
  Base function which takes a single url, download it to outdir/outfile
  
  :param str url: a full/absolute url, e.g. http://www.cnn.com/log.zip
  :param str outdir: the absolute local directory. e.g. /home/user1/tmp/
  :param str outfile: (optional) filename stored in local directory
  :return: None
  """
  
  if not utils.is_valid_url(url):
    logger.info("download_single_url() does not have valid url.")
    return
    
  #if outfile is not given, extract the filename from url
  if not outfile :
    segs = url.split('/')
    outfile = segs[-1]
    
  #check if the outfile exists
  output_file = os.path.join(outdir, outfile)
  if os.path.exists(output_file):
	logger.info("the %s already exists!" % outfile)
  
  #download and write to the file
  with open(output_file, "w") as fh:
    response = urllib2.urlopen(url)
    fh.write(response.read())


# to parse the html file, and extract href links into self.links[]
class MyHTMLParser(HTMLParser):  
  def __init__(self):  
    HTMLParser.__init__(self)  
    self.flag = 0  
    self.links = []  
    self.title=""  
    self.img=""  
    self.content=""  
   
  def handle_starttag(self, tag, attrs):  
    if tag == "a":  
      if len(attrs) == 0: pass  
      else:  
        for (variable, value)  in attrs:  
          if variable == "href":  
            self.links.append(value)  
 
 
def get_urls_from_seed(url):
  """
  get a list of urls from a seeding url, return a list of urls 
  
  :param str url: a full/absolute url, e.g. http://www.cnn.com/logs/
  :return: a list of full/absolute urls. 
  """	
  
  if type(url) != str or not utils.is_valid_url(url):
    logger.info("get_urls_from_seed() does not have valid seeding url.")
    return   

  #extract the host info of "http://host:port/". If href urls are relative urls (e.g., /path/gc.log), then join to form the complete url
  base_index = url.find('/', len("https://"))   # get the first "/" after http://" or "https://"; handling both cases.   
  base_url = url[:base_index]  #base_url = "http://host:port" or https://host:port" or http://host" (where no port is given)
  
  #extract the "href" denoted urls
  urls=[]
  response = urllib2.urlopen(url)  
  hp=MyHTMLParser() 
  hp.feed(response.read()) 
  urls = hp.links
  hp.close()  

  # check whether the url is relative or complete
  for i in range(len(urls)):
    if urls[i].find("http") != 0:
      urls[i] = base_url + urls[i] 
 
  return urls
  
  
def download(inputs, outdir, outfile = None, isRegex = False):
  """ 
  Downloads http(s) urls to a local files
 :param list inputs: 
  (1) a list of absolute urls as ["http://host1/path1/file1", "http://host2/path2/file2"]
  (2) a list of str, which consists of a seeding url (for listing all available files) and zero, 1 or multiple regex str 
      For instance, ["http://host/path/", "2013-*.log"].  
      If no regex str is given, then all urls will be downloaded. 
  :param str outdir: Required. the local directory to put the downloadedfiles.  
  :param str outfile: // Optional. If this is given, the downloaded url will be renated to outfile; 
    If this is not given, then the local file will be the original one, as given in url. 
    outfile can be (1) a single name; (2) a list of names
  :param bool isRegex:  // optional. Indicates whether the call is regex or not. 
  :return None
  """
  
  if not outdir: 
    logging.info("outdir is not given. ")
    return
    
  #create the outdir if necessary
  if not os.path.exists(outdir):
    os.makedirs(outdir)	

  #extract from input.  
  # If it is a regix call, then regexs[] will have the regex str, while seed_url will have the seeding url
  # If a regular call, then regex[] will be empty
  urls=[] 
  regexs =[]
  seed_url =None 

  if type(inputs) != list or len(inputs) < 1:
    logging.info("inputs is not valid.")
    return 
    
  if not isRegex:
    urls = inputs
  else: 
    seed_url = inputs[0]  		# stores the seeding url
    if len(inputs) == 1: 		# no regex str is given, then assuming ".*'
      regexs.append('.*') 
    elif len(inputs) > 1: 		# regex str is given. 
      regexs = inputs[1:] 

   
  # if outfile is given, then check the length of input/output
  if outfile :       
    if len(outfile) != len(urls):
      logging.info("The number of urls (%s) and number of output files (%s) do notmatch." % inputs, outfile)
      return	  
  
  # process regular call and regex call
  if  not isRegex:          	# regular call
    for i in range(len(urls)):
      if outfile:   			# outfiles is given
        download_single_url(urls[i], outdir, outfile[i])
      else:
        download_single_url(urls[i], outdir)        
  else:    						# regex call
    files = get_urls_from_seed(seed_url)
    for f in files:	 	
      print f; 
      for regex_rule in regexs: # in case of multiple regexes  
        if re.compile(regex_rule).match(f):			  
          download_single_url(f, outdir)  

if __name__ == "__main__":
  url = "http://www.google..com/index.html"
  print utils.is_valid_url(url)
  download_single_url(url, ".")
