import boto
import boto.ec2
import utils

class ENIProvisioner:
  def __init__(self,tag):
    tag = tag.split(':')
    self.tag = {'key':tag[0],'value':tag[1]}
    self.c = utils.connect(boto.ec2.EC2Connection)

  def get_eni_pool(self):
    '''
    Find all detached ENIs by tag, then
    find their associated elastic IPs
    '''
    enis = self.c.get_all_network_interfaces(
      filters={
        'tag-key':self.tag['key'],
        'tag-value':self.tag['value'],
        'attachment.status':'detached',
        }
    )
    addresses = []
    for eni in enis:
      addresses.extend(
        self.c.get_all_addresses(
          filters={
            'network-interface-id':eni.id
          }
        )
      )
    return addresses

  def provision(self):
    this_instance = utils.get_this_instance()

    poller = utils.SyncPollWhileFalse(self.get_eni_pool,max_tries=2,poll_interval=3)
    addresses = poller.poll()

    if not addresses:
      raise Exception("No suitable ENI/EIPs were found")

    target = addresses[0]
    poller = utils.SyncPollWhileFalse(
      target.associate,
      f_kwargs={
        'instance_id': this_instance.id,
        'allow_reassociation': True,
      },
      max_tries = 3,
      poll_interval = 5,
    )
    success = poller.poll()

    if not success:
      raise Exception("Could not associate {eni}".format(eni=target.network_interface_id))





