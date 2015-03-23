#!/bin/bash

# Update script for montysolr on AWS. This script is run on each ec2-instance.
# Multi-instance control (such as rolling updates) are expected to be managed elsewhere
# This script will block until montysolr services search requests.

TAG=$1

if [ -z "$TAG" ];
then
  echo "TAG not specified. Exit." #Send to logging service when implemented
  exit 1
fi

pushd /adsabs-vagrant/dockerfiles/montysolr
aws s3 cp s3://adsabs-montysolr-etc/author_generated.translit author_generated.translit
aws s3 cp s3://adsabs-montysolr-etc/solrconfig_searcher.xml solrconfig.xml
sed -i 's/TAG=""/TAG='"$TAG"'/' checkout_tag.sh
docker build -t adsabs/montysolr:$TAG .
popd

docker stop montysolr
docker rm montysolr
docker run -d --name montysolr -p 8983:8983 -v /data:/data --restart=on-failure:3 adsabs/montysolr:$TAG

#Poll this instance until it is responsive
while 1;
do
  STATUS=`curl -I -m 3 "http://localhost:8983/solr/select?q=star" | head -n 1 | cut -d$' ' -f2`
  if [ ! -z "$STATUS" ];
    then
    if [ $STATUS == 200 ];
      then
      exit 0
    fi
  fi
  sleep 20
done

exit 1
