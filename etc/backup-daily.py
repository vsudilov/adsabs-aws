#!/usr/bin/env python

import os,sys
import time
import re
import subprocess

import json
import requests
import logging
import logging.handlers

import boto
import boto.ec2

sys.path.append(os.path.join(os.path.dirname(__file__),'..'))
from components import utils

IP_REGEX = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
logger = logging.getLogger(__name__)

class AppFilter(logging.Filter):
  def filter(self, record):
    record.app_name = 'backup-daily'
    return True

def getDockerContainerIP():
  cmd = ['docker','inspect','solr']
  P = subprocess.Popen(cmd,stdout=subprocess.PIPE)
  P.wait()
  lines = json.loads(P.stdout.read())
  ip = lines[0]['NetworkSettings']['IPAddress']
  return ip

def isLeader(URL='http://localhost:8983/solr/admin/collections?action=CLUSTERSTATUS&wt=json'):
  r = requests.get(URL)
  res = json.loads(r.content)

  leaders = []
  for shard in res['cluster']['collections']['collection1']['shards'].values():
    for replica in shard['replicas'].values():
      if 'leader' in replica and replica['leader']:
        ip = re.search(IP_REGEX,replica['base_url']).group()
        leaders.append(ip)

  if getDockerContainerIP() in leaders:
    return True
  return False

def createSnapshot():
  c = utils.connect(boto.ec2.connection.EC2Connection)
  this_instance = utils.get_this_instance()
  volume = next(v for v in c.get_all_volumes() if v.attach_data.instance_id = this_instance.id)
  volume.create_snapshot(description='%s-%s-snapshot' % (volume.tags['Name'],volume.tags['shardId']) )

def isActive(URL='http://localhost:8983/solr/collection1/admin/mbeans?stats=true&wt=json'):
  r = requests.get(URL)
  res = json.loads(r.content)

  for i in res['solr-mbeans']:
    if i.upper() == 'UPDATEHANDLER':
      index = res['solr-mbeans'].index(i)+1
      if res['solr-mbeans'][index]['updateHandler']['stats']['docsPending']:
        return True
  return False


def forceCommit(URL='http://localhost:8983/solr/update?commit=true'):
  r = requests.get(URL)

def main():
  #1. Check if leader: if not, return
  #2. Check if docsPending: if yes, call commit and poll until docsPending=0
  #3. Call boto.ec2 to creat_snapshot()

  logfmt = '%(levelname)s\t%(app_name)s: %(message)s'
  datefmt= '%m/%d/%Y %H:%M:%S'
  logger.addFilter(AppFilter())
  formatter = logging.Formatter(fmt=logfmt,datefmt=datefmt)
  logging.root.setLevel(logging.INFO)
  ch = logging.StreamHandler() #console handler
  ch.setFormatter(formatter)
  syslogh = logging.handlers.SysLogHandler(address='/dev/log')
  syslogh.setFormatter(formatter)
  logger.handlers = []
  logger.addHandler(ch)
  logger.addHandler(syslogh)

  if isLeader:
    active = isActive()
    while active:
      forceCommit()
      time.sleep(5)
      active = isActive()
    createSnapshot()

if __name__ == '__main__':
  main()