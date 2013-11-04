import os
import nose  
import httpdownload

def test_single_abs_url_yes_outfile():
  ''' single abus url with outfile'''
  # change the date of the url to make it valid. 
  url = "http://eat1-app118.stg.linkedin.com:10475/logs/abook.log.2013-11-03.gz"
  outfile = "tmp1.gz"
  
  #check if the outfile exists
  outdir = "."
  output_file = os.path.join(outdir, outfile)
  assert not os.path.exists(output_file),  "File of %s exists! " % output_file
  httpdownload.download(url, outdir, outfile)
  assert os.path.exists(output_file),  "File of %s not downloaded! " % output_file

def test_single_abs_url_no_outfile():
  ''' single abus url with outfile'''
  url = "http://eat1-app118.stg.linkedin.com:10475/logs/abook.log.2013-11-03.gz"
  outdir = "."
  
  end_index = url.rfind("/"); 
  outfile = url[end_index+1:]
  output_file = os.path.join(outdir, outfile)
  
  #check if the outfile exists
  assert not os.path.exists(output_file),  "File of %s exists! " % output_file
  httpdownload.download(url, outdir)
  assert os.path.exists(output_file),  "File not downloaded! "
  
def test_list_of_urls():
  ''' list of abus urls'''
  url = ["http://eat1-app118.stg.linkedin.com:10475/logs/abook.log.2013-11-03.gz", "http://eat1-app118.stg.linkedin.com:10475/logs/abook.log.2013-11-02.gz"]
  outfile = ["url1.gz", "url2.gz"]
  
  outdir ="."
  #check if the outfile exists
  for i in range(len(url)):
    output_file = os.path.join(outdir, outfile[i])
    assert not os.path.exists(output_file),  "File of %s exists! " % output_file
    
  httpdownload.download(url, outdir, outfile)
  for i in range(len(url)):
    output_file = os.path.join(outdir, outfile[i])
    assert os.path.exists(output_file),  "File of %s not downloaded! " % output_file

def test_regex_urls():
  '''a seeding url, and a regex expression of urls '''
  seed_url = "http://eat1-app118.stg.linkedin.com:10475/logs/"
  
    #regex
  inputs =[]
  inputs.append("regex")
  inputs.append(seed_url)
  inputs.append(".*abook.out.13-08-.*")
  
  httpdownload.download(inputs, ".")
  
  

  
  
