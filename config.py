#Note: Parent key must be the same as their tags['Name'] value!

AS = {
  'launch_configs': {
    'zookeeper-launchconfig': {
        'image_id': 'ami-018c9568', #ubuntu-trusty-14.04-amd64-server-20140416.1
        'key_name': 'micro',
        'security_groups': ['adsabs-security-group',],
        'instance_type': 't1.micro',
        'instance_monitoring': False,
        'associate_public_ip_address': False,
        'user_data': 
          '''
          #!/bin/bash
          apt-get update
          apt-get install -y python-pip git docker.io
          pip install --upgrade pip boto

          git clone https://github.com/adsabs/adsabs-aws /adsabs-aws
          git clone https://github.com/adsabs/adsabs-vagrant /adsabs-vagrant
          /usr/bin/python  /adsabs-aws/aws_provisioner.py --zookeeper
          service docker.io start
          docker.io build -t adsabs/zookeeper .
          docker.io run -d --name zookeeper -p 2181:2181 -p 2888:2888 -p 3888:3888 -v /zookeeper/:/zookeeper/:rw adsabs/zookeeper
          ''',
    },
  },

  'autoscale_groups':{
    'zookeeper-asg': {
      'launch_config': 'zookeeper-launchconfig',
      'default_cooldown': 300,
      'desired_capacity': 0,
      'max_size': 0,
      'min_size': 0,
      'health_check_period': 300,
      'health_check_type': 'EC2',
      'load_balancers': [],
      'vpc_zone_identifier': ['adsabs-subnet',],
      'tags': [#These tags will be used to instantiate a boto Tag class; these specific keys are expected
        { 
          'key':'Name',
          'value': 'zookeeper-asg',
          'propagate_at_launch':True,
          'resource_id': 'zookeeper-asg', #Must be set to name of this ASG
        },
      ],
    },
  },
}

VPC = {
  'adsabs': {
    'cidr_block': '10.0.0.0/16',
    'tags': {'Name': 'adsabs'},
    'subnets': {
      'adsabs-subnet': {
        'cidr_block':'10.0.0.0/24',
        'tags': {'Name':'adsabs-subnet'},
      },
    },
  },
}


EC2 = {
  'security_groups': {
    'adsabs-security-group': {
      'description': 'standard access from cfa',
      'tags': {'Name': 'adsabs-security-group'},
      'vpc' : 'adsabs',
      'rules': [
        {'ip_protocol':'icmp','from_port':-1,'to_port':-1,'cidr_ip':'10.0.0.0/24'},
        {'ip_protocol':'tcp','from_port':0,'to_port':65535,'cidr_ip':'10.0.0.0/24'},
        {'ip_protocol':'udp','from_port':0,'to_port':65535,'cidr_ip':'10.0.0.0/24'},
        {'ip_protocol':'tcp','from_port':22,'to_port':22,'cidr_ip':'131.142.152.62/32'},
      ],
    },
  },

  'network_interfaces': {
    'zookeeper-eni-1': {
      'subnet': 'adsabs-subnet',
      'description':'ENI associated with zookeeper',
      'tags':{'Name':'zookeeper-eni-1'},
      'private_ip_address': '10.0.0.31',
      'groups': ['adsabs-security-group',],
      'EIP': False,
    },
    'zookeeper-eni-2': {
      'subnet': 'adsabs-subnet',
      'description':'ENI associated with zookeeper',
      'tags':{'Name':'zookeeper-eni-2'},
      'private_ip_address': '10.0.0.32',
      'groups': ['adsabs-security-group',],
      'EIP': False,
    },
    'zookeeper-eni-3': {
      'subnet': 'adsabs-subnet',
      'description':'ENI associated with zookeeper',
      'tags':{'Name':'zookeeper-eni-3'},
      'groups': ['adsabs-security-group',],
      'private_ip_address': '10.0.0.33',
      'EIP': False,
    },    

  },
}



#Not working; policy docs are not formatted correctly (copy/pasted from AWS console)
IAM = {
  'admin': {
    'path': '/',
    'doc': {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Action": "*",
          "Resource": "*"
        },
      ],
    },
  },

  'readonly': {
    'path': '/',
    'doc': {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Action": [
            "appstream:Get*",
            "autoscaling:Describe*",
            "cloudformation:DescribeStacks",
            "cloudformation:DescribeStackEvents",
            "cloudformation:DescribeStackResources",
            "cloudformation:GetTemplate",
            "cloudformation:List*",
            "cloudfront:Get*",
            "cloudfront:List*",
            "cloudtrail:DescribeTrails",
            "cloudtrail:GetTrailStatus",
            "cloudwatch:Describe*",
            "cloudwatch:Get*",
            "cloudwatch:List*",
            "directconnect:Describe*",
            "dynamodb:GetItem",
            "dynamodb:BatchGetItem",
            "dynamodb:Query",
            "dynamodb:Scan",
            "dynamodb:DescribeTable",
            "dynamodb:ListTables",
            "ec2:Describe*",
            "elasticache:Describe*",
            "elasticbeanstalk:Check*",
            "elasticbeanstalk:Describe*",
            "elasticbeanstalk:List*",
            "elasticbeanstalk:RequestEnvironmentInfo",
            "elasticbeanstalk:RetrieveEnvironmentInfo",
            "elasticloadbalancing:Describe*",
            "elastictranscoder:Read*",
            "elastictranscoder:List*",
            "iam:List*",
            "iam:Get*",
            "opsworks:Describe*",
            "opsworks:Get*",
            "route53:Get*",
            "route53:List*",
            "redshift:Describe*",
            "redshift:ViewQueriesInConsole",
            "rds:Describe*",
            "rds:ListTagsForResource",
            "s3:Get*",
            "s3:List*",
            "sdb:GetAttributes",
            "sdb:List*",
            "sdb:Select*",
            "ses:Get*",
            "ses:List*",
            "sns:Get*",
            "sns:List*",
            "sqs:GetQueueAttributes",
            "sqs:ListQueues",
            "sqs:ReceiveMessage",
            "storagegateway:List*",
            "storagegateway:Describe*"
          ],
          "Effect": "Allow",
          "Resource": "*"
        },
      ],
    },
  },
}