# Production AWS Deployment Guide

This guide details the step-by-step procedure to deploy the **AWS Scalable Student Management Platform** on production-grade AWS infrastructure.

---

## Architecture Overview

```mermaid
graph TD
    User([End Users]) -->|HTTPS 443| ALB[Application Load Balancer]
    subgraph VPC [Amazon VPC - 10.0.0.0/16]
        subgraph PublicSubnets [Public Subnets - Multi-AZ]
            ALB
        end
        subgraph PrivateSubnets [Private Subnets - Multi-AZ]
            ECS[ECS Fargate Tasks]
        end
        subgraph IsolatedSubnets [Isolated Subnets - Multi-AZ]
            RDS[(RDS Multi-AZ MySQL)]
        end
    end
    ALB -->|HTTP 5000| ECS
    ECS -->|Read/Write| RDS
    ECS -->|Audit Logs| CW[Amazon CloudWatch Logs]
    ECS -->|Presigned Uploads/Downloads| S3[Amazon S3 Bucket]
```

The application is structured to be **stateless** and highly available:
1. **Network**: Deployed in a custom VPC across two Availability Zones (AZs).
2. **Compute**: ECS Fargate container instances scaled dynamically by an Auto Scaling Group.
3. **Database**: RDS MySQL Multi-AZ for failover readiness.
4. **Storage**: Amazon S3 for student documents, utilizing pre-signed URLs to keep container storage stateless.

---

## 1. Network Infrastructure (VPC)

Create a custom VPC using the AWS Console or CloudFormation:
- **IPv4 CIDR block**: `10.0.0.0/16`
- **Availability Zones**: Choose at least two (e.g., `us-east-1a` and `us-east-1b`).
- **Subnet Layout**:
  - **2 Public Subnets**: For the Application Load Balancer (`10.0.1.0/24`, `10.0.2.0/24`).
  - **2 Private Subnets**: For the ECS Fargate Tasks (`10.0.11.0/24`, `10.0.12.0/24`). Route to NAT Gateways.
  - **2 Isolated Subnets**: For the RDS Database instances (`10.0.21.0/24`, `10.0.22.0/24`). No internet access.

### Security Groups

1. **ALB Security Group (`alb-sg`)**:
   - Inbound: `HTTPS (443)` and `HTTP (80)` from `0.0.0.0/0`.
   - Outbound: `HTTP (5000)` to `ecs-sg`.
2. **ECS Security Group (`ecs-sg`)**:
   - Inbound: `HTTP (5000)` from `alb-sg`.
   - Outbound: `All TCP` to `0.0.0.0/0` (for S3, ECR, and CloudWatch access).
3. **RDS Security Group (`rds-sg`)**:
   - Inbound: `MySQL (3306)` from `ecs-sg`.
   - Outbound: None.

---

## 2. Amazon S3 Storage Setup

Student profile pictures and documents are stored in S3. 

1. **Create Bucket**: E.g., `student-platform-vault-production`.
2. **Block Public Access**: Enable "Block all public access" to keep documents private.
3. **CORS Configuration**: Allow pre-signed uploads and downloads from the web domain. Paste this JSON under **Permissions -> CORS**:
```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
    "AllowedOrigins": ["https://your-student-portal-domain.com"],
    "ExposeHeaders": ["ETag"]
  }
]
```

---

## 3. Database Cluster (RDS MySQL)

1. **Create Subnet Group**: Create a DB Subnet Group including the two isolated subnets.
2. **Launch RDS Instance**:
   - **Engine**: MySQL (8.0.x recommended).
   - **Deployment option**: Production (Multi-AZ DB Instance) for high availability.
   - **DB instance class**: `db.t3.medium` or higher.
   - **Connectivity**: Associate with the DB Subnet Group and select the `rds-sg` security group.
   - **Storage**: Enable autoscaling.
   - **Backup**: Set retention to at least 7 days.

---

## 4. IAM Roles and Policies

Create the following IAM execution and task roles:

### ECS Task Execution Role (`ecsTaskExecutionRole`)
This role allows Fargate to pull the container image from ECR and send logs to CloudWatch.
- Attach managed policy: `AmazonECSTaskExecutionRolePolicy`

### ECS Task Role (`ecsTaskRole`)
This role allows the container itself to access S3 buckets and output custom metrics.
- Attach inline policy for S3 access:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::student-platform-vault-production/*"
    }
  ]
}
```

---

## 5. Containerization & ECS Fargate Deployment

### Build and Push to ECR
1. Create a repository in **Amazon Elastic Container Registry (ECR)**: `student-platform-app`.
2. Login, build, tag, and push the Docker image:
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

docker build -t student-platform-app .

docker tag student-platform-app:latest <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/student-platform-app:latest

docker push <YOUR_AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/student-platform-app:latest
```

### ECS Task Definition
Create a Fargate task definition:
- **Task Role**: `ecsTaskRole`
- **Task Execution Role**: `ecsTaskExecutionRole`
- **CPU**: `0.5 vCPU` | **Memory**: `1 GB`
- **Container Port**: `5000`
- **Environment Variables**:
  - `FLASK_ENV`: `production`
  - `SECRET_KEY`: Keep in AWS Secrets Manager and inject at runtime.
  - `DATABASE_URL`: Inject from AWS Secrets Manager (e.g., `mysql+pymysql://db_user:password@rds-endpoint:3306/student_platform`).
  - `STORAGE_TYPE`: `s3`
  - `S3_BUCKET_NAME`: `student-platform-vault-production`
  - `AWS_DEFAULT_REGION`: `us-east-1`
  - `AWS_LOG_GROUP`: `/ecs/student-platform-app`

---

## 6. Load Balancing & HA (ALB)

1. **Create Target Group**:
   - **Target Type**: IP (required for Fargate).
   - **Protocol**: HTTP | Port: `5000`.
   - **Health Check Path**: `/health` (This triggers our ALB-compliant health endpoint returning `200 OK`).
   - **Thresholds**: Healthy: 2, Unhealthy: 3, Timeout: 5s, Interval: 15s.
2. **Create ALB**:
   - **Scheme**: Internet-facing.
   - **Listeners**:
     - Port `80`: Redirects to port `443` (HTTPS).
     - Port `443`: Associated with an ACM SSL/TLS certificate. Forwarding to the Target Group.
   - **Subnets**: Select the public subnets across AZs.

---

## 7. Auto Scaling Policies

Configure Auto Scaling in the ECS Service:
- **Minimum Tasks**: 2 (Ensures AZ-redundancy).
- **Maximum Tasks**: 10.
- **Scaling Policies**:
  - **CPU Utilization Tracking**: Set target to `70%`. Scale out when average CPU exceeds threshold.
  - **Memory Utilization Tracking**: Set target to `80%`.

---

## 8. CloudWatch Monitoring & Logs

1. **Log Stream**: Logs from container stdout (including database queries and application traces) are forwarded to `/ecs/student-platform-app`.
2. **Alarms**:
   - Set up a CloudWatch Alarm for ALB `UnHealthyHostCount >= 1` to alert on service degradation.
   - Set up billing alarms.
