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

  def mount(self):
    utils.mkdir_p(self.mount)
    cmd = ['mount',self.device,self.mount]
    P = subprocess.Popen(cmd)
    P.wait()

  def update_fstab(self):
    with open('/etc/fstab','r') as fp:
      lines = [L.strip() for L in fp.readlines()]

    L = '{device} {mount} ext4 defaults,nofail 0 2'.format(device=self.device,mount=self.mount)
    if L not in lines:
      lines.append(L)

    with open('/etc/fstab','w') as fp:
      fp.write('\n'.join(lines))


  def format(self):
    cmd = ['file','-s',self.mount]
    P = subprocess.Popen(cmd,stdout=subprocess.PIPE)
    P.wait()
    o = P.stdout.readline().strip()
    if o == '{mount}: data'.format(mount=self.mount):
      cmd = ['mkfs','-t','ext4',self.mount]
      P = subprocess.Popen(cmd)
      P.wait()

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

    self.mount()
    self.update_fstab()
    self.format()




