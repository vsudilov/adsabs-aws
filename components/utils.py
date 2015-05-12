"""
General boto/aws utilities
"""
import os
import errno
import fnmatch
import time

import boto
import boto.ec2
import boto.iam
import boto.utils


def connect(connection_class):
    """
    generalized connect function that accepts a connection class and returns
    the instansiated class. Falls back to environment variables
    `AWS_ACCESS_KEY` and `AWS_SECRET_KEY` if an IAM role isn't present
    :param connection_class: boto connection class
    :return: instansiated connection class
    """
    try:
        return connection_class()
    except boto.exception.NoAuthHandlerFound:
        _id = os.environ.get('AWS_ACCESS_KEY', None)
        key = os.environ.get('AWS_SECRET_KEY', None)
    return connection_class(aws_access_key_id=_id, aws_secret_access_key=key)


def get_instance_tag_value(key):
    """
    Returns the value associated with the current instance's tag based on the
    key
    :param key: aws tag key
    :return: value associated with `key`
    """
    this_instance = get_this_instance()
    try:
        return this_instance.tags[key]
    except KeyError:
        raise KeyError('A tag named "{key}" on {instance} does not '
                       'exist'.format(key=key, instance=this_instance.id))


def find_partner_private_ip(tag):
    """
    Find and return the private IP address from the first instance tagged
    by @param `tag` that is not the current instance. If multiple instances
    are found that meet this criteria, return just the first one's ip addr

    :param tag: full tag pair in the form "key:value"
    :type tag: basestring
    :return: peer private ip
    :rtype basestring
    """
    key, value = tag.split(':')
    c = connect(boto.ec2.connection.EC2Connection)
    instances = c.get_only_instances(
        filters={
            'tag-key': key,
            'tag-value': value,
            'instance-state-name': 'running',
        }
    )
    this_instance = get_this_instance()
    peers = filter(lambda i: i.id != this_instance.id, instances)
    return peers[0].private_ip_address


def get_account_id():
    """return the account id associated with this instance/connection"""
    c = connect(boto.iam.connection.IAMConnection)
    return c.get_user()['get_user_response']['get_user_result']['user']['arn'].split(':')[4]


def get_this_instance():
    """
    Return the instance that is running this script
    :return: this instance
    :rtype: boto instance object
    """
    c = connect(boto.ec2.connection.EC2Connection)
    metadata = boto.utils.get_instance_metadata()
    this_instance = next(i for i in c.get_only_instances() if i.id == metadata['instance-id'])
    return this_instance


def find_r(path, pattern):
    """
    recursive find, much like linux's `find -name` command
    :param path: base path to recursively search
    :param pattern: glob file pattern
    :return: filenames matching pattern
    """
    matches = []
    for root, dirnames, filenames in os.walk(path):
        for filename in fnmatch.filter(filenames, pattern):
            matches.append(os.path.join(root, filename))
    return matches


def get_eni_publicIP(instance=None):
    """
    Get the most probable public IP of this instance:
    if this_instance has multiple ENIs, get the ENI that
    a) has a public IP
    b) does not match this_instance.ip (since this will be bound to the default IP
    """
    if instance is None:
        instance = get_this_instance()
    enis = [i for i in instance.interfaces if i.publicIp and i.publicIp != instance.ip_address]
    if len(enis) > 1:
        raise Exception("I don't know what to do when multiple ENIs each with public IPs are attached!")
    return enis[0].publicIp


def mkdir_p(path):
    """
    mkdir -p functionality
    :param path: path to create
    :return: None
    """
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


class cd:
    """Context manager for changing the current working directory"""
    def __init__(self, new_path):
        self.newPath = new_path

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


class SyncPollWhileFalse:
    """
    Class that enables the (blocking) polling of a function until
    it returns a value that evaluates to True
    """
    def __init__(self, f, f_args=[], f_kwargs={},
                 max_tries=5, poll_interval=2):
        self.f = f
        self.f_args = f_args
        self.f_kwargs = f_kwargs
        self.max_tries = max_tries
        self.poll_interval = poll_interval

    def poll(self):
        """
        Main polling loop
        """
        tries = 0
        while 1:
            tries += 1
            result = self.f(*self.f_args,**self.f_kwargs)
            if result or tries >= self.max_tries:
                return result
            time.sleep(self.poll_interval)


