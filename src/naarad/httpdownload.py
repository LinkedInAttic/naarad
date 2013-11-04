#!/usr/bin/python
import os
import re
import urllib2

def download_single_url(url, outdir, outfile=None):
  """
  Base function, which takes a single url, download it to outdir/outfile
  """	
  #if outfile is not given, extract the filename from url
  if not outfile :
    segs = url.split('/')
    outfile = segs[-1]
    
  #check if the outfile exists
  output_file = os.path.join(outdir, outfile)
  if os.path.exists(output_file):
	print "the %s already exists!" % outfile
	return
  
  #download and write to the file
  with open(output_file, "w") as fh:
    response = urllib2.urlopen(url)
    fh.write(response.read())


def get_urls_from_seed(url):
  """
  get a list of urls from a seeding url, return a list of urls 
  """
  if type(url) != str:
    print "get_urls_from_seed() does not have valid seeding url."
    return   

  #extract the basic host: "http://host:port/" 
  base_index = url.find('/', len("https://"))   # get the first "/" after http://"
  base_url = url[:base_index]  #base_url = "http://host:port"
    
  urls=[]
  link_pattern = "a href=" 
  response = urllib2.urlopen(url)  
  lines = response.read().split('<')    

  for line in lines:
    line_tmp = line.lower()  # to handle letter case 
    if link_pattern in line_tmp:     
      start = len(link_pattern) +1  # the trailing "
      end = line.find('>', start)
      if end > start : 
        link = line[start:end - 1]
        urls.append(base_url + link)    

  return urls
  
  
def download(input, outdir, outfile=None):
  """ this function downloads http(s) urls to a local files
  Input: 
  - input // Required. can be in the format of: 
  (1) a single absolute url:  "http://host/path/file"
  (2) a list of absolute urls as ["http://host1/path1/file1", "http://host2/path2/file2"]
  (3) a list of str, which consists of a flag of "regex", a seeding url (for listing all available files) and zero or more regex str ["regex", "http://host/path/", "2013-*.log"].  
      If no regex str is given, then all urls will be downloaded. 

  Output: 
  - outdir // Required. the local directory to put the downloadedfiles.  
  - outfile // Optional. If this is given, the downloaded url will be renated to outfile; If this is not given, then the local file will be the original one, as given in url. 
    outfile can be (1) a single name; (2) a list of names
  """
  
  #create the outdir if necessary
  if not os.path.exists(outdir):
    os.makedirs(outdir)	

  #extract from input.  
  # If it is a regix call, then regexs[] will have the regex str, while seed_url will have the seeding url
  # If a regular call, then regex[] will be empty
  urls=[] 
  regexs =[]
  seed_url=None  				#seed url for regex call. Is None if it is regular call.
  
  if type(input) == str:  		# a single absolute url
    urls.append(input)
  elif type(input) == list and len(input) > 0 and input[0].lower() != "regex":  # input is a regular list
    urls = input
  elif type(input) == list and len(input) > 1 and input[0].lower() == "regex":  # input is a regex list
    seed_url = input[1]  		# stores the seeding url
    if len(input) == 2: 		# no regex str is given, then assuming ".*'
      regexs.append('.*')
    else: 
      regexs = input[2:] 
  else:
    logging.info("input format of %s is wrong. " % input)
    return

  #extract from outfile.  If outfile is not given, then outfiles will be None. Otherwise, not None
  outfiles=[] 
  if type(outfile) == str:     	# just a single url 
    outfiles.append(outfile)
  else:      					# a list of outfile
    outfiles=outfile    
    
  # if outfile is given, then check the length of input/output
  if outfile :       
    if len(outfiles) != len(urls):
      print "The number of urls (%s) and number of output files (%s) do notmatch." % input, outfile
      return	  
  
  # process regular call and regex call
  if  not seed_url:          	# regular call
    for i in range(len(urls)):
      if outfiles:   			# outfiles is given
        download_single_url(urls[i], outdir, outfiles[i])
      else:
        download_single_url(urls[i], outdir)        
  else:    						# regex call
    files = get_urls_from_seed(seed_url)
    for file in files:	 	
      for regex_rule in regexs: # in case of multiple regexes  
        if re.compile(regex_rule).match(file):			  
          download_single_url(file, outdir)  
