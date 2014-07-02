import time
import json

import boto
import boto.ec2
import boto.iam
import boto.vpc
import boto.ec2.autoscale
import boto.ec2.elb
import boto.s3
import boto.s3.connection
import boto.beanstalk
import boto.beanstalk.layer1

import utils

class GlobalProvisioner:
  '''
  Provisions AWS resources based on ../config.py
  Create new resource only if that resource (identified by tag) does not yet exist.
  This provisioner will NEVER overwrite resources, even to update.
  '''

  def __init__(self,config):
    self.config = config
    self.account_id = utils.get_account_id()

  def orderedProvision(self):
    print "Provision: IAM"
    self._IAM_provision()
    print "Provision: S3"
    self._S3_provision()
    print "Provision: VPC"
    self._VPC_provision()
    print "Provision: EC2"
    self._EC2_provision()
    print "Provision: ELB"
    self._ELB_provision()
    print "Provision: ASG"
    self._ASG_provision()
    print "Provision: EB"
    self._EB_provision()

  def _EB_provision(self):
    c = utils.connect(boto.beanstalk.layer1.Layer1)
    try:
      current_apps = [a['ApplicationName'] for a in c.describe_applications()['DescribeApplicationsResponse']['DescribeApplicationsResult']['Applications']]
    except TypeError:
      current_apps = []
    for app in set(self.config.EB).difference(current_apps):
      c.create_application(app)
      properties = self.config.EB[app]['environment']
      env_name = properties['environment_name']
      del properties['environment_name']
      c.create_configuration_template(app,'%s-template' % env_name,**properties)
      c.create_storage_location() #AWS makes this idempotent

  def _S3_provision(self):
    c = utils.connect(boto.s3.connection.S3Connection)
    for bucket in self.config.S3:
      if not c.lookup(bucket):
        properties = self.config.S3[bucket]
        c.create_bucket(bucket,**properties)


  def _ELB_provision(self):
    c = utils.connect(boto.ec2.elb.ELBConnection)
    c2 = utils.connect(boto.vpc.VPCConnection)
    c3 = utils.connect(boto.ec2.connection.EC2Connection)
    snapshot_subnets = c2.get_all_subnets()
    snapshot_security_groups = c3.get_all_security_groups()
    c2.close()
    c3.close()

    for elb in set(self.config.EC2['load_balancers'].keys()).difference([i.name for i in c.get_all_load_balancers()]):
      properties = self.config.EC2['load_balancers'][elb]
      properties['security_groups'] = [next(j.id for j in snapshot_security_groups if j.tags.get('Name',None)==i) for i in properties['security_groups']]
      properties['subnets'] = [next(j.id for j in snapshot_subnets if j.tags.get('Name',None)==i) for i in properties['subnets']]
      c.create_load_balancer(**properties)

  def _ASG_provision(self):
    c = utils.connect(boto.ec2.autoscale.AutoScaleConnection)
    c2 = utils.connect(boto.vpc.VPCConnection)
    c3 = utils.connect(boto.ec2.connection.EC2Connection)
    snapshot_subnets = c2.get_all_subnets()
    snapshot_security_groups = c3.get_all_security_groups()
    c2.close()
    c3.close()

    #launch configs
    print "..LC"
    for lc in set(self.config.AS['launch_configs'].keys()).difference([i.name for i in c.get_all_launch_configurations()]):
      properties = self.config.AS['launch_configs'][lc]
      properties['name'] = lc
      properties['security_groups'] = [next(j.id for j in snapshot_security_groups if j.tags.get('Name',None)==i) for i in properties['security_groups']]
      config = boto.ec2.autoscale.launchconfig.LaunchConfiguration(**properties)
      c.create_launch_configuration(config)

    #autoscale groups
    print "..ASG"
    for asg in set(self.config.AS['autoscale_groups'].keys()).difference([i.name for i in c.get_all_groups()]):
      properties = self.config.AS['autoscale_groups'][asg]
      properties['name'] = asg
      properties['availability_zones'] = [next(j.availability_zone for j in snapshot_subnets if j.tags.get('Name',None)==i) for i in properties['vpc_zone_identifier']]
      properties['vpc_zone_identifier'] = [next(j.id for j in snapshot_subnets if j.tags.get('Name',None)==i) for i in properties['vpc_zone_identifier']]
      properties['tags'] = [boto.ec2.autoscale.tag.Tag(**i) for i in properties['tags']]
      group = boto.ec2.autoscale.group.AutoScalingGroup(**properties)
      c.create_auto_scaling_group(group)

  def _EC2_provision(self):
    c = utils.connect(boto.ec2.connection.EC2Connection)
    c2 = utils.connect(boto.vpc.VPCConnection)
    snapshot_vpcs = c2.get_all_vpcs()
    snapshot_subnets = c2.get_all_subnets()
    c2.close()

    #Security groups
    print "..SG"
    for s in set(self.config.EC2['security_groups'].keys()).difference([i.tags.get('Name',None) for i in c.get_all_security_groups()]):
      properties = self.config.EC2['security_groups'][s]
      vpc_id = next(i.id for i in snapshot_vpcs if i.tags.get('Name',None)==properties['vpc'])
      sg = c.create_security_group(s, properties['description'], vpc_id=vpc_id, dry_run=False)
      time.sleep(2)
      c.create_tags(sg.id,properties['tags'])
      [sg.authorize(**rule) for rule in properties['rules']]
    snapshot_groups = c.get_all_security_groups()

    #ENIs
    print "..ENI"
    for n in set(self.config.EC2['network_interfaces'].keys()).difference([i.tags.get('Name',None) for i in c.get_all_network_interfaces()]):
      properties = self.config.EC2['network_interfaces'][n]
      groups = [i.id for i in snapshot_groups if i.tags.get('Name',"None") in properties['groups']]
      subnet_id = next(i.id for i in snapshot_subnets if i.tags.get('Name',None)==properties['subnet'])
      ni = c.create_network_interface(subnet_id,
        description=properties['description'],
        groups=groups,
        private_ip_address=properties['private_ip_address'])
      time.sleep(5)
      c.create_tags(ni.id,properties['tags'])
      if properties['EIP']:
        eip = c.allocate_address()
        time.sleep(2)
        #When using an Allocation ID, make sure to pass None for public_ip as EC2 expects a single parameter and if public_ip is passed boto will preference that instead of allocation_id.
        c.associate_address(network_interface_id=ni.id,public_ip=None,allocation_id=eip.allocation_id)
        time.sleep(2)

    #EBS
    print "..EBS"
    for eb in set(self.config.EC2['volumes'].keys()).difference([i.tags.get('Name',None) for i in c.get_all_volumes()]):
      n = self.config.EC2['volumes'][eb]['number']
      tag = self.config.EC2['volumes'][eb]['tags']
      snapshots = [i for i in c.get_all_snapshots() if i.owner_id==self.account_id and 'shardId' in i.tags]
      del self.config.EC2['volumes'][eb]['number']
      del self.config.EC2['volumes'][eb]['tags']
      properties = self.config.EC2['volumes'][eb]
      for i in range(n):
        shardId = (i % self.config.SolrCloud['shards']) + 1
        if snapshots:
          ss = next(i for i in snapshots if int(i.tags['shardId'])==shardId)
          vol = ss.create_volume(**properties)
        else:  
          vol = c.create_volume(**properties)
        time.sleep(2)
        c.create_tags(vol.id,tag)
        c.create_tags(vol.id,{'shardId':shardId})

  def _VPC_provision(self):
    c = utils.connect(boto.vpc.VPCConnection)

    for v in set(self.config.VPC.keys()).difference([i.tags.get('Name',None) for i in c.get_all_vpcs()]):
      properties = self.config.VPC[v]
      vpc = c.create_vpc(properties['cidr_block'], instance_tenancy=None, dry_run=False)
      time.sleep(5)
      c.create_tags(vpc.id,properties['tags'])
      gateway = c.create_internet_gateway()
      c.attach_internet_gateway(gateway.id,vpc.id) #TODO: Route tables?
      time.sleep(2)
      rt = next(i for i in c.get_all_route_tables() if i.vpc_id==vpc.id)
      c.create_route(rt.id,'0.0.0.0/0',gateway_id=gateway.id)
      for subnet,properties in self.config.VPC[v]['subnets'].iteritems():
        s = c.create_subnet(vpc.id,properties['cidr_block'],availability_zone=properties['availability_zone'], dry_run=False)
        time.sleep(2)
        c.create_tags(s.id,properties['tags'])

  def _IAM_provision(self):
    c = utils.connect(boto.iam.connection.IAMConnection)
    for role,properties in self.config.IAM.iteritems():
      try:
        #If no exception is raised, role already exists. Assume it has been configured properly ;)
        c.get_role(role)
        continue
      except boto.exception.BotoServerError:
        c.create_role(role)
        c.put_role_policy(role,'%s-policy' % role,json.dumps(properties['policy']))
        for profile in properties['instance_profiles']:
          c.create_instance_profile(profile)
          c.add_role_to_instance_profile(profile,role)