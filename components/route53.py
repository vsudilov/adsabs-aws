import boto
import boto.route53
import boto.ec2
import utils


class Route53Provisioner:
    """
    route53 provisioner class
    """
    def __init__(self, zone):
        self.zone = zone
        self.conn = utils.connect(boto.route53.Route53Connection)

    def provision(self):
        """
        Provision route53 A records based on the tag "Name" of all instances
        in the network.
          - Assumes private housted route53 zone
          - instances without a "Name" tag are silently skipped
          - instances not in a 'running' state are silently skipped
          - creates A record based on the "Name" tag
          - an A record may contain multiple private IPs

        :return: None
        """
        zone = self.conn.get_zone(self.zone)
        assert zone, "No hosted zones found"

        # Group instances by their tag "Name"
        instances = utils.connect(boto.ec2.EC2Connection).get_only_instances(
            filters={
                'instance-state-name': 'running',
                'vpc-id': utils.get_this_instance().vpc_id
            }
        )
        network_map = {}
        for instance in instances:
            name = instance.tags.get('Name').lower()
            if name is None:
                continue
            if name not in network_map:
                network_map[name] = []
            network_map[name].append(instance.private_ip_address)

        current_records = {
            r.name.replace(self.zone, '').strip('.'): r
            for r in zone.get_records()
        }

        # Create any new records
        for new_record_name in set(network_map).difference(current_records):
            zone.add_a(
                name='{0}.{1}'.format(new_record_name, self.zone),
                value=network_map.pop(new_record_name),  # list is safe to pass
                ttl=30,
            )

        # Update any records that need to be updated
        for update_record_name in network_map.keys():
            record_value = network_map.pop(update_record_name)
            if set(current_records[update_record_name].resource_records) != \
                    set(record_value):
                zone.update_a(
                    name='{0}.{1}'.format(update_record_name, self.zone),
                    value=record_value,
                    ttl=30,
                )

        assert len(network_map) == 0, "network_map has unused " \
                                      "entries: {0}".format(network_map)