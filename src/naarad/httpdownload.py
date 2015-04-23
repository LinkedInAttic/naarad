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

import os
import sys
import re
import urllib2
import logging
from HTMLParser import HTMLParser

import naarad.utils

logger = logging.getLogger('naarad.httpdownload')


def handle_single_url(url, outdir, outfile=None):
  """
  Base function which takes a single url, download it to outdir/outfile
  :param str url: a full/absolute url, e.g. http://www.cnn.com/log.zip
  :param str outdir: the absolute local directory. e.g. /home/user1/tmp/
  :param str outfile: (optional) filename stored in local directory. If outfile is not given, extract the filename from url
  :return: the local full path name of downloaded url
  """
  if not url or type(url) != str \
     or not outdir or type(outdir) != str:
      logger.error('passed in parameters %s %s are incorrect.' % (url, outdir))
      return

  if not naarad.utils.is_valid_url(url):
    logger.error("passed in url %s is incorrect." % url)
    return

  if not outfile:
    segs = url.split('/')
    outfile = segs[-1]
    outfile = urllib2.quote(outfile)

  output_file = os.path.join(outdir, outfile)
  if os.path.exists(output_file):
    logger.warn("the %s already exists!" % outfile)

  with open(output_file, "w") as fh:
    try:
      response = urllib2.urlopen(url)
      fh.write(response.read())
    except urllib2.HTTPError:
      logger.error("got HTTPError when retrieving %s" % url)
      return
    except urllib2.URLError:
      logger.error("got URLError when retrieving %s" % url)
      return

  return output_file


def stream_url(url):
  """
  Read response of specified url into memory and return to caller. No persistence to disk.
  :return: response content if accessing the URL succeeds, False otherwise
  """
  try:
    response = urllib2.urlopen(url)
    response_content = response.read()
    return response_content
  except (urllib2.URLError, urllib2.HTTPError) as e:
    logger.error('Unable to access requested URL: %s', url)
    return False


class HTMLLinkExtractor(HTMLParser):
  """
  Helper class to parse the html file returned. It extracts href links into links[]
  """
  def __init__(self):
    HTMLParser.__init__(self)
    self.flag = 0
    self.links = []
    self.title = ""
    self.img = ""
    self.content = ""

  def handle_starttag(self, tag, attrs):
    if tag == "a":
      if len(attrs) != 0:
        for (variable, value) in attrs:
          if variable == "href":
            self.links.append(value)


def get_urls_from_seed(url):
  """
  get a list of urls from a seeding url, return a list of urls

  :param str url: a full/absolute url, e.g. http://www.cnn.com/logs/
  :return: a list of full/absolute urls.
  """

  if not url or type(url) != str or not naarad.utils.is_valid_url(url):
    logger.error("get_urls_from_seed() does not have valid seeding url.")
    return

  # Extract the host info of "http://host:port/" in case of href urls are elative urls (e.g., /path/gc.log)
  # Then join (host info and relative urls) to form the complete urls
  base_index = url.find('/', len("https://"))   # get the first "/" after http://" or "https://"; handling both cases.
  base_url = url[:base_index]      # base_url = "http://host:port" or https://host:port" or http://host" (where no port is given)

  # Extract the "href" denoted urls
  urls = []
  try:
    response = urllib2.urlopen(url)
    hp = HTMLLinkExtractor()
    hp.feed(response.read())
    urls = hp.links
    hp.close()
  except urllib2.HTTPError:
    logger.error("Got HTTPError when opening the url of %s" % url)
    return urls

  # Check whether the url is relative or complete
  for i in range(len(urls)):
    if not urls[i].startswith("http://") and not urls[i].startswith("https://"):    # a relative url ?
      urls[i] = base_url + urls[i]

  return urls


def download_url_single(inputs, outdir, outfile=None):
  """
  Downloads a http(s) url to a local file
  :param str inputs:  the absolute url
  :param str outdir: Required. the local directory to put the downloadedfiles.
  :param str outfile: // Optional. If this is given, the downloaded url will be renated to outfile;
    If this is not given, then the local file will be the original one, as given in url.
  :return: the local full path name of downloaded url
  """

  if not inputs or type(inputs) != str or not outdir or type(outdir) != str:
    logging.error("The call parameters are invalid.")
    return
  else:
    if not os.path.exists(outdir):
      os.makedirs(outdir)

  output_file = handle_single_url(inputs, outdir, outfile)
  return output_file


def download_url_regex(inputs, outdir, regex=".*"):
  """
  Downloads http(s) urls to a local files
  :param str inputs: Required, the seed url
  :param str outdir: Required. the local directory to put the downloadedfiles.
  :param str regex: Optional, a regex string. If not given, then all urls will be valid
  :return: A list of local full path names (downloaded from inputs)
  """
  if not inputs or type(inputs) != str \
     or not outdir or type(outdir) != str:
    logging.error("The call parameters are invalid.")
    return
  else:
    if not os.path.exists(outdir):
      os.makedirs(outdir)

  output_files = []
  files = get_urls_from_seed(inputs)
  for f in files:
    if re.compile(regex).match(f):
      output_file = handle_single_url(f, outdir)
      output_files.append(output_file)

  return output_files


def download_url_list(url_list, outdir):
  """
  Downloads list of http(s) urls to local files
  :param list url_list: list of URLs to download
  :param str outdir: Required. the local directory to put the downloadedfiles.
    If this is not given, then the local file will be the original one, as given in url.
  :return None
  """
  for url in url_list:
    download_url_single(url, outdir)
