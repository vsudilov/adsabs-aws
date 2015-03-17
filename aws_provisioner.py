import sys,os
import argparse
import config

from components import utils
from components import Solr
from components import ENIProvisioner


def main(argv=sys.argv):
  parser = argparse.ArgumentParser()
  g = parser.add_mutually_exclusive_group()
  g.add_argument(
    '--get-instance-tag',
    default=None,
    nargs=1,
    dest='get',
    help='\n'.join([
      'tag: The tag name to query on this instance (returns VALUE in TAG:VALUE)',
    ]),
  )

  g.add_argument(
    '--eni',
    default=None,
    nargs=1,
    dest='eni',
    metavar=('instance_tags',),
    help='\n'.join([
      'instances_tags: instances to connect to defined by tags ("Key:Value")',
    ]),
  )
  g.add_argument(
    '--user-script',
    default=None,
    nargs=3,
    dest='user_script',
    metavar=('instance_tags','ssh_key','script','ec2_user'),
    help='\n'.join([
      'instances_tags: instances to connect to defined by tags ("Key:Value")',
      'ssh_key: path to ssh key',
      'script: path to script to run',
      'ec2_user: ec2 user (ubuntu for Ubuntu, ec2-user for amazon-linux or debian)',
    ]),
  )

  args = parser.parse_args()
  if args.get_instance_tag:
    sys.stdout.write(utils.get_instance_tag_value(args.get_instance_tag))

  if args.eni:
    P = ENIProvisioner(tags)
    P.provision()

  if args.user_script:
    tags,key,script = args.user_script
    P = UserScript(tags,key,script,ec2_user)
    P.run()

if __name__ == '__main__':
  main()


