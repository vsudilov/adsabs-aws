import sys,os
import argparse
import config

from components import Solr
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
  parser.add_argument(
    '--solr',
    default=False,
    action='store_true',
    dest='solr',
  )
  parser.add_argument (
    '--global',
    default=False,
    action='store_true',
    dest='global_provision',
  )


  args = parser.parse_args()

  if args.global_provision:
    P = GlobalProvisioner.GlobalProvisioner(config)
    P.orderedProvision()

  if args.zookeeper:
    P = Zookeeper.Zookeeper()
    P.localProvision()

  if args.solr:
    P = Solr.Solr()
    P.localProvision()

if __name__ == '__main__':
  main()