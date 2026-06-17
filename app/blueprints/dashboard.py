from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta

from app.database import db
from app.models import User, Student, Teacher, Course, Attendance, Mark, AuditLog
from app.services.attendance_service import AttendanceService
from app.services.marks_service import MarksService
from app.services.course_service import CourseService

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    if current_user.role == 'admin':
        return redirect(url_for('dashboard.admin'))
    elif current_user.role == 'teacher':
        return redirect(url_for('dashboard.teacher'))
    elif current_user.role == 'student':
        return redirect(url_for('dashboard.student'))
    else:
        # Fallback
        return redirect(url_for('auth.logout'))

@dashboard_bp.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        return redirect(url_for('dashboard.index'))
        
    # Gather counts
    total_students = Student.query.count()
    total_teachers = Teacher.query.count()
    total_courses = Course.query.count()
    total_attendance = Attendance.query.count()
    
    # Average Attendance Rate
    # Find all attendance records
    all_attendance = Attendance.query.all()
    if all_attendance:
        present_count = sum(1 for r in all_attendance if r.status in ['Present', 'Late'])
        avg_attendance = round((present_count / len(all_attendance)) * 100, 1)
    else:
        avg_attendance = 100.0
        
    # Pass rate
    pass_rate = MarksService.get_system_pass_rate()
    
    # Recent Activities
    recent_activities = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(8).all()
    
    # Chart 1: Grade Distribution
    grade_dist = MarksService.get_grade_distribution()
    
    # Chart 2: Student growth (enrollment counts by date, grouped by month)
    # Simple query for enrollment growth
    growth_records = db.session.query(
        func.strftime('%Y-%m', Student.enrollment_date).label('month'), 
        func.count(Student.id).label('count')
    ).group_by('month').order_by('month').limit(6).all()
    
    # If using postgres/mysql, strftime won't work, so check if SQLite or MySQL
    # For robust cross-DB support we can also query and format in Python:
    students_all = Student.query.all()
    growth_dict = {}
    for s in students_all:
        if s.enrollment_date:
            m_key = s.enrollment_date.strftime('%Y-%m')
            growth_dict[m_key] = growth_dict.get(m_key, 0) + 1
            
    # Sort growth keys
    sorted_months = sorted(growth_dict.keys())[-6:]
    growth_labels = sorted_months
    growth_data = [growth_dict[m] for m in sorted_months]
    
    # Chart 3: Attendance Trends (Present / Late / Absent counts)
    attendance_stats = db.session.query(
        Attendance.status, func.count(Attendance.status)
    ).group_by(Attendance.status).all()
    attendance_dist = {'Present': 0, 'Absent': 0, 'Late': 0}
    for status, count in attendance_stats:
        if status in attendance_dist:
            attendance_dist[status] = count

    return render_template(
        'dashboard/admin.html',
        total_students=total_students,
        total_teachers=total_teachers,
        total_courses=total_courses,
        total_attendance=total_attendance,
        avg_attendance=avg_attendance,
        pass_rate=pass_rate,
        recent_activities=recent_activities,
        grade_dist=grade_dist,
        growth_labels=growth_labels,
        growth_data=growth_data,
        attendance_dist=attendance_dist
    )

@dashboard_bp.route('/teacher')
@login_required
def teacher():
    if current_user.role != 'teacher':
        return redirect(url_for('dashboard.index'))
        
    teacher_profile = Teacher.query.filter_by(user_id=current_user.id).first()
    if not teacher_profile:
        return "Teacher profile not configured. Contact Administrator.", 404
        
    assigned_courses = CourseService.get_teacher_courses(teacher_profile.id)
    
    return render_template(
        'dashboard/teacher.html',
        teacher=teacher_profile,
        courses=assigned_courses
    )

@dashboard_bp.route('/student')
@login_required
def student():
    if current_user.role != 'student':
        return redirect(url_for('dashboard.index'))
        
    student_profile = Student.query.filter_by(user_id=current_user.id).first()
    if not student_profile:
        return "Student profile not configured. Contact Administrator.", 404
        
    # Get enrolled courses
    courses = CourseService.get_student_enrollments(student_profile.id)
    
    # Attendance stats
    attendance_percentage = AttendanceService.calculate_attendance_percentage(student_profile.id)
    attendance_logs = AttendanceService.get_student_attendance(student_profile.id)[:5]
    
    # Marks / GPA
    marks = MarksService.get_student_marks(student_profile.id)
    cumulative_gpa = MarksService.calculate_student_gpa(student_profile.id)
    
    return render_template(
        'dashboard/student.html',
        student=student_profile,
        courses=courses,
        attendance_percentage=attendance_percentage,
        attendance_logs=attendance_logs,
        marks=marks,
        cumulative_gpa=cumulative_gpa
    )
