import os,sys,time
import subprocess
import datetime

import boto
import boto.ec2

import utils

class UserScript:
  
  def __init__(self,tags,key,script,ec2_user):
    self.c = utils.connect(boto.ec2.connection.EC2Connection)
    tags = tags.split(':')
    self.tags = {'key':tags[0],'value':tags[1]}
    self.key = os.path.abspath(key)
    self.script = os.path.abspath(script)
    self.tmpfile = 'userscript_{time}.sh'.format(
      time=datetime.datetime.utcnow().strftime('%m.%d.%Y_%H:%M:%S')
    )
    self.user = ec2_user

  def run(self):
    instances = [i for i in self.c.get_only_instances() if i.tags.get(self.tags['key'],None) == self.tags['value'] and i.state=="running"]
    for i in instances:
      rsync = "rsync -vrPa -e 'ssh -C -i {key}' {script} {user}@{remote}:/tmp/{tmpfile}".format(
        key=self.key,
        user=self.user,
        script=self.script,
        remote=i.ip_address,
        tmpfile=self.tmpfile
      )
      ssh = "ssh -i {key} {user}@{remote} 'bash /tmp/{tmpfile}'".format(
        key=self.key,
        remote=i.ip_address,
        tmpfile=self.tmpfile,
        user=self.user,
      )

      print "Running:\n\t%s\non %s" % (rsync,i)
      P = subprocess.Popen(rsync,shell=True)
      P.wait()
      print "Running:\n\t%s\non %s" % (ssh,i)
      P = subprocess.Popen(ssh,shell=True)
      P.wait()

