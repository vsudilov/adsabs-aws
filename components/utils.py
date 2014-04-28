import os,sys
import errno

import boto
import boto.ec2
import boto.utils

'''
Define general tasks our deployment in AWS
'''

def connect(ConnectionClass):
  _id = os.environ.get('AWS_ACCESS_KEY',None)
  key = os.environ.get('AWS_SECRET_KEY',None)
  try:
    #auth is automatically handled via IAM in an EC2 instance; no need to supply credentials
    c = ConnectionClass()
  except boto.exception.NoAuthHandlerFound:
    #Fallback: either we aren't in an EC2 instance, or no IAM group has been set
    c = ConnectionClass(aws_access_key_id=_id,aws_secret_access_key=key)
  return c

def getEIPs(conn,shouldExist=3):
  #Get elastic IPs
  addrs = conn.get_all_addresses()
  if len(addrs) > shouldExist:
    #Too many EIPs; something is very wrong. An alarm should be set!
    sys.exit(1)
  
  while len(addrs) < shouldExist:
    addrs.append(conn.allocate_address())

  return addrs

def get_instance_metadata():
  return boto.utils.get_instance_metadata()

def find_resource_by_tag(tag,value):
  pass

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise
