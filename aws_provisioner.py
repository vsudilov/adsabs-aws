import sys,os
import argparse
import config

from components import Solr
from components import UserScript


def main(argv=sys.argv):
  parser = argparse.ArgumentParser()
  parser.add_argument(
    '--zookeeper',
    default=False,
    action='store_true',
    dest='zookeeper',
  )

  parser.add_argument(
    '--user-script',
    default=None,
    nargs=3,
    dest='user_script',
    metavar=('instance_tags','ssh_key','script'),
    help='\n'.join([
      'instances_tags: instances to connect to defined by tags ("Key:Value")',
      'ssh_key: path to ssh key',
      'script: path to script to run',
      ]),
  )

  args = parser.parse_args()

  if args.zookeeper:
    P = Zookeeper.Zookeeper()
    P.localProvision()

  if args.user_script:
    tags,key,script = args.user_script
    P = UserScript.UserScript(tags,key,script)
    P.localProvision()

if __name__ == '__main__':
  main()
