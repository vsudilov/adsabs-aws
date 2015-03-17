import boto
import boto.ec2
import utils

class ENIProvisioner:
  def __init__(self,tags,value):
    tags = tags.split(':')
    self.tags = {'key':tags[0],'value':tags[1]}
    self.key = os.path.abspath(key)
  def provision(self):
    pass