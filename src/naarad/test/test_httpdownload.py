import os
import nose  
import sys

# add the path of ~/naarad/src/naarad;   the testing py is under ~/naarad/src/naarad/test 
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import httpdownload
 
def test_list_of_urls_no_output():
  ''' list of abus urls'''
  url = ["http://localhost/naarad/1.html", "http://localhost/naarad/2.html"]
  outdir ="."

  if os.path.exists(os.path.join(outdir, "1.html")):
    os.remove(os.path.join(outdir, "1.html"));  
  if os.path.exists(os.path.join(outdir, "2.html")):
    os.remove(os.path.join(outdir, "2.html"));     
  
  httpdownload.download(url, outdir)
  
  output_file = "1.html"
  assert os.path.exists(os.path.join(outdir, output_file)),  "File of %s does not exist! " % output_file  
  output_file = "2.html"
  assert os.path.exists(os.path.join(outdir, output_file)),  "File of %s does not exist! " % output_file
    

def test_list_of_urls_with_output():
  ''' list of abus urls'''
  url = ["http://localhost/naarad/1.html", "http://localhost/naarad/2.html"]
  outfile = ["1a.html", "2a.html"]
  outdir ="." 
  
  if os.path.exists(os.path.join(outdir, "1a.html")):
    os.remove(os.path.join(outdir, "1a.html"));  
  if os.path.exists(os.path.join(outdir, "2a.html")):
    os.remove(os.path.join(outdir, "2a.html"));    
      
  httpdownload.download(url, outdir, outfile)

  output_file = "1a.html"
  assert os.path.exists(os.path.join(outdir, output_file)),  "File of %s does not exist! " % output_file  
  output_file = "2a.html"
  assert os.path.exists(os.path.join(outdir, output_file)),  "File of %s does not exist! " % output_file
       
def test_regex_urls():
  '''a seeding url, and a regex expression of urls '''
  seed_url = "http://localhost/naarad/a.html"
  outdir ="." 
    #regex
  inputs =[]
  inputs.append(seed_url)
  inputs.append(".*.html")
  
  if os.path.exists(os.path.join(outdir, "1.html")):
    os.remove(os.path.join(outdir, "1.html"));  
  if os.path.exists(os.path.join(outdir, "2.html")):
    os.remove(os.path.join(outdir, "2.html"));    
  
  httpdownload.download(inputs, outdir, None, True)
  
  output_file = "1.html"
  assert os.path.exists(os.path.join(outdir, output_file)),  "File of %s does not exist! " % output_file  
  output_file = "2.html"
  assert os.path.exists(os.path.join(outdir, output_file)),  "File of %s does not exist! " % output_file
  
  
