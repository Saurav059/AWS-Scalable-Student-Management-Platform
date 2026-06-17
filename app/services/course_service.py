from typing import List, Optional, Dict, Any
from app.database import db
from app.models import Course, Teacher, Student, Enrollment

class CourseService:
    @staticmethod
    def get_all_courses() -> List[Course]:
        return Course.query.all()

    @staticmethod
    def get_course_by_id(course_id: int) -> Optional[Course]:
        return Course.query.get(course_id)

    @staticmethod
    def get_course_by_code(course_code: str) -> Optional[Course]:
        return Course.query.filter_by(course_code=course_code).first()

    @staticmethod
    def search_courses(query: str) -> List[Course]:
        """Search courses by Code, Name, Department, or Semester."""
        if not query:
            return CourseService.get_all_courses()
            
        search_pattern = f"%{query}%"
        return Course.query.filter(
            (Course.course_code.like(search_pattern)) |
            (Course.course_name.like(search_pattern)) |
            (Course.department.like(search_pattern)) |
            (Course.semester.like(search_pattern))
        ).all()

    @staticmethod
    def create_course(data: Dict[str, Any]) -> Course:
        existing = Course.query.filter_by(course_code=data['course_code']).first()
        if existing:
            raise ValueError(f"Course code {data['course_code']} already exists.")
            
        course = Course(
            course_code=data['course_code'],
            course_name=data['course_name'],
            credit_hours=data['credit_hours'],
            department=data['department'],
            semester=data['semester'],
            teacher_id=data.get('teacher_id')
        )
        db.session.add(course)
        db.session.commit()
        return course

    @staticmethod
    def update_course(course_id: int, data: Dict[str, Any]) -> Course:
        course = Course.query.get(course_id)
        if not course:
            raise ValueError("Course not found.")
            
        if 'course_code' in data and data['course_code'] != course.course_code:
            existing = Course.query.filter_by(course_code=data['course_code']).first()
            if existing:
                raise ValueError(f"Course code {data['course_code']} already exists.")
                
        for key in ['course_code', 'course_name', 'credit_hours', 'department', 'semester', 'teacher_id']:
            if key in data:
                setattr(course, key, data[key])
                
        db.session.commit()
        return course

    @staticmethod
    def delete_course(course_id: int) -> bool:
        course = Course.query.get(course_id)
        if not course:
            return False
            
        db.session.delete(course)
        db.session.commit()
        return True

    @staticmethod
    def assign_teacher(course_id: int, teacher_id: Optional[int]) -> Course:
        course = Course.query.get(course_id)
        if not course:
            raise ValueError("Course not found.")
            
        if teacher_id:
            teacher = Teacher.query.get(teacher_id)
            if not teacher:
                raise ValueError("Teacher not found.")
                
        course.teacher_id = teacher_id
        db.session.commit()
        return course

    @staticmethod
    def enroll_student(course_id: int, student_id: int) -> Enrollment:
        """Enrolls a student in a course."""
        student = Student.query.get(student_id)
        course = Course.query.get(course_id)
        
        if not student or not course:
            raise ValueError("Student or Course not found.")
            
        existing = Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first()
        if existing:
            return existing
            
        enrollment = Enrollment(student_id=student_id, course_id=course_id)
        db.session.add(enrollment)
        db.session.commit()
        return enrollment

    @staticmethod
    def unenroll_student(course_id: int, student_id: int) -> bool:
        """Removes student enrollment from a course."""
        enrollment = Enrollment.query.filter_by(student_id=student_id, course_id=course_id).first()
        if not enrollment:
            return False
            
        db.session.delete(enrollment)
        db.session.commit()
        return True

    @staticmethod
    def get_enrolled_students(course_id: int) -> List[Student]:
        course = Course.query.get(course_id)
        if not course:
            return []
        return [enrollment.student for enrollment in course.enrollments]

    @staticmethod
    def get_student_enrollments(student_id: int) -> List[Course]:
        student = Student.query.get(student_id)
        if not student:
            return []
        return [enrollment.course for enrollment in student.enrollments]

    @staticmethod
    def get_teacher_courses(teacher_id: int) -> List[Course]:
        return Course.query.filter_by(teacher_id=teacher_id).all()
