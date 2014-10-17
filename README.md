# adsabs-aws
Infrastructure provisioning for AWS/EC2. Requires authentication via IAM profiles (preferred) or `AWS_ACCESS_KEY` and `AWS_SECRET_KEY` set as environmental variables. Essentially, this is a python remote-side implementation of Amazon OpsWorks.

## Components:

#### GlobalProvisioner:

Usage: `python aws_provisioner.py --global`

Creates top-level configuration including:
- VPCs
- subnets
- IAMs+IAM instance profiles
- security groups
- ENIs
- launch configs+associated user-data
- autoscale groups.

Those resources defined in config.py will be created, but never touched if they already exist (even to update). Update by deleting the resources and re-running the provisioner.

#### Zookeeper:
Usage: `python aws_provisioner.py --zookeeper`

Provisions the networking necessary to spin up a single zookeeper on an instance. Zookeeper application provisioning is expected to occur as part of the user-data scripts given to a autoscale group. This component only sets up the networking.

###### Special notes

Zookeeper ensemble requires connection endpoints defined at startup. Once defined, they can't be changed witout restarting the entire ensemble.

Solution:
- Create a pool of pre-defined ENIs with manually specified private IPs
- Attach an unallocated ENI to any new member of the ensemble
- Configure OS-level routing to include the new interface
- Configure myid and zoo.cfg based on the tag:Name and private ip of the ENI, respectively.

#### Solr:
Usage: `python aws_provisioner.py --solr`

Provisions the config files necessary for solr (including information about zookeeper). Like the zookeeper component, application provisioning is offloaded to user-data. Reads the local private IP address (for routing traffic through docker correctly) as well as the zookeeper ENIs to write to /etc/hosts.

Creates an ELB to which any member of solr ASG connects.

Sets up EBS on /data (restores from snapshot if available) based on shardId.

#### Application (docker via ElasticBeanstalk):
Usage: `python aws_provisioner.py --application name path version_string`

- Zips and uploads the application defined in `path` to elastic beanstalk. 
- `name` must coorespond to an EB entry in config.py (which also defines the platform and other deployment specific options). 
- `version_string` is an arbitrary string to tag the version. It must be unique in the context of that app. The zipfile is stored in s3 with `key=version_string`.
- Will always start at least 1 instance. The autoscaling group param in the context of EB does not accept `0`.
