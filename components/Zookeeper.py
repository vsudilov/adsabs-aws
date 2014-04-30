import sys,os
import time
import subprocess

import boto
import boto.ec2
import utils


class Zookeeper:
  def __init__(self,num_instances=3,tag='Name',tag_value='zookeeper'):
    self.c = utils.connect(boto.ec2.connection.EC2Connection)
    self.num_instances = num_instances
    self.tag = tag
    self.tag_value = tag_value
    self.metadata = boto.utils.get_instance_metadata()
    self.this_instance = next(i for i in self.c.get_only_instances() if i.id == self.metadata['instance-id'])

  def _configureNetworkInterface(self):
    P = subprocess.Popen(['dhclient','eth1'])
    P.wait()

    with open('/etc/iproute2/rt_tables','a') as fp:
      fp.write('\n200 zookeeper\n')

    commands = '''
      ip route add default via 10.0.0.1 dev eth1 table zookeeper
      ip rule add from {ip}/32 table zookeeper
      ip rule add to {ip}/32 table zookeeper
      ip route flush cache
    '''.strip().format(ip=self.eni.private_ip_address)

    for c in commands.split('\n'):
      P = subprocess.Popen(c.strip().split())
      P.wait()

  def localProvision(self,zk_dockerfile_path='/adsabs-vagrant/dockerfiles/zookeeper/'):
    '''
    idempotent provisioning of zookeeper ensemble in AWS/EC2
    We assume that the autoscale group takes care of keeping N instances up.
    '''

    ENIs = dict([(i.tags['Name'].split('-')[-1],i) for i in self.c.get_all_network_interfaces() if 'zookeeper' in i.tags.get('Name','')])

    try:
      self.eni = [i for i in ENIs.values() if not i.attachment][0]
    except IndexError:
      #If this provisioner is running, there should be at least one unallocated ENI
      raise EnvironmentError, "No unallocated ENIs!"

    self.c.attach_network_interface(self.eni.id,self.this_instance.id,device_index=1)
    time.sleep(5) #Wait for OS to see the new interface
    self._configureNetworkInterface()
    utils.mkdir_p(zk_dockerfile_path)
    _id = self.eni.tags['Name'].split('-')[-1]
    with utils.cd(zk_dockerfile_path):
      with open('myid','w') as fp:
        fp.write(_id)
      with open('zoo.cfg','r') as fp:
        lines = [i for i in fp.readlines() if "server." not in i]
      servers = ['server.%s=%s:2888:3888' % (key,interface.private_ip_address) for key,interface in ENIs.iteritems()]
      servers.sort()
      lines.extend(servers)
      with open('zoo.cfg','w') as fp:
        fp.write('\n'.join(lines))

