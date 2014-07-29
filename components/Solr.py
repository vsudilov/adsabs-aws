import os,sys,time
import subprocess

import boto
import boto.ec2

import utils

class Solr:
  
  def __init__(self):
    self.c = utils.connect(boto.ec2.connection.EC2Connection)
    self.this_instance = utils.get_this_instance()
    self.shardId = self._setupVolumes()

  def _setupVolumes(self):
    '''
    Attaches the next available EBS volume
    Mounts the volume under /data/

    returns the shardId based on the tags on that volume
    '''
    def getNext():
      volumes = [i for i in self.c.get_all_volumes() if i.tags.get('Name',None) == 'solr-data-volume']
      #There should be an available volume. If not, there is a more fundamental problem with the plumbing
      #This will raise StopIteration if that's the case.
      next_available = next(i for i in volumes if i.status=='available')
      return next_available
    
    next_available = getNext()
    try:
      next_available.attach(self.this_instance.id,'/dev/xvdf')
    except boto.exception.EC2ResponseError:
      next_available = getNext()
      next_available.attach(self.this_instance.id,'/dev/xvdf')

    shardId = next_available.tags['shardId']
    next_available.update()

    time.sleep(5)
    cmd = ['file','-s','/dev/xvdf']
    P = subprocess.Popen(cmd,stdout=subprocess.PIPE)
    P.wait()
    o = P.stdout.readline().strip()
    if o == '/dev/xvdf: data':
      cmd = ['mkfs','-t','ext4','/dev/xvdf']
      P = subprocess.Popen(cmd)
      P.wait()
    # print "Warming EBS"
    # start = time.time()
    # P = subprocess.Popen(['dd','if=/dev/xvdf','of=/dev/null','bs=1M'])
    # P.wait()
    # print "dd completed in %0.1f seconds" % (time.time()-start)
    utils.mkdir_p('/data')
    cmd = ['mount','/dev/xvdf','/data']
    P = subprocess.Popen(cmd)
    P.wait()

    with open('/etc/fstab','r') as fp:
      lines = [L.strip() for L in fp.readlines()]
    L = '/dev/xvdf       /data   ext4    defaults        0       2'
    if L not in lines:
      lines.append(L)
    with open('/etc/fstab','w') as fp:
      fp.write('\n'.join(lines))

    return shardId


  def localProvision(self):
    '''
    1. Write zookeeper IPs to /etc/hosts
    2. Find and write local IPs to run.sh to be sent as -Dhost property
    '''
    ENIs = dict([(i.tags['Name'].split('-')[-1],i) for i in self.c.get_all_network_interfaces() if 'zookeeper' in i.tags.get('Name','')])
    with open('/etc/hosts','a') as fp:
      fp.write('\n')
      fp.write('\n'.join(['%s zookeeper%s' % (interface.private_ip_address,key) for key,interface in ENIs.iteritems()]))

    #Assume the cwd has been set correctly before runtime
    with open('run.sh','r') as fp:
      lines = fp.readlines()
    with open('run.sh','w') as fp:
      lines = [L if not L.startswith("H=") else "H=%s\n" % self.this_instance.private_ip_address for L in lines]
      lines = [L if not L.startswith("shardId=") else "shardId=%s\n" % self.shardId for L in lines]
      fp.write(''.join(lines))