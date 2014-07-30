import os,sys,time
import subprocess

import boto
import boto.ec2

import utils

class UserScript:
  
  def __init__(self,tags,key,script):
    self.c = utils.connect(boto.ec2.connection.EC2Connection)
    tags = tags.split(':')
    self.tags = {'key':tags[0],'value':tags[1]}
    self.key = os.path.abspath(key)
    self.script = os.path.abspath(script)

  def localProvision(self):
    instances = [i for i in self.c.get_only_instances() if i.tags.get(self.tags['key'],None) == self.tags['value'] and i.state=="running"]
    for i in instances:
      rsync = "rsync -vrPa -e 'ssh -C -i %(key)s' %(script)s ubuntu@%(remote)s:/tmp/UserScript.sh" % {'script':self.script,'remote':i.ip_address, 'key':self.key}
      ssh = "ssh -i %(key)s ubuntu@%(remote)s 'bash /tmp/UserScript.sh'" % {'key':self.key,'remote':i.ip_address}

      print "Running:\n\t%s" % rsync
      P = subprocess.Popen(rsync,shell=True)
      P.wait()
      print "Running:\n\t%s" % ssh
      P = subprocess.Popen(ssh,shell=True)
      P.wait()

