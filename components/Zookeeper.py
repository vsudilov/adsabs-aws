import boto
import boto.ec2
import boto.ec2.autoscale
import sys,os
import utils

class Zookeeper:
  def __init__(self,boto_ec2_connection,instances=3,
                tag=                'Name',
                tag_value=          'zookeeper'):
    self.c = boto_ec2_connection
    self.instances = 3
    self.tag = tag
    self.tag_value = tag_value

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

  def provision(self):
    '''
    idempotent provisioning of zookeeper ensemble in AWS/EC2
    We assume that the autoscale group takes care of keeping N instances up.
    '''
    self.checkASG()

    instances = [i for i in self.c.get_only_instances() if self.tag_value in i.tags[self.tag]]
    if len(instances) != self.instances:
      #Autoscaling isn't working! An alarm should be set for this!
      sys.exit(1)

    #Map the EIPs to any instances without one
    addrs = utils.getEIPs(self.c,shouldExist=3)

    #These instances need an IP assigned
    pool = [a for a in addrs if a.public_ip not in [i.ip_address for i in instances]]
    for instance in [i for i in instances if i.ip_address not in [a.public_ip for a in addrs]]:
      instance.use_ip(pool.pop())