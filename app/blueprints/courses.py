from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.services.course_service import CourseService
from app.services.auth_service import role_required
from app.models import Teacher, Student, Course

courses_bp = Blueprint('courses', __name__)

@courses_bp.route('/')
@login_required
def index():
    query = request.args.get('q', '')
    if query:
        courses = CourseService.search_courses(query)
    else:
        courses = CourseService.get_all_courses()
        
    return render_template('courses/index.html', courses=courses, query=query)

@courses_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create():
    teachers = Teacher.query.all()
    if request.method == 'POST':
        course_code = request.form.get('course_code')
        course_name = request.form.get('course_name')
        credit_hours_str = request.form.get('credit_hours')
        department = request.form.get('department')
        semester = request.form.get('semester')
        teacher_id_str = request.form.get('teacher_id')
        
        # Validation
        if not (course_code and course_name and credit_hours_str and department and semester):
            flash("Please fill in all required fields.", "warning")
            return redirect(url_for('courses.create'))
            
        try:
            credit_hours = int(credit_hours_str)
            teacher_id = int(teacher_id_str) if (teacher_id_str and teacher_id_str != 'None') else None
            
            data = {
                'course_code': course_code,
                'course_name': course_name,
                'credit_hours': credit_hours,
                'department': department,
                'semester': semester,
                'teacher_id': teacher_id
            }
            
            CourseService.create_course(data)
            flash("Course created successfully!", "success")
            return redirect(url_for('courses.index'))
        except Exception as e:
            flash(f"Error creating course: {str(e)}", "danger")
            
    return render_template('courses/create.html', teachers=teachers)

@courses_bp.route('/<int:id>')
@login_required
def details(id):
    course = CourseService.get_course_by_id(id)
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for('courses.index'))
        
    # Check permissions: Students can only view their own courses. Teachers can only view assigned courses.
    if current_user.role == 'student':
        student = Student.query.filter_by(user_id=current_user.id).first()
        if not student or course not in [e.course for e in student.enrollments]:
            abort(403)
    elif current_user.role == 'teacher':
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        # Teachers can view courses they teach
        if not teacher or (course.teacher_id != teacher.id):
            abort(403)
            
    enrolled_students = CourseService.get_enrolled_students(course.id)
    all_students = Student.query.all()  # For the admin quick enrollment modal/form
    
    return render_template(
        'courses/details.html',
        course=course,
        enrolled_students=enrolled_students,
        all_students=all_students
    )

@courses_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit(id):
    course = CourseService.get_course_by_id(id)
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for('courses.index'))
        
    teachers = Teacher.query.all()
    if request.method == 'POST':
        try:
            credit_hours_str = request.form.get('credit_hours')
            teacher_id_str = request.form.get('teacher_id')
            
            data = {
                'course_code': request.form.get('course_code'),
                'course_name': request.form.get('course_name'),
                'credit_hours': int(credit_hours_str) if credit_hours_str else course.credit_hours,
                'department': request.form.get('department'),
                'semester': request.form.get('semester'),
                'teacher_id': int(teacher_id_str) if (teacher_id_str and teacher_id_str != 'None') else None
            }
            
            CourseService.update_course(course.id, data)
            flash("Course updated successfully!", "success")
            return redirect(url_for('courses.details', id=course.id))
        except Exception as e:
            flash(f"Error updating course: {str(e)}", "danger")
            
    return render_template('courses/edit.html', course=course, teachers=teachers)

@courses_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete(id):
    if CourseService.delete_course(id):
        flash("Course deleted successfully.", "success")
    else:
        flash("Failed to delete course.", "danger")
    return redirect(url_for('courses.index'))

@courses_bp.route('/<int:id>/enroll', methods=['POST'])
@login_required
@role_required('admin')
def enroll(id):
    student_id_str = request.form.get('student_id')
    if not student_id_str:
        flash("Please select a student.", "warning")
        return redirect(url_for('courses.details', id=id))
        
    try:
        student_id = int(student_id_str)
        CourseService.enroll_student(id, student_id)
        flash("Student enrolled successfully!", "success")
    except Exception as e:
        flash(f"Error enrolling student: {str(e)}", "danger")
        
    return redirect(url_for('courses.details', id=id))

@courses_bp.route('/<int:id>/unenroll/<int:student_id>', methods=['POST'])
@login_required
@role_required('admin')
def unenroll(id, student_id):
    if CourseService.unenroll_student(id, student_id):
        flash("Student unenrolled successfully.", "success")
    else:
        flash("Failed to unenroll student.", "danger")
    return redirect(url_for('courses.details', id=id))
