import sys,os
import boto
import boto.ec2
import argparse

from components import Zookeeper

def connect():
  c = boto.ec2.connection.EC2Connection
  try:
    #auth is automatically handled via IAM in an EC2 instance; no need to supply credentials
    conn = c()
  except boto.exception.NoAuthHandlerFound:
    #Fallback: either we aren't in an EC2 instance, or no IAM group has been set
    conn = c(aws_access_key_id=os.environ.get('AWS_ACCESS_KEY',None),aws_secret_access_key=os.environ.get('AWS_SECRET_KEY',None))
  return conn

def main(argv=sys.argv):
  parser = argparse.ArgumentParser()
  parser.add_argument(
    '--zookeeper',
    default=False,
    action='store_true',
    dest='zookeeper',
  )
  args = parser.parse_args()

  if args.zookeeper:
    zk = Zookeeper.Zookeeper(connect())
    zk.provision()

if __name__ == '__main__':
  main()