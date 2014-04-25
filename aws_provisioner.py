import sys,os
import argparse
import config

from components import Zookeeper
from components import GlobalProvisioner


def main(argv=sys.argv):
  parser = argparse.ArgumentParser()
  parser.add_argument(
    '--zookeeper',
    default=False,
    action='store_true',
    dest='zookeeper',
  )
  parser.add_argument (
    '--global_provision',
    default=False,
    action='store_true',
    dest='global_provision',
  )
  args = parser.parse_args()

  if args.global_provision:
    gp = GlobalProvisioner.GlobalProvisioner(config)
    gp.orderedProvision()

  if args.zookeeper:
    zk = Zookeeper.Zookeeper(connect())
    zk.localProvision()

if __name__ == '__main__':
  main()