import os,sys
import subprocess

import boto
import boto.ec2

import utils

class Solr:
  
  def __init__(self):
    self.c = utils.connect(boto.ec2.connection.EC2Connection)
    self.metadata = boto.utils.get_instance_metadata()
    self.this_instance = next(i for i in self.c.get_only_instances() if i.id == self.metadata['instance-id'])

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
      fp.write(''.join(lines))