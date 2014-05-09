import os,sys
import subprocess
import shutil

import boto
import boto.beanstalk
import boto.beanstalk.layer1
import boto.s3
import boto.s3.connection

import utils

class EB:
  
  def __init__(self,config,app,path,version_string):
    self.app = app
    self.path = path
    self.version_string = version_string
    self.config = config.EB[app]

  def localProvision(self):
    ''' 
    Check that the config file exists, zip the application, upload to S3
    '''
    c = utils.connect(boto.s3.connection.S3Connection)

    if not utils.find_r(self.path,self.config['app_config_file']):
      sys.exit('%s not found! Exiting.' % self.config['app_config_file'])
    base_name = '%s_%s' % (self.app,self.version_string)
    
    print "Archiving %s" % self.path
    shutil.make_archive(base_name,format='zip',root_dir=self.path)

    print "Uploading to S3"
    bucket = c.get_bucket(self.config['s3_bucket'])
    k = boto.s3.key.Key(bucket)
    k.key = self.version_string
    k.set_contents_from_filename('%s.zip' % base_name)

  def remoteProvision(self):
    '''
    Set up EB apps/versions
    '''
    c = utils.connect(boto.beanstalk.layer1.Layer1)
    c.create_application_version(self.app,self.version_string,s3_bucket=self.config['s3_bucket'],s3_key=self.version_string)
    env_name = self.config['environment']['environment_name']
    try:
      c.create_environment(self.app,env_name,template_name='%s-template' % env_name,version_label=self.version_string)
    except:
      print "Updating environment"
      c.update_environment(environment_name=env_name,template_name='%s-template' % env_name,version_label=self.version_string)