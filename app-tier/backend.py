import os
import boto3
import time
from botocore.exceptions import ClientError
from facenet_pytorch import MTCNN, InceptionResnetV1
from PIL import Image
import torch
from io import BytesIO
from constants import *

s3_client = boto3.client("s3", region_name=AWS_REGION)
sqs_client = boto3.client("sqs", region_name=AWS_REGION)
req_queue_url = sqs_client.get_queue_url(QueueName=REQ_QUEUE_NAME)["QueueUrl"]
resp_queue_url = sqs_client.get_queue_url(QueueName=RESP_QUEUE_NAME)["QueueUrl"]

mtcnn = MTCNN(image_size=240, margin=0, min_face_size=20)
resnet = InceptionResnetV1(pretrained='vggface2').eval()
saved_data = torch.load('data.pt')
embedding_list = saved_data[0]
name_list = saved_data[1]

def face_match(img_bytes):
    img = Image.open(BytesIO(img_bytes))
    with torch.no_grad():
        face, prob = mtcnn(img, return_prob=True)
        emb = resnet(face.unsqueeze(0))
    dist_list = [torch.dist(emb, emb_db).item() for emb_db in embedding_list]
    idx_min = dist_list.index(min(dist_list))
    return (name_list[idx_min], min(dist_list))

def process_requests():
    while True:
        try:
            resp = sqs_client.receive_message(QueueUrl=req_queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=5)
        except ClientError:
            time.sleep(1)
            continue
        messages = resp.get("Messages", [])
        if not messages:
            continue
        for msg in messages:
            file_name = msg["Body"].strip()
            file_key = os.path.splitext(file_name)[0]
            try:
                s3_response = s3_client.get_object(Bucket=S3_IN_BUCKET_NAME, Key=file_name)
                image_data = s3_response["Body"].read()
            except ClientError:
                sqs_client.delete_message(QueueUrl=req_queue_url, ReceiptHandle=msg["ReceiptHandle"])
                continue
            prediction, distance = face_match(image_data)
            try:
                s3_client.put_object(Bucket=S3_OUT_BUCKET_NAME, Key=file_key, Body=prediction)
            except ClientError:
                pass
            message_body = f"{file_key}:{prediction}"
            try:
                sqs_client.send_message(QueueUrl=resp_queue_url, MessageBody=message_body)
            except ClientError:
                pass
            sqs_client.delete_message(QueueUrl=req_queue_url, ReceiptHandle=msg["ReceiptHandle"])
        time.sleep(0.5)

if __name__ == "__main__":
    process_requests()
