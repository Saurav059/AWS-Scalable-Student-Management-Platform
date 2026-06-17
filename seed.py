import os
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import create_app
from app.database import db
from app.extensions import bcrypt
from app.models import User, Student, Teacher, Course, Enrollment, Attendance, Mark, AuditLog

def seed_database():
    app = create_app()
    with app.app_context():
        print("Starting database seeding process...")
        
        # Clear existing tables to prevent duplicate entries
        print("Clearing existing tables...")
        # To avoid cascading constraint issues, let's delete in order
        AuditLog.query.delete()
        Mark.query.delete()
        Attendance.query.delete()
        Enrollment.query.delete()
        Course.query.delete()
        Student.query.delete()
        Teacher.query.delete()
        User.query.delete()
        db.session.commit()
        
        print("Creating User accounts...")
        # 1. Admin
        admin_user = User(
            email='admin@university.edu',
            password_hash=bcrypt.generate_password_hash('Admin@123').decode('utf-8'),
            role='admin',
            is_active=True
        )
        db.session.add(admin_user)
        
        # 2. Teachers
        t1_user = User(
            email='teacher1@university.edu',
            password_hash=bcrypt.generate_password_hash('Teacher@123').decode('utf-8'),
            role='teacher',
            is_active=True
        )
        t2_user = User(
            email='teacher2@university.edu',
            password_hash=bcrypt.generate_password_hash('Teacher@123').decode('utf-8'),
            role='teacher',
            is_active=True
        )
        db.session.add(t1_user)
        db.session.add(t2_user)
        
        # 3. Students
        s1_user = User(
            email='student1@university.edu',
            password_hash=bcrypt.generate_password_hash('Student@123').decode('utf-8'),
            role='student',
            is_active=True
        )
        s2_user = User(
            email='student2@university.edu',
            password_hash=bcrypt.generate_password_hash('Student@123').decode('utf-8'),
            role='student',
            is_active=True
        )
        s3_user = User(
            email='student3@university.edu',
            password_hash=bcrypt.generate_password_hash('Student@123').decode('utf-8'),
            role='student',
            is_active=True
        )
        db.session.add(s1_user)
        db.session.add(s2_user)
        db.session.add(s3_user)
        db.session.commit() # Commit to generate user IDs
        
        print("Creating Teachers profiles...")
        teacher1 = Teacher(
            user_id=t1_user.id,
            employee_id='TCH001',
            first_name='Albert',
            last_name='Einstein',
            phone='+1-555-0101',
            department='Physics',
            specialization='Quantum Mechanics'
        )
        teacher2 = Teacher(
            user_id=t2_user.id,
            employee_id='TCH002',
            first_name='Alan',
            last_name='Turing',
            phone='+1-555-0102',
            department='Computer Science',
            specialization='Theoretical Computation'
        )
        db.session.add(teacher1)
        db.session.add(teacher2)
        db.session.commit()
        
        print("Creating Student profiles...")
        student1 = Student(
            user_id=s1_user.id,
            student_id='STD001',
            first_name='Marie',
            last_name='Curie',
            date_of_birth=date(2005, 11, 7),
            gender='Female',
            phone='+1-555-0201',
            address='77 Science Park, Warsaw',
            department='Physics',
            program='B.Sc. Nuclear Physics'
        )
        student2 = Student(
            user_id=s2_user.id,
            student_id='STD002',
            first_name='Nikola',
            last_name='Tesla',
            date_of_birth=date(2006, 7, 10),
            gender='Male',
            phone='+1-555-0202',
            address='12 Alternating Current Blvd, Smiljan',
            department='Computer Science',
            program='B.Sc. Electrical Eng'
        )
        student3 = Student(
            user_id=s3_user.id,
            student_id='STD003',
            first_name='Ada',
            last_name='Lovelace',
            date_of_birth=date(2005, 12, 10),
            gender='Female',
            phone='+1-555-0203',
            address='10 Bernoulli St, London',
            department='Computer Science',
            program='B.Sc. IT'
        )
        db.session.add(student1)
        db.session.add(student2)
        db.session.add(student3)
        db.session.commit()
        
        print("Creating Course Catalog...")
        course1 = Course(
            course_code='CS-101',
            course_name='Introduction to Cloud Architecture & AWS',
            credit_hours=3,
            semester='Fall 2026',
            department='Computer Science',
            teacher_id=teacher2.id
        )
        course2 = Course(
            course_code='CS-202',
            course_name='Distributed Database Systems',
            credit_hours=4,
            semester='Fall 2026',
            department='Computer Science',
            teacher_id=teacher2.id
        )
        course3 = Course(
            course_code='PHYS-301',
            course_name='General Relativity & Astrophysics',
            credit_hours=3,
            semester='Fall 2026',
            department='Physics',
            teacher_id=teacher1.id
        )
        db.session.add(course1)
        db.session.add(course2)
        db.session.add(course3)
        db.session.commit()
        
        print("Creating Course Enrollments...")
        # Marie Curie is enrolled in Cloud Architecture and Relativity
        e1 = Enrollment(student_id=student1.id, course_id=course1.id)
        e2 = Enrollment(student_id=student1.id, course_id=course3.id)
        # Nikola Tesla in Database Systems and Cloud Architecture
        e3 = Enrollment(student_id=student2.id, course_id=course1.id)
        e4 = Enrollment(student_id=student2.id, course_id=course2.id)
        # Ada Lovelace in Cloud Architecture and Database Systems
        e5 = Enrollment(student_id=student3.id, course_id=course1.id)
        e6 = Enrollment(student_id=student3.id, course_id=course2.id)
        
        db.session.add_all([e1, e2, e3, e4, e5, e6])
        db.session.commit()
        
        print("Generating Attendance logs...")
        # Add 5 days of attendance for CS-101 (all students) and PHYS-301
        today = date.today()
        for i in range(5):
            past_date = today - timedelta(days=i)
            # Skip weekends
            if past_date.weekday() >= 5:
                continue
                
            # CS-101 records
            db.session.add(Attendance(student_id=student1.id, course_id=course1.id, date=past_date, status='Present'))
            # Tesla is Late on day 2, Absent on day 4, Present otherwise
            status_t = 'Present'
            if i == 2: status_t = 'Late'
            elif i == 4: status_t = 'Absent'
            db.session.add(Attendance(student_id=student2.id, course_id=course1.id, date=past_date, status=status_t))
            # Ada is present
            db.session.add(Attendance(student_id=student3.id, course_id=course1.id, date=past_date, status='Present'))
            
            # PHYS-301 records (Only student 1 is enrolled)
            db.session.add(Attendance(student_id=student1.id, course_id=course3.id, date=past_date, status='Present'))
            
        db.session.commit()
        
        print("Generating Grade cards (Marks)...")
        # Save marks with custom weights
        # Cloud Architecture (CS-101) grades
        db.session.add(Mark(student_id=student1.id, course_id=course1.id, assignment_marks=18.5, midterm_marks=27.0, final_marks=45.0, total_marks=90.5, grade='A', gpa=4.0)) # A
        db.session.add(Mark(student_id=student2.id, course_id=course1.id, assignment_marks=15.0, midterm_marks=22.0, final_marks=38.0, total_marks=75.0, grade='B', gpa=3.0)) # B
        db.session.add(Mark(student_id=student3.id, course_id=course1.id, assignment_marks=19.0, midterm_marks=29.0, final_marks=48.0, total_marks=96.0, grade='A', gpa=4.0)) # A
        
        # Database Systems (CS-202) grades
        db.session.add(Mark(student_id=student2.id, course_id=course2.id, assignment_marks=12.0, midterm_marks=18.0, final_marks=31.0, total_marks=61.0, grade='C', gpa=2.0)) # C
        db.session.add(Mark(student_id=student3.id, course_id=course2.id, assignment_marks=17.0, midterm_marks=25.0, final_marks=42.0, total_marks=84.0, grade='A', gpa=4.0)) # A
        
        # Relativity (PHYS-301) grades
        db.session.add(Mark(student_id=student1.id, course_id=course3.id, assignment_marks=19.5, midterm_marks=28.5, final_marks=47.5, total_marks=95.5, grade='A', gpa=4.0)) # A
        db.session.add(Mark(student_id=student2.id, course_id=course3.id, assignment_marks=5.0, midterm_marks=10.0, final_marks=15.0, total_marks=30.0, grade='F', gpa=0.0)) # F
        
        db.session.commit()
        
        print("Writing system audit entries...")
        db.session.add(AuditLog(action='user_registration', details='Created admin account (admin@university.edu)', ip_address='127.0.0.1'))
        db.session.add(AuditLog(action='user_registration', details='Registered teacher Einstein (TCH001)', ip_address='127.0.0.1'))
        db.session.add(AuditLog(action='user_registration', details='Registered student Curie (STD001)', ip_address='127.0.0.1'))
        db.session.add(AuditLog(action='marks_modification', details='Albert Einstein recorded grades for CS-101', ip_address='127.0.0.1'))
        db.session.commit()
        
        print("Database seeded successfully with all relationships intact!")
        print("\nLogin Credentials:")
        print("--------------------")
        print("Admin   : admin@university.edu / Admin@123")
        print("Teacher : teacher1@university.edu / Teacher@123")
        print("Student : student1@university.edu / Student@123")

if __name__ == '__main__':
    seed_database()
