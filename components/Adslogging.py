import os,sys,time
import subprocess
import tarfile

import boto
import boto.ec2
import boto.s3
import boto.s3.connection

import utils

class Adslogging:
  
  def __init__(self):
    self.c = utils.connect(boto.s3.connection.S3Connection)

  def localProvision(self,bucket='adsabs-logging',key='adslogging_certs.tar.gz',certpath='/adslogging/dockerfiles/logstash/certs/'):
    utils.mkdir_p(certpath)
    b = self.c.get_bucket(bucket)
    k = b.get_key(key)
    f = os.path.join(certpath,key)
    k.get_contents_to_filename(f)
    with tarfile.open(f) as tf:
      tf.extractall(path=certpath)