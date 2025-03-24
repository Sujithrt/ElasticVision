import boto3
import time
from botocore.exceptions import ClientError
from constants import *

sqs_client = boto3.client("sqs", region_name=AWS_REGION)
ec2_client = boto3.client("ec2", region_name=AWS_REGION)
ec2_resource = boto3.resource("ec2", region_name=AWS_REGION)
req_queue_url = sqs_client.get_queue_url(QueueName=REQ_QUEUE_NAME)["QueueUrl"]

last_nonzero_time = time.time()
over_capacity_start = None

def get_queue_length():
    attrs = sqs_client.get_queue_attributes(QueueUrl=req_queue_url, AttributeNames=["ApproximateNumberOfMessages"])
    return int(attrs["Attributes"].get("ApproximateNumberOfMessages", 0))

def get_preprovisioned_instances():
    filters = [{"Name": "tag:Name", "Values": ["app-tier-instance-*"]},
               {"Name": "instance-state-name", "Values": ["stopped", "pending", "running"]}]
    return list(ec2_resource.instances.filter(Filters=filters))

def scale():
    global last_nonzero_time, over_capacity_start
    while True:
        qlen = get_queue_length()
        instances = get_preprovisioned_instances()
        active = [i for i in instances if i.state["Name"] in ["running", "pending"]]
        stopped = [i for i in instances if i.state["Name"] == "stopped"]
        print(f"Pending requests: {qlen}, Active instances: {len(active)}")
        if qlen > 0:
            last_nonzero_time = time.time()
        desired = min(qlen, MAX_INSTANCES)
        if len(active) < desired:
            needed = desired - len(active)
            over_capacity_start = None
            if needed > 0 and stopped:
                instance_ids = [i.id for i in stopped[:needed]]
                print(f"Starting instances: {instance_ids}")
                try:
                    ec2_client.start_instances(InstanceIds=instance_ids)
                except ClientError as e:
                    print(f"Error starting instances {instance_ids}: {e}")
        elif len(active) > desired:
            if over_capacity_start is None:
                over_capacity_start = time.time()
            elif time.time() - over_capacity_start >= GRACE_PERIOD:
                to_stop = active[desired:]
                instance_ids = [i.id for i in to_stop]
                if instance_ids:
                    print(f"Stopping instances: {instance_ids}")
                    try:
                        ec2_client.stop_instances(InstanceIds=instance_ids)
                    except ClientError as e:
                        print(f"Error stopping instances {instance_ids}: {e}")
        else:
            over_capacity_start = None
        time.sleep(2)

if __name__ == "__main__":
    scale()
