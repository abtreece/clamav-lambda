import socket, boto3

HOSTNAME = "database.clamav.net"
EGRESS_PORT = 80
SECURITY_GROUP_TAGS = { 'Name': 'clamav-updates' }


def lambda_handler(event, context):
    new_cidrs = get_ips()
    result = update_security_group(new_cidrs)

    return result


def get_ips():
    try:
        host = socket.gethostbyname_ex(HOSTNAME)
        ip_addrs = host[2]

        ip_list = list()

        for ip in ip_addrs:
            ip_list.append(ip + '/32')

        return ip_list

    except socket.gaierror, err:
        print "cannot resolve hostname: ", name, err


def update_security_group(new_cidrs):
    client = boto3.client('ec2')

    groups = get_security_group(client)
    print ('Found ' + str(len(groups)) + ' Security Group to update')

    result = list()

    for group in groups:
        if update_group_permissions(client, group, new_cidrs, EGRESS_PORT):
            result.append('Updated ' + group['GroupId'])

    return result


def update_group_permissions(client, group, new_cidrs, port):
    added = 0
    removed = 0

    if len(group['IpPermissionsEgress']) > 1:
        for permission in group['IpPermissionsEgress']:
            old_prefixes = list()
            to_revoke = list()
            to_add = list()
            for range in permission['IpRanges']:
                cidr = range['CidrIp']
                old_prefixes.append(cidr)
                if new_cidrs.count(cidr) == 0:
                    to_revoke.append(range)
                    print(group['GroupId'] + ": Revoking " + cidr + ":" + str(permission['FromPort']))
            
            for cidr in new_cidrs:
                if old_prefixes.count(cidr) == 0:
                    to_add.append({ 'CidrIp': cidr })
                    print(group['GroupId'] + ": Adding " + cidr + ":" + str(permission['FromPort']))
            
            removed += revoke_permissions(client, group, permission, to_revoke)
            added += add_permissions(client, group, permission, to_add)

    else:
        to_add = list()
        for cidr in new_cidrs:
            to_add.append({ 'CidrIp': cidr })
            print(group['GroupId'] + ": Adding " + cidr + ":" + str(port))
        permission = { 'FromPort': port, 'ToPort': port, 'IpProtocol': 'tcp'}
        added += add_permissions(client, group, permission, to_add)
 
    print (group['GroupId'] + ": Added " + str(added) + ", Revoked " + str(removed))
    return (added > 0 or removed > 0)

 
def revoke_permissions(client, group, permission, to_revoke):
    if len(to_revoke) > 0:
        revoke_params = {
            'FromPort': permission['FromPort'],
            'ToPort': permission['ToPort'],
            'IpRanges': to_revoke,
            'IpProtocol': permission['IpProtocol']
        }
        
        client.revoke_security_group_egress(GroupId=group['GroupId'], IpPermissions=[revoke_params])
        
    return len(to_revoke)
    

def add_permissions(client, group, permission, to_add):
    if len(to_add) > 0:
        add_params = {
            'FromPort': permission['FromPort'],
            'ToPort': permission['ToPort'],
            'IpRanges': to_add,
            'IpProtocol': permission['IpProtocol']
        }
        
        client.authorize_security_group_egress(GroupId=group['GroupId'], IpPermissions=[add_params])
        
    return len(to_add)


def get_security_group(client):
    filters = list();
    for key, value in SECURITY_GROUP_TAGS.iteritems():
        filters.extend(
            [
                { 'Name': "tag-key", 'Values': [ key ] },
                { 'Name': "tag-value", 'Values': [ value ] }
            ]
        )
 
    response = client.describe_security_groups(Filters=filters)
    
    return response['SecurityGroups']
