import os,sys,time
import subprocess
import tarfile
import datetime

import boto
import boto.ec2
import boto.s3
import boto.s3.connection

import utils

class Adslogging:
  
  def __init__(self):
    self.c = utils.connect(boto.s3.connection.S3Connection)

  def discoverLogstash(self):
    c = utils.connect(boto.ec2.connection.EC2Connection)
    instances = [i for i in c.get_only_instances() if i.tags.get('Name',None) == 'adslogging-asg']

    if instances:
      latest = sorted(instances,key=lambda i: datetime.datetime.strptime(i.launch_time[:i.lanuch_time.rfind('.')],'%Y-%m-%dT%H:%M:%s'))[-1]
      return latest.private_ip_address

    return None
    

  def localProvision(self,bucket='adsabs-logging',key='adslogging_certs.tar.gz',certpath='/adslogging/dockerfiles/logstash/certs/'):
    utils.mkdir_p(certpath)
    b = self.c.get_bucket(bucket)
    k = b.get_key(key)
    f = os.path.join(certpath,key)
    k.get_contents_to_filename(f)
    with tarfile.open(f) as tf:
      tf.extractall(path=certpath)

    logstash_ip = discoverLogstash()
    with open('/SET_LOGSTASH_SERVER.bash','w') as fp:
      fp.write('export LOGSTASH_SERVER="%s:"' % logstash_ip)
