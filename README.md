# adsabs-aws
Infrastructure provisioning for AWS/EC2.

### Components:

#### GlobalProvisioner:  

Idempotent usage: `python aws_provisioner.py --global_provision`

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
Idempotent usage: `python aws_provisioner.py --zookeeper`

Provisions the networking necessary to spin up a zookeeper on an instance. Zookeeper application provisioning is expected to occur as part of the user-data scripts.

###### Why a special provisioner?  

Zookeeper ensemble requires connection endpoints defined at startup. Once defined, they can't be changed witout restarting the entire ensemble.

Solution:
- Create a pool of pre-defined ENIs with manually specified private IPs
- Attach an unallocated ENI to any new member of the ensemble 
- Configure OS-level routing to include the new interface
- Configure myid and zoo.cfg based on the tag:Name and private ip of the ENI, respectively.
