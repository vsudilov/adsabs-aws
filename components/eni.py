import boto
import boto.ec2
import utils

class ENIProvisioner:
  def __init__(self,tag):
    tag = tag.split(':')
    self.tag = {'key':tag[0],'value':tag[1]}
    self.c = utils.connect(boto.ec2.EC2Connection)
    self.this_instance = utils.get_this_instance()

  def get_eni_pool(self):
    '''
    Find all detached ENIs by tag, then
    find their associated elastic IPs
    '''
    enis = self.c.get_all_network_interfaces(
      filters={
        'tag-key':self.tag['key'],
        'tag-value':self.tag['value'],
        'status':'available',
        'availability-zone':self.this_instance.placement,
        }
    )
    return enis

  def provision(self):

    poller = utils.SyncPollWhileFalse(self.get_eni_pool,max_tries=2,poll_interval=3)
    eni_pool = poller.poll()

    if not eni_pool:
      raise Exception("No suitable ENI/EIPs were found")

    target = eni_pool[0]
    poller = utils.SyncPollWhileFalse(
      target.attach,
      f_kwargs={
        'instance_id': self.this_instance.id,
        'device_index': 1,
      },
      max_tries = 3,
      poll_interval = 5,
    )
    success = poller.poll()

    if not success:
      raise Exception("Could not associate {eni}".format(eni=target.network_interface_id))





