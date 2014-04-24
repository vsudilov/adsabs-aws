import os,sys
import boto
import boto.ec2

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