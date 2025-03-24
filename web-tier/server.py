from flask import Flask, request
import boto3
from botocore.exceptions import ClientError
import time
import threading

from constants import *

s3_client = boto3.client("s3", region_name=AWS_REGION)
sqs_client = boto3.client("sqs", region_name=AWS_REGION)
req_queue_url = sqs_client.get_queue_url(QueueName=REQ_QUEUE_NAME)["QueueUrl"]
resp_queue_url = sqs_client.get_queue_url(QueueName=RESP_QUEUE_NAME)["QueueUrl"]

app = Flask(__name__)
results = {}

def poll_responses():
    while True:
        try:
            resp = sqs_client.receive_message(QueueUrl=resp_queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=5)
            messages = resp.get("Messages", [])
            for msg in messages:
                body = msg["Body"]
                if ":" in body:
                    file_key, prediction = body.split(":", 1)
                    results[file_key] = prediction
                sqs_client.delete_message(QueueUrl=resp_queue_url, ReceiptHandle=msg["ReceiptHandle"])
        except Exception:
            pass
        time.sleep(POLL_INTERVAL)

threading.Thread(target=poll_responses, daemon=True).start()

@app.route("/", methods=["POST"])
def get_prediction():
    if "inputFile" not in request.files:
        return "Missing inputFile", 400
    input_file = request.files["inputFile"]
    file_name = input_file.filename
    if not file_name:
        return "Empty filename", 400
    try:
        s3_client.upload_fileobj(input_file, S3_IN_BUCKET_NAME, file_name)
    except ClientError:
        return "Failed to upload file", 500
    file_key = os.path.splitext(file_name)[0]
    try:
        sqs_client.send_message(QueueUrl=req_queue_url, MessageBody=file_name)
    except ClientError:
        return "Failed to send SQS message", 500
    start_time = time.time()
    while time.time() - start_time < MAX_WAIT_TIME:
        if file_key in results:
            prediction = results.pop(file_key)
            return f"{file_key}:{prediction}", 200
        time.sleep(0.5)
    return "Timeout waiting for recognition result", 504

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)
