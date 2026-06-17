from datetime import date
from typing import List, Optional, Dict, Any
from werkzeug.datastructures import FileStorage
from app.database import db
from app.models import Student, User, Document
from app.services.auth_service import AuthService
from app.services.storage_service import StorageService
from app.services.audit_service import AuditService

class StudentService:
    def __init__(self, storage_service: StorageService):
        self.storage = storage_service

    def get_all_students(self) -> List[Student]:
        return Student.query.all()

    def get_student_by_id(self, student_id: int) -> Optional[Student]:
        return Student.query.get(student_id)

    def get_student_by_student_code(self, student_code: str) -> Optional[Student]:
        return Student.query.filter_by(student_id=student_code).first()

    def get_student_by_user_id(self, user_id: int) -> Optional[Student]:
        return Student.query.filter_by(user_id=user_id).first()

    def search_students(self, query: str) -> List[Student]:
        """Search students by ID, Name, Department, or Program."""
        if not query:
            return self.get_all_students()
            
        search_pattern = f"%{query}%"
        return Student.query.filter(
            (Student.student_id.like(search_pattern)) |
            (Student.first_name.like(search_pattern)) |
            (Student.last_name.like(search_pattern)) |
            (Student.department.like(search_pattern)) |
            (Student.program.like(search_pattern))
        ).all()

    def create_student(self, data: Dict[str, Any], profile_photo_file: Optional[FileStorage] = None, current_user_id: Optional[int] = None) -> Student:
        """
        Creates a User account and a corresponding Student profile.
        All-or-nothing transaction.
        """
        # 1. Register corresponding User
        email = data['email']
        password = data.get('password', 'Student@123')  # Default password
        
        try:
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                raise ValueError(f"A user with email {email} already exists.")
                
            # Check if student ID already exists
            existing_student = Student.query.filter_by(student_id=data['student_id']).first()
            if existing_student:
                raise ValueError(f"Student ID {data['student_id']} is already in use.")

            user = User(
                email=email,
                password_hash=AuthService.hash_password(password),
                role='student'
            )
            db.session.add(user)
            db.session.flush()  # Obtain user.id

            # 2. Upload Profile Photo if provided
            photo_path = None
            if profile_photo_file:
                photo_path = self.storage.upload_file(profile_photo_file, folder='profile_photos')

            # 3. Create Student Profile
            student = Student(
                user_id=user.id,
                student_id=data['student_id'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                date_of_birth=data['date_of_birth'],
                gender=data.get('gender'),
                phone=data.get('phone'),
                address=data.get('address'),
                department=data['department'],
                program=data['program'],
                enrollment_date=data.get('enrollment_date', date.today()),
                profile_photo=photo_path
            )
            db.session.add(student)
            db.session.commit()
            
            # Log Student Creation
            AuditService.log_event(
                action="student_create",
                user_id=current_user_id,
                details=f"Created student {student.student_id} ({student.full_name}) linked to user ID {user.id}"
            )
            return student
            
        except Exception as e:
            db.session.rollback()
            # Delete uploaded file if the transaction failed
            if photo_path:
                self.storage.delete_file(photo_path)
            raise e

    def update_student(self, student_id: int, data: Dict[str, Any], profile_photo_file: Optional[FileStorage] = None, current_user_id: Optional[int] = None) -> Student:
        """
        Updates student profile information.
        """
        student = Student.query.get(student_id)
        if not student:
            raise ValueError("Student not found.")
            
        try:
            # Update user email
            if 'email' in data and data['email'] != student.user.email:
                existing_user = User.query.filter_by(email=data['email']).first()
                if existing_user:
                    raise ValueError(f"Email {data['email']} is already in use.")
                student.user.email = data['email']

            # Update core fields
            for key in ['first_name', 'last_name', 'date_of_birth', 'gender', 'phone', 'address', 'department', 'program', 'enrollment_date']:
                if key in data:
                    setattr(student, key, data[key])

            # Update profile photo
            if profile_photo_file:
                old_photo = student.profile_photo
                photo_path = self.storage.upload_file(profile_photo_file, folder='profile_photos')
                student.profile_photo = photo_path
                
                # Delete old photo
                if old_photo:
                    self.storage.delete_file(old_photo)

            db.session.commit()
            
            AuditService.log_event(
                action="student_update",
                user_id=current_user_id,
                details=f"Updated student profile for {student.student_id}"
            )
            return student
            
        except Exception as e:
            db.session.rollback()
            raise e

    def delete_student(self, student_id: int, current_user_id: Optional[int] = None) -> bool:
        """
        Deletes student and their associated user account, documents, and profile photo.
        """
        student = Student.query.get(student_id)
        if not student:
            return False
            
        try:
            user = student.user
            student_code = student.student_id
            student_name = student.full_name
            
            # Keep tracks of files to clean up from storage
            files_to_delete = []
            if student.profile_photo:
                files_to_delete.append(student.profile_photo)
                
            for doc in student.documents:
                files_to_delete.append(doc.file_path)

            # Cascade delete is handled by ORM and database constraints
            # We delete the User which cascades to Student and associated tables
            db.session.delete(user)
            db.session.commit()

            # Clean up files after successful DB transaction
            for file_path in files_to_delete:
                self.storage.delete_file(file_path)

            AuditService.log_event(
                action="student_delete",
                user_id=current_user_id,
                details=f"Deleted student {student_code} ({student_name}) and associated user account."
            )
            return True
        except Exception as e:
            db.session.rollback()
            raise e
            
    def upload_document(self, student_id: int, file: FileStorage, file_type: str = 'document') -> Document:
        """Uploads a certificate or academic document for a student."""
        student = Student.query.get(student_id)
        if not student:
            raise ValueError("Student not found.")
            
        file_path = self.storage.upload_file(file, folder=f"documents/{student.student_id}")
        
        try:
            doc = Document(
                student_id=student.id,
                file_name=file.filename,
                file_path=file_path,
                file_type=file_type
            )
            db.session.add(doc)
            db.session.commit()
            return doc
        except Exception as e:
            db.session.rollback()
            self.storage.delete_file(file_path)
            raise e
            
    def delete_document(self, document_id: int) -> bool:
        doc = Document.query.get(document_id)
        if not doc:
            return False
            
        file_path = doc.file_path
        try:
            db.session.delete(doc)
            db.session.commit()
            self.storage.delete_file(file_path)
            return True
        except Exception as e:
            db.session.rollback()
            raise e
