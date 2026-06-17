from datetime import datetime, date
from flask_login import UserMixin
from app.database import db

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, teacher, student
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # 1:1 Relationships
    student = db.relationship('Student', back_populates='user', uselist=False, cascade="all, delete-orphan")
    teacher = db.relationship('Teacher', back_populates='user', uselist=False, cascade="all, delete-orphan")
    
    # Logs relationship
    audit_logs = db.relationship('AuditLog', back_populates='user')

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"


class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    student_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(15), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    department = db.Column(db.String(100), nullable=False)
    program = db.Column(db.String(100), nullable=False)
    enrollment_date = db.Column(db.Date, default=date.today, nullable=False)
    profile_photo = db.Column(db.String(255), nullable=True)  # File path or S3 key
    
    # Relationships
    user = db.relationship('User', back_populates='student')
    enrollments = db.relationship('Enrollment', back_populates='student', cascade="all, delete-orphan")
    attendance = db.relationship('Attendance', back_populates='student', cascade="all, delete-orphan")
    marks = db.relationship('Mark', back_populates='student', cascade="all, delete-orphan")
    documents = db.relationship('Document', back_populates='student', cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<Student {self.student_id}: {self.full_name}>"


class Teacher(db.Model):
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    employee_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    department = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(150), nullable=True)
    
    # Relationships
    user = db.relationship('User', back_populates='teacher')
    courses = db.relationship('Course', back_populates='teacher')

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<Teacher {self.employee_id}: {self.full_name}>"


class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    course_name = db.Column(db.String(100), nullable=False)
    credit_hours = db.Column(db.Integer, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id', ondelete='SET NULL'), nullable=True)
    
    # Relationships
    teacher = db.relationship('Teacher', back_populates='courses')
    enrollments = db.relationship('Enrollment', back_populates='course', cascade="all, delete-orphan")
    attendance = db.relationship('Attendance', back_populates='course', cascade="all, delete-orphan")
    marks = db.relationship('Mark', back_populates='course', cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Course {self.course_code}: {self.course_name}>"


class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    student = db.relationship('Student', back_populates='enrollments')
    course = db.relationship('Course', back_populates='enrollments')

    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', name='_student_course_enrollment_uc'),
    )

    def __repr__(self) -> str:
        return f"<Enrollment Student: {self.student_id} -> Course: {self.course_id}>"


class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.String(15), nullable=False)  # Present, Absent, Late
    
    # Relationships
    student = db.relationship('Student', back_populates='attendance')
    course = db.relationship('Course', back_populates='attendance')

    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', 'date', name='_student_course_date_attendance_uc'),
    )

    def __repr__(self) -> str:
        return f"<Attendance Student: {self.student_id}, Course: {self.course_id}, Date: {self.date}, Status: {self.status}>"


class Mark(db.Model):
    __tablename__ = 'marks'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    assignment_marks = db.Column(db.Float, default=0.0, nullable=False)
    midterm_marks = db.Column(db.Float, default=0.0, nullable=False)
    final_marks = db.Column(db.Float, default=0.0, nullable=False)
    total_marks = db.Column(db.Float, default=0.0, nullable=False)
    grade = db.Column(db.String(5), nullable=False)  # A, B+, etc.
    gpa = db.Column(db.Float, default=0.0, nullable=False)
    
    # Relationships
    student = db.relationship('Student', back_populates='marks')
    course = db.relationship('Course', back_populates='marks')

    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', name='_student_course_marks_uc'),
    )

    def __repr__(self) -> str:
        return f"<Mark Student: {self.student_id}, Course: {self.course_id}, Total: {self.total_marks}, Grade: {self.grade}>"


class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    file_name = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)  # local storage path or S3 key/URL
    file_type = db.Column(db.String(20), nullable=False)  # photo, certificate, document, other
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    student = db.relationship('Student', back_populates='documents')

    def __repr__(self) -> str:
        return f"<Document {self.file_name} of Student {self.student_id}>"


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    email = db.Column(db.String(120), nullable=True)  # Tracks targeted/used email during login or events
    action = db.Column(db.String(50), nullable=False, index=True)  # login, logout, failed_login, student_create, student_delete, marks_modify, etc.
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = db.relationship('User', back_populates='audit_logs')

    def __repr__(self) -> str:
        return f"<AuditLog Action: {self.action}, User ID: {self.user_id}, Time: {self.created_at}>"
