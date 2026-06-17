import os
import uuid
import boto3
from botocore.exceptions import ClientError
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

class StorageService:
    def upload_file(self, file: FileStorage, folder: str = '') -> str:
        """Uploads a file and returns its path or key."""
        raise NotImplementedError
        
    def get_file_url(self, file_path: str) -> str:
        """Returns a URL to access the file."""
        raise NotImplementedError
        
    def delete_file(self, file_path: str) -> bool:
        """Deletes a file from storage."""
        raise NotImplementedError


class LocalStorageService(StorageService):
    def __init__(self, upload_folder: str):
        self.upload_folder = upload_folder
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)
            
    def upload_file(self, file: FileStorage, folder: str = '') -> str:
        filename = secure_filename(file.filename)
        # Prevent collisions by appending a UUID
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        
        target_dir = os.path.join(self.upload_folder, folder)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
            
        file_path = os.path.join(target_dir, unique_name)
        file.save(file_path)
        
        # Return a relative path for storing in DB
        return os.path.join(folder, unique_name) if folder else unique_name
        
    def get_file_url(self, file_path: str) -> str:
        # Returns relative URL matching static uploads folder route
        # Clean up path representation for URLs
        clean_path = file_path.replace('\\', '/')
        return f"/static/uploads/{clean_path}"
        
    def delete_file(self, file_path: str) -> bool:
        full_path = os.path.join(self.upload_folder, file_path)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
                return True
            except OSError:
                return False
        return False


class S3StorageService(StorageService):
    def __init__(self, aws_access_key: str, aws_secret_key: str, region: str, bucket_name: str):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )
        self.region = region

    def upload_file(self, file: FileStorage, folder: str = '') -> str:
        filename = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        s3_key = f"{folder}/{unique_name}" if folder else unique_name
        
        try:
            # S3 client upload_fileobj accepts stream
            self.s3_client.upload_fileobj(
                file.stream,
                self.bucket_name,
                s3_key,
                ExtraArgs={'ContentType': file.content_type}
            )
            return s3_key
        except ClientError as e:
            print(f"S3 Upload failed: {e}")
            raise e

    def get_file_url(self, file_path: str) -> str:
        try:
            # Generate pre-signed URL valid for 1 hour to secure files
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_path},
                ExpiresIn=3600
            )
            return url
        except ClientError as e:
            print(f"Error generating pre-signed S3 URL: {e}")
            # Fallback to standard URL structure if credentials fail
            return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{file_path}"

    def delete_file(self, file_path: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_path)
            return True
        except ClientError as e:
            print(f"S3 Delete failed: {e}")
            return False


def get_storage_service(config) -> StorageService:
    if config.STORAGE_TYPE == 's3':
        return S3StorageService(
            aws_access_key=config.AWS_ACCESS_KEY_ID,
            aws_secret_key=config.AWS_SECRET_ACCESS_KEY,
            region=config.AWS_REGION,
            bucket_name=config.S3_BUCKET_NAME
        )
    else:
        return LocalStorageService(upload_folder=config.UPLOAD_FOLDER)
