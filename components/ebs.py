import boto
import boto.ec2
import utils
import subprocess

class EBSProvisioner:
  def __init__(self,tag,device='/dev/xvdf',mount='/data'):
    tag = tag.split(':')
    self.tag = {'key':tag[0],'value':tag[1]}
    self.c = utils.connect(boto.ec2.EC2Connection)
    self.this_instance = utils.get_this_instance()
    self.device = device
    self.mount = mount

  def get_ebs_pool(self):
    '''
    Find all detached ENIs by tag, then
    find their associated elastic IPs
    '''
    volumes = self.c.get_all_volumes(
      filters={
        'tag-key':self.tag['key'],
        'tag-value':self.tag['value'],
        'status':'available',
        'availability-zone': self.this_instance.placement,
        }
    )
    return volumes

  def mount_device(self):
    utils.mkdir_p(self.mount)
    cmd = ['mount',self.device,self.mount]
    retval = subprocess.Popen(cmd).wait()
    if retval==0:
      return True

  def update_fstab(self):
    with open('/etc/fstab','r') as fp:
      lines = [L.strip() for L in fp.readlines()]
    L = '{device} {mount} ext4 defaults,nofail 0 2'.format(device=self.device,mount=self.mount)
    if L not in lines:
      lines.append(L)
    with open('/etc/fstab','w') as fp:
      fp.write('\n'.join(lines))


  def format(self):
    cmd = ['file','-s',self.device]
    P = subprocess.Popen(cmd,stdout=subprocess.PIPE)
    retval = P.wait()
    o = P.stdout.readline().strip()
    if '(No such file or directory)' in o or retval != 0:
      return False
    if o == '{device}: data'.format(device=self.device):
      cmd = ['mkfs','-t','ext4',self.device]
      retval = subprocess.Popen(cmd).wait()
      if retval != 0:
        return False
    return True

  def provision(self):

    poller = utils.SyncPollWhileFalse(self.get_ebs_pool,max_tries=2,poll_interval=3)
    ebs_pool = poller.poll()

    if not ebs_pool:
      raise Exception("No suitable EBS volumes were found")

    target = ebs_pool[0]

    poller = utils.SyncPollWhileFalse(
      target.attach,
      f_kwargs={
        'instance_id': self.this_instance.id,
        'device': self.device,
      },
      max_tries = 3,
      poll_interval = 5,
    )
    success = poller.poll()
    if not success:
      raise Exception("Could not attach {ebs}".format(ebs=target.id))

    poller = utils.SyncPollWhileFalse(self.format,max_tries=3,poll_interval=5)
    success = poller.poll()
    if not success:
      raise Exception("Could not format the device")

    poller = utils.SyncPollWhileFalse(self.mount_device,max_tries=3,poll_interval=5)
    success = poller.poll()
    if not success:
      raise Exception("Could mount {dev} on {mnt}".format(dev=self.device,mnt=self.mount))

    self.update_fstab()




