import boto
import boto.ec2
import boto.iam
import boto.vpc

import utils

class GlobalProvisioner:
  '''
  Provisions AWS resources based on ../config.py
  Create new resource only if that resource (identified by tag) does not yet exist.
  This provisioner will NEVER overwrite resources, even to update.
  '''

  def __init__(self,config):
    self.config = config

  def orderedProvision(self):
    #self._IAM_provision() #TODO:Figure out why AWS gives policy syntax error
    self._VPC_provision()
    self._EC2_provision()

  def _EC2_provision(self):
    c = utils.connect(boto.ec2.connection.EC2Connection)
    c2 = utils.connect(boto.vpc.VPCConnection)
    snapshot_groups = c.get_all_security_groups()
    snapshot_vpcs = c2.get_all_vpcs()
    snapshot_subnets = c2.get_all_subnets()

    #Security groups
    for s in set(self.config.EC2['security_groups'].keys()).difference([i.tags.get('Name',None) for i in c.get_all_security_groups()]):
      properties = self.config.EC2['security_groups'][s]
      vpc_id = next(i.id for i in snapshot_vpcs if i.tags.get('Name',None)==properties['vpc'])
      sg = c.create_security_group(s, properties['description'], vpc_id=vpc_id, dry_run=False)
      c.create_tags(sg.id,properties['tags'])
      [sg.authorize(**rule) for rule in properties['rules']]

    #ENIs
    for n in set(self.config.EC2['network_interfaces'].keys()).difference([i.tags.get('Name',None) for i in c.get_all_network_interfaces()]):
      properties = self.config.EC2['network_interfaces'][n]
      groups = [i.id for i in snapshot_groups if i.tags.get('Name',None) in properties['groups']]
      subnet_id = next(i.id for i in snapshot_subnets if i.tags.get('Name',None)==properties['subnet'])
      ni = c.create_network_interface(subnet_id,description=properties['description'],groups=groups)
      c.create_tags(ni.id,properties['tags'])
      if properties['EIP']:
        eip = c.allocate_address()
        #When using an Allocation ID, make sure to pass None for public_ip as EC2 expects a single parameter and if public_ip is passed boto will preference that instead of allocation_id.
        c.associate_address(network_interface_id=ni.id,public_ip=None,allocation_id=eip.allocation_id)

  def _VPC_provision(self):
    c = utils.connect(boto.vpc.VPCConnection)

    for v in set(self.config.VPC.keys()).difference([i.tags.get('Name',None) for i in c.get_all_vpcs()]):
      properties = self.config.VPC[v]
      vpc = c.create_vpc(properties['cidr_block'], instance_tenancy=None, dry_run=False)
      c.create_tags(vpc.id,properties['tags'])
      gateway = c.create_internet_gateway()
      c.attach_internet_gateway(gateway.id,vpc.id) #TODO: Route tables?
      for subnet in self.config.VPC[v]['subnets']:
        s = c.create_subnet(vpc.id,subnet['cidr_block'],availability_zone=None, dry_run=False)
        c.create_tags(s.id,subnet['tags'])

  def _IAM_provision(self):
    c = utils.connect(boto.iam.connection.IAMConnection)
    for role,properties in self.config.IAM.iteritems():
      try:
        #If no exception is raised, role already exists. Assume it has been configured properly ;)
        c.get_role(role)
        continue
      except boto.exception.BotoServerError:
        c.create_role(role, assume_role_policy_document=properties['doc'], path=properties['path'])