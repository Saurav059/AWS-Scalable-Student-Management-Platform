from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from datetime import datetime

from app.services.student_service import StudentService
from app.services.storage_service import get_storage_service
from app.services.auth_service import role_required
from app.models import Student, Teacher

students_bp = Blueprint('students', __name__)

def get_student_service():
    storage = get_storage_service(current_app.config)
    return StudentService(storage)

@students_bp.route('/')
@login_required
@role_required(['admin', 'teacher'])
def index():
    query = request.args.get('q', '')
    student_service = get_student_service()
    if query:
        students = student_service.search_students(query)
    else:
        students = student_service.get_all_students()
        
    return render_template('students/index.html', students=students, query=query)

@students_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create():
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        dob_str = request.form.get('date_of_birth')
        gender = request.form.get('gender')
        phone = request.form.get('phone')
        address = request.form.get('address')
        department = request.form.get('department')
        program = request.form.get('program')
        password = request.form.get('password') or 'Student@123'
        
        profile_photo = request.files.get('profile_photo')
        
        # Validation
        if not (student_id and first_name and last_name and email and dob_str and department and program):
            flash("Please fill in all required fields.", "warning")
            return redirect(url_for('students.create'))
            
        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            data = {
                'student_id': student_id,
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'date_of_birth': dob,
                'gender': gender,
                'phone': phone,
                'address': address,
                'department': department,
                'program': program,
                'password': password
            }
            
            student_service = get_student_service()
            student_service.create_student(data, profile_photo, current_user_id=current_user.id)
            flash("Student created successfully!", "success")
            return redirect(url_for('students.index'))
        except Exception as e:
            flash(f"Error creating student: {str(e)}", "danger")
            
    return render_template('students/create.html')

@students_bp.route('/<int:id>')
@login_required
def details(id):
    student_service = get_student_service()
    student = student_service.get_student_by_id(id)
    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for('students.index') if current_user.role in ['admin', 'teacher'] else url_for('dashboard.index'))
        
    # Check authorization: Admin/Teacher can view any student. Student can only view themselves.
    if current_user.role == 'student':
        logged_in_student = Student.query.filter_by(user_id=current_user.id).first()
        if not logged_in_student or logged_in_student.id != student.id:
            abort(403)
            
    return render_template('students/details.html', student=student)

@students_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    student_service = get_student_service()
    student = student_service.get_student_by_id(id)
    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for('students.index'))
        
    # Check authorization: Admin can edit any student. Student can edit their own profile.
    if current_user.role == 'student':
        logged_in_student = Student.query.filter_by(user_id=current_user.id).first()
        if not logged_in_student or logged_in_student.id != student.id:
            abort(403)
    elif current_user.role == 'teacher':
        abort(403)
        
    if request.method == 'POST':
        data = {
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'email': request.form.get('email'),
            'gender': request.form.get('gender'),
            'phone': request.form.get('phone'),
            'address': request.form.get('address'),
            'department': request.form.get('department'),
            'program': request.form.get('program')
        }
        
        dob_str = request.form.get('date_of_birth')
        if dob_str:
            data['date_of_birth'] = datetime.strptime(dob_str, '%Y-%m-%d').date()
            
        profile_photo = request.files.get('profile_photo')
        
        try:
            student_service.update_student(student.id, data, profile_photo, current_user_id=current_user.id)
            flash("Profile updated successfully!", "success")
            return redirect(url_for('students.details', id=student.id))
        except Exception as e:
            flash(f"Error updating profile: {str(e)}", "danger")
            
    return render_template('students/edit.html', student=student)

@students_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete(id):
    student_service = get_student_service()
    if student_service.delete_student(id, current_user_id=current_user.id):
        flash("Student record and user account deleted successfully.", "success")
    else:
        flash("Failed to delete student.", "danger")
    return redirect(url_for('students.index'))
