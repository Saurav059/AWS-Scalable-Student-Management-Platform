from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user

from app.services.student_service import StudentService
from app.services.storage_service import get_storage_service
from app.models import Student, Document

documents_bp = Blueprint('documents', __name__)

def get_student_service():
    storage = get_storage_service(current_app.config)
    return StudentService(storage)

@documents_bp.route('/student/<int:student_id>')
@login_required
def list_docs(student_id):
    student = Student.query.get(student_id)
    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for('dashboard.index'))
        
    # Permission check: Admin/Teacher can view. Student can only view their own.
    if current_user.role == 'student':
        logged_in_student = Student.query.filter_by(user_id=current_user.id).first()
        if not logged_in_student or logged_in_student.id != student.id:
            abort(403)
            
    return render_template('documents/list.html', student=student)

@documents_bp.route('/student/<int:student_id>/upload', methods=['POST'])
@login_required
def upload(student_id):
    student = Student.query.get(student_id)
    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for('dashboard.index'))
        
    # Permission check: Admin can upload. Student can upload for themselves.
    if current_user.role == 'student':
        logged_in_student = Student.query.filter_by(user_id=current_user.id).first()
        if not logged_in_student or logged_in_student.id != student.id:
            abort(403)
    elif current_user.role == 'teacher':
        abort(403)
        
    file = request.files.get('file')
    file_type = request.form.get('file_type', 'document')
    
    if not file or file.filename == '':
        flash("No file selected.", "warning")
        return redirect(url_for('documents.list_docs', student_id=student.id))
        
    try:
        student_service = get_student_service()
        student_service.upload_document(student.id, file, file_type)
        flash("Document uploaded successfully!", "success")
    except Exception as e:
        flash(f"Error uploading document: {str(e)}", "danger")
        
    return redirect(url_for('documents.list_docs', student_id=student.id))

@documents_bp.route('/<int:document_id>/download')
@login_required
def download(document_id):
    doc = Document.query.get(document_id)
    if not doc:
        flash("Document not found.", "danger")
        return redirect(url_for('dashboard.index'))
        
    # Permission check
    if current_user.role == 'student':
        logged_in_student = Student.query.filter_by(user_id=current_user.id).first()
        if not logged_in_student or logged_in_student.id != doc.student_id:
            abort(403)
            
    storage = get_storage_service(current_app.config)
    file_url = storage.get_file_url(doc.file_path)
    
    # Redirect user directly to the file url (pre-signed S3 or local static url)
    return redirect(file_url)

@documents_bp.route('/<int:document_id>/delete', methods=['POST'])
@login_required
def delete(document_id):
    doc = Document.query.get(document_id)
    if not doc:
        flash("Document not found.", "danger")
        return redirect(url_for('dashboard.index'))
        
    student_id = doc.student_id
    
    # Permission check
    if current_user.role == 'student':
        logged_in_student = Student.query.filter_by(user_id=current_user.id).first()
        if not logged_in_student or logged_in_student.id != doc.student_id:
            abort(403)
    elif current_user.role == 'teacher':
        abort(403)
        
    student_service = get_student_service()
    if student_service.delete_document(document_id):
        flash("Document deleted successfully.", "success")
    else:
        flash("Failed to delete document.", "danger")
        
    return redirect(url_for('documents.list_docs', student_id=student_id))
