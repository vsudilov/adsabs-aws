import sys,os
import time

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
    self.this_instance = next(i for i in self.zookeepers if i.id == self.metadata['instance-id'])

  def localProvision(self,zk_dockerfile_path='/adsabs-vagrant/dockerfiles/zookeeper/'):
    '''
    idempotent provisioning of zookeeper ensemble in AWS/EC2
    We assume that the autoscale group takes care of keeping N instances up.
    '''

    ENIs = [i for i in self.c.get_all_network_interfaces() if 'zookeeper' in i.tags.get('Name','')]

    try:
      self.eni = [i for i in ENIs if not i.attachment][0]
    except IndexError:
      #If this provisioner is running, there should be at least one unallocated ENI
      raise EnvironmentError, "No unallocated ENIs!"

    self.c.attach_network_interface(self.eni.id,self.this_instance.id,device_index=1)
    time.sleep(1)

    utils.mkdir_p(zk_datadir)
    _id = self.eni.tags['Name'].split('-')[1]
    with open(os.path.join(zk_dockerfile_path,'myid'),'w') as fp:
      fp.write(_id)
    with open(os.path.join(zk_dockerfile_path,'zoo.cfg'),'w') as fp:
      lines = [i for i in fp.readlines() if "server." not in i]
      servers = ['%s:2888:3888' % i.private_ip_address for i in ENIs]
      lines.extend(servers)
      fp.write('\n'.join(lines))

