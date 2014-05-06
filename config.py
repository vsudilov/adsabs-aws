#Note: Parent key must be the same as their tags['Name'] value!

AS = {
  'launch_configs': {
    'zookeeper-launchconfig': {
        'image_id': 'ami-018c9568', #ubuntu-trusty-14.04-amd64-server-20140416.1
        'key_name': 'micro',
        'security_groups': ['adsabs-security-group',],
        'instance_type': 't1.micro',
        'instance_monitoring': False,
        'associate_public_ip_address': True,
        'instance_profile_name': 'zookeeper-instanceprofile',
        'user_data': 
          '''#!/bin/bash
          apt-get update
          apt-get install -y python-pip git openjdk-7-jre-headless supervisor language-pack-en-base
          pip install --upgrade pip boto

          export LC_ALL="en_US.UTF-8"
          export JAVA_HOME=/usr/lib/jvm/java-7-openjdk-amd64
          export JMXDISABLE=true
          export JAVA_OPTS="-Xms256m -Xmx512m" #Set default java heap size, very important for good performance

          git clone https://github.com/adsabs/adsabs-aws /adsabs-aws
          git clone https://github.com/adsabs/adsabs-vagrant /adsabs-vagrant
          /usr/bin/python  /adsabs-aws/aws_provisioner.py --zookeeper

          mkdir /zookeeper

          wget -q -O /opt/zookeeper-3.4.6.tar.gz http://apache.mirrors.pair.com/zookeeper/zookeeper-3.4.6/zookeeper-3.4.6.tar.gz
          tar -xzf /opt/zookeeper-3.4.6.tar.gz -C /opt

          cp /adsabs-vagrant/dockerfiles/zookeeper/zoo.cfg /opt/zookeeper-3.4.6/conf/zoo.cfg
          cp /adsabs-vagrant/dockerfiles/zookeeper/myid /zookeeper/myid

          bash /opt/zookeeper-3.4.6/bin/zkServer.sh start
          ''',
    },

    'solr-launchconfig': {
        'image_id': 'ami-018c9568', #ubuntu-trusty-14.04-amd64-server-20140416.1
        'key_name': 'micro',
        'security_groups': ['adsabs-security-group',],
        'instance_type': 't1.micro',
        'instance_monitoring': False,
        'associate_public_ip_address': True,
        'instance_profile_name': 'zookeeper-instanceprofile',
        'user_data': 
          '''#!/bin/bash
          apt-get update
          apt-get install -y python-pip git docker.io dnsmasq-base
          pip install --upgrade pip boto

          git clone https://github.com/adsabs/adsabs-aws /adsabs-aws
          git clone https://github.com/adsabs/adsabs-vagrant /adsabs-vagrant
          /usr/bin/python  /adsabs-aws/aws_provisioner.py --solr
          
          ip link add virtual0 link eth0 type macvlan mode bridge
          #ip address add 10.0.0.0/24 broadcast 10.0.0.255 dev virtual0 #For static IP
          dhclient virtual0
          ip link set virtual0 up
          dnsmasq
          
          pushd /adsabs-vagrant/dockerfiles/solr
          docker.io build -t adsabs/solr .
          docker.io run -d -p 8983:8983 --dns `ip addr show eth0 | grep inet | grep eth0 | awk '{print $2}' | cut -d "/" -f -1` --name solr adsabs/solr
          popd
          EXT_IP=`ip addr show eth0 | grep inet | grep virtual0 | awk '{print $2}' | cut -d "/" -f -1`
          INT_IP=`docker.io inspect solr | grep IPAddress | cut -d '"' -f 4`
          iptables -t nat -N BRIDGE-VIRTUAL0
          iptables -t nat -A PREROUTING -p all -d $EXT_IP -j BRIDGE-VIRTUAL0
          iptables -t nat -A OUTPUT -p all -d $EXT_IP -j BRIDGE-VIRTUAL
          iptables -t nat -A BRIDGE-VIRTUAL0 -p all -j DNAT --to-destination $INT_IP
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
  'solr-asg': {
      'launch_config': 'solr-launchconfig',
      'default_cooldown': 300,
      'desired_capacity': 0,
      'max_size': 0,
      'min_size': 0,
      'health_check_period': 300,
      'health_check_type': 'EC2',
      'load_balancers': ['solr-elb',],
      'vpc_zone_identifier': ['adsabs-subnet',],
      'tags': [#These tags will be used to instantiate a boto Tag class; these specific keys are expected
        { 
          'key':'Name',
          'value': 'solr-asg',
          'propagate_at_launch':True,
          'resource_id': 'solr-asg', #Must be set to name of this ASG
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
  'load_balancers': {
    'solr-elb': {
      'name' : 'solr-elb',
      'zones': None,
      'security_groups': ['adsabs-security-group',],
      'subnets': ['adsabs-subnet',],
      'listeners': [
        (8983,8983,'TCP'),
      ],
    },
  },

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


IAM = {

  'admin': {
    'instance_profiles':['zookeeper-instanceprofile',],
    'policy': {
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
    'instance_profiles':[],
    'policy': {
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