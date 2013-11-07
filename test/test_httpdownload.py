import os
import nose  
import sys

# add the path of ~/naarad/src;   the testing py is under ~/naarad/test 
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')))

import naarad.httpdownload as httpdownload
 
def test_list_of_urls_no_output():
  ''' list of abosulute urls with no output file name'''
  url = "http://localhost/naarad/1.html"
  outdir ="."

  if os.path.exists(os.path.join(outdir, "1.html")):
    os.remove(os.path.join(outdir, "1.html"));  
  
  httpdownload.download_url_single(url, outdir)
  
  output_file = "1.html"
  assert os.path.exists(os.path.join(outdir, output_file)),  "File of %s does not exist! " % output_file  
  
  if os.path.exists(os.path.join(outdir, "1.html")):
    os.remove(os.path.join(outdir, "1.html"));  
    

def test_list_of_urls_with_output():
  ''' list of abosulute urls with output file name given'''
  url = "http://localhost/naarad/1.html"
  outfile = "1a.html"
  outdir ="." 
  
  if os.path.exists(os.path.join(outdir, "1a.html")):
    os.remove(os.path.join(outdir, "1a.html"));  
      
  httpdownload.download_url_single(url, outdir, outfile)

  output_file = "1a.html"
  assert os.path.exists(os.path.join(outdir, output_file)),  "File of %s does not exist! " % output_file  
       
  if os.path.exists(os.path.join(outdir, "1a.html")):
    os.remove(os.path.join(outdir, "1a.html"));  
  
      
def test_regex_urls():
  '''a seeding url, and a regex expression of urls '''
  seed_url = "http://localhost/naarad/a.html"
  outdir = "." 
  regex = ".*.html"
  
  if os.path.exists(os.path.join(outdir, "1.html")):
    os.remove(os.path.join(outdir, "1.html"));  
  if os.path.exists(os.path.join(outdir, "2.html")):
    os.remove(os.path.join(outdir, "2.html"));    
  
  httpdownload.download_url_regex(seed_url, outdir, None, regex)
  
  output_file = "1.html"
  assert os.path.exists(os.path.join(outdir, output_file)),  "File of %s does not exist! " % output_file  
  output_file = "2.html"
  assert os.path.exists(os.path.join(outdir, output_file)),  "File of %s does not exist! " % output_file
  
  if os.path.exists(os.path.join(outdir, "1.html")):
    os.remove(os.path.join(outdir, "1.html"));  
  if os.path.exists(os.path.join(outdir, "2.html")):
    os.remove(os.path.join(outdir, "2.html"));    
