import os,sys,time
import subprocess
import datetime
import time

import boto
import boto.ec2

import utils

class UserScript:
  
  def __init__(self,tag,key,ec2_user,script,script_args):
    tag = tag.split(':')
    self.tag = {'key':tag[0],'value':tag[1]}
    self.key = os.path.abspath(key)
    self.script = os.path.abspath(script)
    self.tmpfile = 'userscript_{time}.sh'.format(
      time=datetime.datetime.utcnow().strftime('%m.%d.%Y_%H:%M:%S')
    )
    self.user = ec2_user
    self.c = utils.connect(boto.ec2.connection.EC2Connection)
    self.script_args = script_args
    
  def get_instances(self):
    return self.c.get_only_instances(
      filters={
        'tag-key':self.tag['key'],
        'tag-value':self.tag['value'],
        'instance-state-name': 'running',
        }
    )

  def run(self):
    for i in self.get_instances():
      ip = utils.get_eni_publicIP(instance=i) if len(i.interfaces) > 1 else i.ip_address
      rsync = "rsync -vrPa -e 'ssh -C -i {key}' {script} {user}@{remote}:/tmp/{tmpfile}".format(
        key=self.key,
        user=self.user,
        script=self.script,
        remote=ip,
        tmpfile=self.tmpfile,
      )
      ssh = "ssh -t -i {key} {user}@{remote} 'sudo bash /tmp/{tmpfile} {args}'".format(
        key=self.key,
        remote=ip,
        tmpfile=self.tmpfile,
        user=self.user,
        args=self.script_args,
      )
      print "Targetting remote instance: %s | %s" % (i,ip)

      s = time.time()
      print "\tRunning:\n\t\t%s" % rsync
      P = subprocess.Popen(rsync,shell=True)
      retval = P.wait()
      print "\t...completed in %0.2f seconds" % (time.time()-s)
      if retval != 0:
        sys.exit("Non-zero exit status on {cmd}. Exit!".format(cmd=rsync))

      s = time.time()
      print "\tRunning:\n\t\t%s" % ssh
      P = subprocess.Popen(ssh,shell=True)
      retval = P.wait()
      print "\t...completed in %0.2f seconds" % (time.time()-s)
      if retval != 0:
        sys.exit("Non-zero exit status on {cmd}. Exit!".format(cmd=ssh))

