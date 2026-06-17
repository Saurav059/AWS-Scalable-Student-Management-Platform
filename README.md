# AWS Scalable Student Management Platform

A Flask-based student management platform designed for local development with SQLite or MySQL and production deployment on AWS using ECS Fargate, RDS MySQL, S3, and an Application Load Balancer.

## Features

- Role-based authentication for admins, teachers, and students
- Student, teacher, and course management
- Attendance recording and reporting
- Marks and grade tracking
- Document upload support with local storage or S3
- REST API routes for platform data
- AWS-ready health check endpoint at `/health`

## Tech Stack

- Python 3 / Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-Bcrypt
- SQLite for local default storage
- MySQL for Docker and AWS production-style runs
- Boto3 for S3 document storage
- Docker and Docker Compose

## Local Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a local environment file:

```bash
cp .env.example .env
```

Run the app:

```bash
python run.py
```

Open the app at:

```text
http://127.0.0.1:5000/
```

## Seed Data

The app creates database tables automatically on startup. To load sample users, courses, attendance, and marks:

```bash
python seed.py
```

Sample login credentials:

```text
Admin   : admin@university.edu / Admin@123
Teacher : teacher1@university.edu / Teacher@123
Student : student1@university.edu / Student@123
```

## Docker Compose

Start the Flask app with a MySQL container:

```bash
docker compose up --build
```

The web app will be available at:

```text
http://127.0.0.1:5000/
```

The MySQL service runs on port `3306` with the development credentials defined in `docker-compose.yml`.

## Environment Variables

Important settings are documented in `.env.example`:

- `SECRET_KEY`
- `JWT_SECRET_KEY`
- `DATABASE_URL`
- `STORAGE_TYPE`
- `UPLOAD_FOLDER`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `S3_BUCKET_NAME`

Use `STORAGE_TYPE=local` for local uploads and `STORAGE_TYPE=s3` for AWS S3-backed document storage.

## AWS Deployment

See `AWS_DEPLOYMENT.md` for the production architecture and deployment steps covering:

- VPC and subnet layout
- Security groups
- S3 document storage
- RDS MySQL
- ECS Fargate
- Application Load Balancer
- Auto Scaling
- CloudWatch monitoring

## Repository Notes

Local runtime files are intentionally ignored, including `.env`, Python cache files, uploaded files, and the SQLite `instance/` directory.
