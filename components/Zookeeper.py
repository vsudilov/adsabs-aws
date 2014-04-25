import sys,os

import boto
import boto.ec2
import boto.ec2.autoscale
import utils

class Zookeeper:
  def __init__(self,boto_ec2_connection,num_instances=3,
                tag=                'Name',
                tag_value=          'zookeeper',
                id_tag=             'id'): #The tag params here represent what they should/will be, not what they necessarily are.
    self.c = boto_ec2_connection
    self.num_instances = instances
    self.tag = tag
    self.tag_value = tag_value
    self.metadata = utils.get_instance_metadata()
    self.zookeepers = self.c.get_only_instances()
    self.this_instance = next(i for i in self.zookeepers if i.id == self.metadata['instance-id'])

  def checkASG(self,resource_id='zookeeper-ensemble-group'):
    '''
    Not currently possible to assign ASG tags via the web interface
    TODO: Check launchconfig, this still assumes the ASG exists
    '''
    conn = boto.ec2.autoscale.AutoScaleConnection()
    groups = conn.get_all_groups()

    if resource_id not in [g.name for g in groups]:
      t = boto.ec2.autoscale.tag.Tag(key='Name',value='zookeeper',propagate_at_launch=True,resource_id=resource_id)
      conn.create_or_update_tags(t)
      conn.update()

  def globalProvision(self):
    '''
    idempotent provisioning of zookeeper ensemble in AWS/EC2
    We assume that the autoscale group takes care of keeping N instances up.
    '''
    self.checkASG()

    instances = [i for i in self.zookeepers if self.tag_value in i.tags[self.tag]]
    if len(instances) != self.num_instances:
      #Autoscaling isn't working! An alarm should be set for this!
      sys.exit(1)

    #Map the EIPs to any instances without one
    addrs = utils.getEIPs(self.c,shouldExist=3)

    #These instances need an IP and ID assigned
    pool_ip = [a for a in addrs if a.public_ip not in [i.ip_address for i in instances]]
    pool_id = set([i+1 for i in range(self.num_instances)]).difference([int(i.tags[self.id_tag]) for i in instances])
    assert len(pool_ip)==len(pool_id)
    for inst in [i for i in instances if i.ip_address not in [a.public_ip for a in addrs]]:
      inst.tags[self.id_tag] = pool_id.pop()
      inst.use_ip(pool_ip.pop())
      inst.update()
      instances.append(inst)
    assert len(instances) == self.num_instances

  def localProvision(self,zk_datadir='/zookeeper/data/'):
    utils.mkdir_p(zk_datadir)
    _id = self.this_instance.tags[self.id_tag]

    with open(os.path.join(zk_dir,'myid'),'w') as fp:
      fp.write(_id)