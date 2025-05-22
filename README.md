# Elastic Face Recognition Application

## Overview

This project implements a multi-tier, elastic face recognition application using AWS IaaS services. The system is designed to handle variable workloads by dynamically scaling its compute resources while minimizing costs. The architecture is divided into three main components:

- **Web Tier:**  
  A Flask-based web server (server.py) that handles incoming HTTP POST requests. When a user submits an image file, the server:
  - Extracts the image from the request.
  - Uploads the image to an S3 bucket (named `<ASU_ID>-in-bucket`).
  - Sends a request message (containing the file name) to an SQS request queue (named `<ASU_ID>-req-queue`).
  - Waits for the processing result on an SQS response queue (named `<ASU_ID>-resp-queue`).
  - Returns the result to the user in the format `<filename>:<prediction>`.

- **Application Tier:**  
  A set of EC2 instances (scaling between 0 and 15) that process the face recognition requests. Each instance:
  - Polls the SQS request queue to retrieve a file name.
  - Downloads the corresponding image from the S3 input bucket.
  - Runs a face recognition model to predict the identity in the image.
  - Uploads the prediction result to an S3 output bucket.
  - Sends the result back to the SQS response queue.
  
  The key design point is that each instance processes one request at a time, and the system scales out (up to a maximum of 15 instances) during heavy load, then scales in to 0 when there are no pending requests.

- **Autoscaling Controller:**  
  A custom autoscaling solution (controller.py) that monitors the SQS request queue and adjusts the number of running application-tier EC2 instances accordingly:
  - When the request queue grows, it starts additional pre-provisioned instances.
  - When the queue is empty for a sustained period, it stops excess instances.
  - The controller uses a "grace period" to avoid premature scale-in, ensuring that transient dips in workload do not cause unnecessary shutdowns.

Overall, the application leverages AWS S3 for storage, SQS for decoupled messaging, and EC2 for computing resources. The design demonstrates how to build a responsive and cost-effective cloud application using a custom autoscaling solution, with infrastructure provisioned via AWS CDK.

## Required AWS Resources

- **S3 Buckets:**  
  - **Input Bucket:** `<ASU_ID>-in-bucket` – stores the images submitted for face recognition.  
  - **Output Bucket:** `<ASU_ID>-out-bucket` – stores the recognition results.

- **SQS Queues:**  
  - **Request Queue:** `<ASU_ID>-req-queue` – receives the file names of images to be processed (max message size: 1 KB).  
  - **Response Queue:** `<ASU_ID>-resp-queue` – receives the face recognition results.

- **EC2 Instances:**  
  - **Web-tier Instance:** A single instance (named "web-instance") running the Flask server (via Gunicorn) with a static Elastic IP.  
  - **Application-tier Instances:** A group of instances that can scale from 0 to 15 based on load, each processing one request at a time.

- **IAM Roles & Policies:**  
  - An IAM role for the web-tier instance with policies granting access to S3, SQS, and read-only access to EC2.

## System Architecture
![image](https://github.com/user-attachments/assets/d88bc73f-c109-42e1-9a47-9b38b1e300da)

