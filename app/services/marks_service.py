from typing import List, Dict, Any, Optional
from app.database import db
from app.models import Mark, Student, Course
from app.services.audit_service import AuditService

class MarksService:
    @staticmethod
    def calculate_grade_and_gpa(total_marks: float) -> tuple:
        """
        Maps total marks (0-100) to Letter Grade and GPA points.
        """
        if total_marks >= 90:
            return 'A', 4.0
        elif total_marks >= 80:
            return 'B', 3.0
        elif total_marks >= 70:
            return 'C', 2.0
        elif total_marks >= 60:
            return 'D', 1.0
        else:
            return 'F', 0.0

    @classmethod
    def save_marks(cls, student_id: int, course_id: int, assignment: float, midterm: float, final: float, current_user_id: Optional[int] = None) -> Mark:
        """
        Saves or updates marks for a student in a course, recalculating totals, grade, and GPA.
        """
        # Validate values (Assignment out of 20, Midterm out of 30, Final out of 50)
        if not (0 <= assignment <= 20) or not (0 <= midterm <= 30) or not (0 <= final <= 50):
            raise ValueError("Invalid marks inputs. Constraints: Assignment (0-20), Midterm (0-30), Final (0-50).")
            
        total = assignment + midterm + final
        grade, gpa = cls.calculate_grade_and_gpa(total)
        
        record = Mark.query.filter_by(student_id=student_id, course_id=course_id).first()
        is_update = record is not None
        
        if record:
            old_total = record.total_marks
            record.assignment_marks = assignment
            record.midterm_marks = midterm
            record.final_marks = final
            record.total_marks = total
            record.grade = grade
            record.gpa = gpa
        else:
            old_total = 0.0
            record = Mark(
                student_id=student_id,
                course_id=course_id,
                assignment_marks=assignment,
                midterm_marks=midterm,
                final_marks=final,
                total_marks=total,
                grade=grade,
                gpa=gpa
            )
            db.session.add(record)
            
        db.session.commit()
        
        # Security requirement: log marks modification audit event
        student = Student.query.get(student_id)
        course = Course.query.get(course_id)
        AuditService.log_event(
            action="marks_modify",
            user_id=current_user_id,
            details=f"Modified marks for student {student.student_id if student else student_id} in course {course.course_code if course else course_id}. "
                    f"New Total: {total} ({grade}), Previous Total: {old_total if is_update else 'None'}"
        )
        
        return record

    @staticmethod
    def get_student_marks(student_id: int) -> List[Mark]:
        return Mark.query.filter_by(student_id=student_id).all()

    @staticmethod
    def get_course_marks(course_id: int) -> List[Mark]:
        return Mark.query.filter_by(course_id=course_id).all()

    @staticmethod
    def calculate_student_gpa(student_id: int) -> float:
        """
        Calculates cumulative GPA (weighted by course credit hours if possible, or simple average).
        We will use course credit-hour weightage. Cumulative GPA = Sum(GPA * Credits) / Sum(Credits)
        """
        marks = Mark.query.filter_by(student_id=student_id).all()
        if not marks:
            return 0.0
            
        total_points = 0.0
        total_credits = 0
        
        for mark in marks:
            credits = mark.course.credit_hours
            total_points += (mark.gpa * credits)
            total_credits += credits
            
        if total_credits == 0:
            return 0.0
            
        return round(total_points / total_credits, 2)

    @staticmethod
    def get_system_pass_rate() -> float:
        """Calculates system-wide pass rate (percentage of courses passed with non-F grades)."""
        total_records = Mark.query.count()
        if total_records == 0:
            return 100.0
            
        passed_records = Mark.query.filter(Mark.grade != 'F').count()
        return round((passed_records / total_records) * 100, 2)

    @staticmethod
    def get_grade_distribution() -> Dict[str, int]:
        """Returns the counts of students in each grade category (A, B, C, D, F)."""
        distribution = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
        records = db.session.query(Mark.grade, db.func.count(Mark.grade)).group_by(Mark.grade).all()
        
        for grade, count in records:
            if grade in distribution:
                distribution[grade] = count
                
        return distribution
