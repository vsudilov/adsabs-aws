SolrCloud = {
  'shards': 2,
  'replication_factor': 2,
}

#Note: Parent key must be the same as their tags['Name'] value!
AS = {
  'launch_configs': {
    'zookeeper-launchconfig': {
        'image_id': 'ami-80778be8',
        'key_name': 'micro',
        'security_groups': ['adsabs-security-group',],
        'instance_type': 't1.micro',
        'instance_monitoring': False,
        'associate_public_ip_address': True,
        'instance_profile_name': 'zookeeper-instanceprofile',
        'user_data': 
          '''#!/bin/bash
          apt-get update
          apt-get install -y python-pip git openjdk-7-jre-headless supervisor language-pack-en-base python-dev docker.io
          pip install --upgrade pip boto fabric
          ln -s /usr/bin/docker.io /usr/bin/docker

          export LC_ALL="en_US.UTF-8"
          export JAVA_HOME=/usr/lib/jvm/java-7-openjdk-amd64
          export JMXDISABLE=true
          export JAVA_OPTS="-Xms256m -Xmx512m" #Set default java heap size, very important for good performance

          git clone https://github.com/adsabs/adsabs-aws /adsabs-aws
          git clone https://github.com/adsabs/adsabs-vagrant /adsabs-vagrant
          #git clone https://github.com/adsabs/adslogging-forwarder /adslogging-forwarder

          /usr/bin/python  /adsabs-aws/aws_provisioner.py --zookeeper
          #/usr/bin/python  /adsabs-aws/aws_provisioner.py --adslogging-forwarder
          #bash /SET_LOGSTASH_SERVER.bash

          #pushd /adslogging-forwarder
          #fab build
          #fab run:LOGSTASH_SERVER=$LOGSTASH_SERVER
          #popd

          mkdir /zookeeper

          wget -q -O /opt/zookeeper-3.4.6.tar.gz http://apache.mirrors.pair.com/zookeeper/zookeeper-3.4.6/zookeeper-3.4.6.tar.gz
          tar -xzf /opt/zookeeper-3.4.6.tar.gz -C /opt

          ln -sf /adsabs-vagrant/dockerfiles/zookeeper/zookeeper-env.sh /opt/zookeeper-3.4.6/conf/zookeeper-env.sh
          ln -sf /adsabs-vagrant/dockerfiles/zookeeper/zoo.cfg /opt/zookeeper-3.4.6/conf/zoo.cfg
          ln -sf /adsabs-vagrant/dockerfiles/zookeeper/myid /zookeeper/myid
          ln -sf /adsabs-vagrant/dockerfiles/zookeeper/zk.sh /zk.sh
          ln -sf /adsabs-vagrant/dockerfiles/zookeeper/supervisord.conf /etc/supervisor/supervisord.conf

          service supervisor stop
          service supervisor start
          ''',
    },

    'montysolr-launchconfig': {
#        'image_id': 'ami-018c9568', #ubuntu-trusty-14.04-amd64-server-20140416.1
#        'image_id': 'ami-a6926dce', #Ubuntu Server 14.04 LTS (HVM), 
        'image_id': 'ami-80778be8', #Ubuntu Server 14.04 LTS (PV), SSD Volume Type - 
        'key_name': 'micro',
        'security_groups': ['adsabs-security-group',],
        'instance_type': 'm3.large',
#        'instance_type': 't1.micro',
        'instance_monitoring': False,
        'associate_public_ip_address': True,
        'instance_profile_name': 'zookeeper-instanceprofile',
        'user_data': 
          '''#!/bin/bash
          apt-get update
          apt-get install -y python-pip git docker.io dnsmasq-base bridge-utils udhcpc python-dev
          pip install --upgrade pip boto requests fabric
          ln -s /usr/bin/docker.io /usr/bin/docker

          git clone https://github.com/adsabs/adsabs-aws /adsabs-aws
          git clone https://github.com/adsabs/adsabs-vagrant /adsabs-vagrant
          git clone https://github.com/adsabs/adslogging-forwarder /adslogging-forwarder

          #ln -sf /adsabs-aws/etc/backup-daily.py /etc/cron.daily/backup-daily.py
          pushd /adsabs-vagrant/dockerfiles/montysolr
          /usr/bin/python  /adsabs-aws/aws_provisioner.py --solr
          popd
          #/usr/bin/python  /adsabs-aws/aws_provisioner.py --adslogging-forwarder
          #bash /SET_LOGSTASH_SERVER.bash

          #pushd /adslogging-forwarder
          #fab build
          #fab run:LOGSTASH_SERVER=$LOGSTASH_SERVER
          #popd
          
          HOST_IP=`ip addr show eth0 | grep inet | grep eth0 | awk '{print $2}' | cut -d "/" -f -1`
          iptables -t nat -A POSTROUTING -p tcp --dport 8983 -o eth0 -j SNAT --to-source $HOST_IP
          dnsmasq
          
          pushd /adsabs-vagrant/dockerfiles/montysolr          
          docker build -t adsabs/montysolr .
          docker run -d -p 8983:8983 --dns $HOST_IP --name montysolr -v /data:/data adsabs/montysolr
          popd
          ''',
    },

    'adslogging-launchconfig': {
        'image_id': 'ami-018c9568', #ubuntu-trusty-14.04-amd64-server-20140416.1
        'key_name': 'micro',
        'security_groups': ['adsabs-security-group',],
        'instance_type': 'm1.medium',
        'instance_monitoring': False,
        'associate_public_ip_address': True,
        'instance_profile_name': 'zookeeper-instanceprofile',
        'user_data': 
          '''#!/bin/bash
          apt-get update
          apt-get install -y python-pip git docker.io python-dev
          pip install --upgrade pip boto requests fabric
          ln -s /usr/bin/docker.io /usr/bin/docker

          git clone https://github.com/adsabs/adsabs-aws /adsabs-aws
          git clone https://github.com/adsabs/adslogging /adslogging

          /usr/bin/python  /adsabs-aws/aws_provisioner.py --adslogging

          pushd /adslogging
          pip install -r requirements.txt
          fab all build
          fab data:yes
          fab all run
          popd
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
    'montysolr-asg': {
      'launch_config': 'montysolr-launchconfig',
      'default_cooldown': 300,
      'desired_capacity': 0,
      'max_size': 0,
      'min_size': 0,
      'health_check_period': 900,
      'health_check_type': 'ELB',
      'load_balancers': ['solr-elb',],
      'vpc_zone_identifier': ['adsabs-subnet',],
      'tags': [#These tags will be used to instantiate a boto Tag class; these specific keys are expected
        { 
          'key':'Name',
          'value': 'montysolr-asg',
          'propagate_at_launch':True,
          'resource_id': 'montysolr-asg', #Must be set to name of this ASG
        },
      ],
    },
    'adslogging-asg': {
      'launch_config': 'adslogging-launchconfig',
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
          'value': 'adslogging-asg',
          'propagate_at_launch':True,
          'resource_id': 'adslogging-asg', #Must be set to name of this ASG
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
        'availability_zone': 'us-east-1c',
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
      'health_check': {
        'interval': 20,
        'healthy_threshold': 3,
        'unhealthy_threshold': 5,
        'target': 'HTTP:8983/solr/',
      }
    },
  },

  'volumes': {
    'solr-data-volume': {
      'number': SolrCloud['replication_factor']*SolrCloud['shards'],
      'zone': 'us-east-1c',
      'volume_type': 'gp2',
      'size': 600/SolrCloud['shards'], #size in GB
      'tags': {'Name': 'solr-data-volume'},
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


S3 = {
  's3-adsabs-beer': {
    'headers': None,
    'location': '',
    'policy': None,
  },
  's3-adsabs-bumblebee': {
    'headers': None,
    'location': '',
    'policy': None,
  },
  's3-adsabs-adslogging': {
    'headers': None,
    'location': '',
    'policy': None,
  }

}

EB = {
  # 'beer-test': {
  #   'application_name': 'beer-test',
  #   'description': '''Flask labs 2.0''',
  #   's3_bucket': 's3-beer',
  #   'app_config_file': 'local_config.py', #Will exit if this file isn't (recursively) found
  #   'auto_create_application': False,
  #   'environment': {
  #     'environment_name': 'default-docker-env',
  #     'solution_stack_name': '64bit Amazon Linux 2014.03 v1.0.1 running Docker 1.0.0',
  #     'option_settings': [
  #       ('aws:autoscaling:asg','MinSize',1),
  #       ('aws:autoscaling:asg','MaxSize',1),
  #       ('aws:autoscaling:launchconfiguration','InstanceType','t1.micro'),
  #     ],
  #   },

  'bumblebee': {
    'application_name': 'bumblebee',
    'description': '''Bumblebee-ADS''',
    's3_bucket': 's3-bumblebee',
    'app_config_file': 'local-config.json', #Will exit if this file isn't (recursively) found
    'auto_create_application': False,
    'environment': {
      'environment_name': 'adsabs-bumblebee-demo',
      'solution_stack_name': '64bit Amazon Linux 2014.03 v1.0.1 running Docker 1.0.0',
      'option_settings': [
        ('aws:autoscaling:asg','MinSize',1),
        ('aws:autoscaling:asg','MaxSize',1),
        ('aws:autoscaling:launchconfiguration','InstanceType','t1.micro'),
        ('aws:autoscaling:launchconfiguration','Ec2KeyName', 'micro'),
        ('aws:elasticbeanstalk:command','Timeout',1800),
        #('aws:elasticbeanstalk:sns:topics','Notification Endpoint','vsudilovsky@cfa.harvard.edu')
      ],
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
