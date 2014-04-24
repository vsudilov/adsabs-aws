# adsabs-aws
Infrastructure provisioning designed to be called via cloud-init on AWS/EC2/.

Top-level configuration is assumed to be already in place. This include subnets, IAMs, security groups, and autoscale groups.

### Components:
#### Zookeeper:


###### The problem:
Zookeeper ensemble requires connection endpoints defined at startup. Once defined, they can't be changed witout restarting the entire ensemble.

###### Solution:
- Use elastic IPs (1 EIP for 1 zookeeper)
- Attach an EIP to any new member of the ensemble 
- zoo.cfg points to the public_dns_hostname as specified by AWS on EIP assignment.
- On the VPC network, hostname resolution doesn't require talking to the internet; This behavior is up to AWS, which hopefully shouldn't change
- See [here](http://alestic.com/2009/06/ec2-elastic-ip-internal) and [here](http://stackoverflow.com/questions/5499671/how-do-i-know-the-internal-dns-name-of-an-amazon-aws-instance) for more details about this solution
