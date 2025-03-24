import os
from dotenv import load_dotenv

load_dotenv()

ASU_ID = os.getenv("ASU_ID")

# AWS constants
AWS_REGION = os.getenv("AWS_REGION")
S3_IN_BUCKET_NAME = f"{ASU_ID}-in-bucket"
S3_OUT_BUCKET_NAME = f"{ASU_ID}-out-bucket"
REQ_QUEUE_NAME = f"{ASU_ID}-req-queue"
RESP_QUEUE_NAME = f"{ASU_ID}-resp-queue"

# server constants
POLL_INTERVAL = 0.2
MAX_WAIT_TIME = 60

# controller constants
MAX_INSTANCES = 15
GRACE_PERIOD = 5