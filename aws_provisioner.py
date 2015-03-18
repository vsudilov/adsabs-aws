import sys,os
import argparse

from components import utils
from components import ENIProvisioner
from components import UserScript
from components import EBSProvisioner

def main(argv=sys.argv):
  parser = argparse.ArgumentParser()
  g = parser.add_mutually_exclusive_group(required=True)
  g.add_argument(
    '--get-instance-tag',
    default=None,
    nargs=1,
    dest='get_instance_tag',
    metavar=('tag'),
    help='\n'.join([
      'tag: The tag name to query on this instance (returns VALUE in TAG:VALUE)',
    ]),
  )
  g.add_argument(
    '--eni',
    default=None,
    nargs=1,
    dest='eni_tag',
    metavar=('eni_tag'),
    help='\n'.join([
      'eni_tag: ENI to attach, defined by a single tag ("Key:Value")',
    ]),
  )

  g.add_argument(
    '--ebs',
    default=None,
    nargs=1,
    dest='ebs_tag',
    metavar=('ebs_tag'),
    help='\n'.join([
      'ebs_tag: EBS volume to attach, defined by a single tag ("Key:Value")',
    ]),
  )

  g.add_argument(
    '--user-script',
    default=None,
    nargs=4,
    dest='user_script',
    metavar=('instance_tag','ssh_key','script','ec2_user'),
    help='\n'.join([
      'instances_tag: instances to connect to defined by a single tag ("Key:Value")',
      'ssh_key: path to ssh key',
      'script: path to script to run',
      'ec2_user: ec2 user (ubuntu for Ubuntu, ec2-user for amazon-linux or debian)',
    ]),
  )
  args = parser.parse_args()

  if args.get_instance_tag:
    sys.stdout.write(utils.get_instance_tag_value(args.get_instance_tag[0]))

  if args.eni_tag:
    tag = args.eni_tag[0]
    P = ENIProvisioner(tag)
    P.provision()

  if args.ebs_tag:
    tag = args.ebs_tag[0]
    P = EBSProvisioner(tag)
    P.provision()  

  if args.user_script:
    tag,key,script = args.user_script
    P = UserScript(tag,key,script,ec2_user)
    P.run()

if __name__ == '__main__':
  main()


