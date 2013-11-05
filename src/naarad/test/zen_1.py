import os                  
import re  
import sys
import urllib

# add the path of ~/naarad/src/naarad;   the testing py is under ~/naarad/src/naarad/test 
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import httpdownload
  
       
if __name__ == "__main__":  
    httpdownload.get_urls_from_seed("http://localhost/naarad/a.html")
