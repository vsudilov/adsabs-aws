import boto
import boto.ec2

import utils

class Solr:
  def __init__(self):
    self.c = utils.connect(boto.ec2.connection.EC2Connection)
  def localProvision(self):
    '''
    Write zookeeper IPs to /etc/hosts
    '''

    ENIs = dict([(i.tags['Name'].split('-')[-1],i) for i in self.c.get_all_network_interfaces() if 'zookeeper' in i.tags.get('Name','')])
    with open('/etc/hosts','a') as fp:
      fp.write('\n')
      fp.write('\n'.join(['%s zookeeper%s' % (interface.private_ip_address,key) for key,interface in ENIs.iteritems()]))
