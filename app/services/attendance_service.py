from datetime import date
from typing import List, Dict, Any, Optional
from app.database import db
from app.models import Attendance, Student, Course, Enrollment

class AttendanceService:
    @staticmethod
    def mark_attendance(student_id: int, course_id: int, date_val: date, status: str) -> Attendance:
        """Mark or update attendance for a student in a course on a specific date."""
        if status not in ['Present', 'Absent', 'Late']:
            raise ValueError("Invalid attendance status. Must be Present, Absent, or Late.")
            
        record = Attendance.query.filter_by(
            student_id=student_id,
            course_id=course_id,
            date=date_val
        ).first()
        
        if record:
            record.status = status
        else:
            record = Attendance(
                student_id=student_id,
                course_id=course_id,
                date=date_val,
                status=status
            )
            db.session.add(record)
            
        db.session.commit()
        return record

    @staticmethod
    def batch_mark_attendance(course_id: int, date_val: date, attendance_data: List[Dict[str, Any]]) -> List[Attendance]:
        """
        Batch save attendance for a class.
        attendance_data: list of dicts containing {'student_id': 1, 'status': 'Present'}
        """
        records = []
        for item in attendance_data:
            student_id = int(item['student_id'])
            status = item['status']
            if status not in ['Present', 'Absent', 'Late']:
                continue
                
            record = Attendance.query.filter_by(
                student_id=student_id,
                course_id=course_id,
                date=date_val
            ).first()
            
            if record:
                record.status = status
            else:
                record = Attendance(
                    student_id=student_id,
                    course_id=course_id,
                    date=date_val,
                    status=status
                )
                db.session.add(record)
            records.append(record)
            
        db.session.commit()
        return records

    @staticmethod
    def get_student_attendance(student_id: int, course_id: Optional[int] = None) -> List[Attendance]:
        query = Attendance.query.filter_by(student_id=student_id)
        if course_id:
            query = query.filter_by(course_id=course_id)
        return query.order_by(Attendance.date.desc()).all()

    @staticmethod
    def get_course_attendance_on_date(course_id: int, date_val: date) -> List[Attendance]:
        return Attendance.query.filter_by(course_id=course_id, date=date_val).all()

    @staticmethod
    def calculate_attendance_percentage(student_id: int, course_id: Optional[int] = None) -> float:
        """
        Calculates attendance percentage. Present and Late are counted as attended.
        """
        query = Attendance.query.filter_by(student_id=student_id)
        if course_id:
            query = query.filter_by(course_id=course_id)
            
        records = query.all()
        if not records:
            return 100.0  # Default to 100 if no classes have occurred
            
        attended = sum(1 for r in records if r.status in ['Present', 'Late'])
        return round((attended / len(records)) * 100, 2)

    @staticmethod
    def get_course_attendance_summary(course_id: int) -> Dict[str, Any]:
        """Returns statistics for a course: total classes, average attendance rate."""
        records = Attendance.query.filter_by(course_id=course_id).all()
        if not records:
            return {'total_records': 0, 'average_rate': 100.0}
            
        attended = sum(1 for r in records if r.status in ['Present', 'Late'])
        avg_rate = round((attended / len(records)) * 100, 2)
        
        # Get unique dates
        unique_dates = db.session.query(Attendance.date).filter_by(course_id=course_id).distinct().count()
        
        return {
            'total_records': len(records),
            'unique_dates': unique_dates,
            'average_rate': avg_rate
        }
