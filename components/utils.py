import os,sys
import errno

import boto
import boto.ec2
import boto.utils

'''
Define general tasks our deployment in AWS
'''

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

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise
