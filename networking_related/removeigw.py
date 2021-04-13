import boto3, click
region = 'us-east-1'


gw_list = ['igw-095b5b9a49260e8fa']
vpc_list = ['vpc-04fdafaa6954147ee']



def igw_remover(gw_id,vpc_id, region):
    ec2client = boto3.client('ec2', region_name=region,)
    ec2 = boto3.resource('ec2', region_name=region, )
    internet_gateway = ec2.InternetGateway(gw_id)
    vpc = ec2.Vpc(vpc_id)
    waiter = ec2client.get_waiter('instance_terminated')

    try:
        internet_gateway.detach_from_vpc(VpcId=vpc_id, DryRun=False)
        print(f'detached {gw_id}')

    except Exception as e:
        print(f'Errors: {(e)} \n')
        try:
            if 'has some mapped public address(es)' in str(e):
                for subnets in vpc.subnets.all():
                    for subnet in vpc.subnets.filter(SubnetIds=[subnets.id]):
                        if subnet.tags is None:
                            continue
                        for tag in subnet.tags:
                            if tag['Key'] == 'Network' and tag['Value'] == 'Public':
                                print(f'removing {subnet.id}  \n \r ')
                                if click.confirm('Do you want to continue?'):
                                    subnet.delete()
                                    print(f'deleted {subnet.id}')

        except Exception as e:
            print(f'{subnet.id}  {(e)}')
            print(f'Deleting the instance Attached to the gateway \n')
            instance = ec2client.describe_instances(Filters=[{ 'Name': 'network-interface.subnet-id', 'Values': [ subnet.id ]}])
            instanceId = (instance['Reservations'][0]['Instances'][0]['InstanceId'])
            print(f"The instance {instanceId} is running under the subnet {subnet.id} \n")
            if click.confirm(f'Do you want to Delete {instanceId} ? '):
                ec2client.terminate_instances(InstanceIds=[instanceId])
                waiter.wait(Filters=[{ 'Name': 'network-interface.subnet-id', 'Values': [ subnet.id ]}], InstanceIds=[instanceId])
                print(f'deleted {instanceId}')

                        
    else:
        internet_gateway.delete()
        print(f'deleted {gw_id}')   


if __name__ == '__main__':

    for gw_id in gw_list:
        for vpc_id in vpc_list:
            igw_remover(gw_id, vpc_id, region,)



