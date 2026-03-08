"""
University Gown Management System - Main Routes (Dashboard)
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, Response, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
import csv
import io
import random

from app import db
from app.models import Student, Inventory, Transaction, AuditLog
from app.access_control import admin_required

main_bp = Blueprint('main', __name__)


# Funny greetings for admins
FUNNY_GREETINGS = [
    "Welcome back! Coffee is on the house ☕",
    "Hello there! Ready to manage some gowns today? 🎓",
    "Hey superstar! The gowns won't manage themselves!",
    "Welcome! May your transactions be smooth and your returns be timely!",
    "Hello! Props for showing up. The gowns are waiting! 🎭",
    "Hey hey! Let's make sure everyone looks sharp today! 👔",
    "Welcome back! Your students' fashion sense is in good hands!",
    "Hello! Today would be a great day to issue some gowns!",
    "Hey there! Ready to dress some graduates for success? 🎓",
    "Welcome! Let's get everyone suited up for their big day!",
    "Hello superstar! The gown empire awaits your command! 👑",
    "Hey hey! Someone's looking sharp today (pun intended)! ✨",
    "Welcome! Ready to sprinkle some academic magic? ✨",
    "Hello there! Let's make sure they walk across that stage in style! 🎓",
    "Hey! The graduation fairy (that's you) is needed! 🧚",
]


def get_greeting():
    """Get time-based greeting with a funny message"""
    hour = datetime.now().hour
    
    if 5 <= hour < 12:
        time_greeting = "Good Morning"
    elif 12 <= hour < 17:
        time_greeting = "Good Afternoon"
    elif 17 <= hour < 21:
        time_greeting = "Good Evening"
    else:
        time_greeting = "Good Night"
    
    # Add a random funny greeting
    funny = random.choice(FUNNY_GREETINGS)
    
    return time_greeting, funny


@main_bp.route('/')
@main_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Dashboard with statistics (Admin & SuperAdmin)"""
    
    from sqlalchemy import func
    
    # Get department filter for non-superadmin users
    department_filter = None
    if not current_user.is_superadmin():
        department_filter = current_user.department_id
    
    # Get student count
    if department_filter:
        total_students = Student.query.filter_by(department_id=department_filter).count()
    else:
        total_students = db.session.query(func.count(Student.id)).scalar() or 0
    
    # Get inventory stats
    inventory = Inventory.query.all()
    total_gowns = sum(inv.total_count for inv in inventory)
    issued_gowns = sum(inv.get_issued_count() for inv in inventory)
    available_gowns = total_gowns - issued_gowns
    
    # Get transaction counts with department filter
    if department_filter:
        active_transactions = db.session.query(func.count(Transaction.id)).join(
            Student, Transaction.student_id == Student.id
        ).filter(
            Transaction.status == 'Issued',
            Student.department_id == department_filter
        ).scalar() or 0
        
        returned_transactions = db.session.query(func.count(Transaction.id)).join(
            Student, Transaction.student_id == Student.id
        ).filter(
            Transaction.status == 'Returned',
            Student.department_id == department_filter
        ).scalar() or 0
    else:
        active_transactions = db.session.query(func.count(Transaction.id)).filter(
            Transaction.status == 'Issued'
        ).scalar() or 0
        
        returned_transactions = db.session.query(func.count(Transaction.id)).filter(
            Transaction.status == 'Returned'
        ).scalar() or 0
    
    # Calculate overdue transactions
    from datetime import date
    today = date.today()
    overdue_count = db.session.query(func.count(Transaction.id)).filter(
        Transaction.status == 'Issued',
        Transaction.expected_return_date < today
    ).scalar() or 0
    
    # Get recent transactions - filtered by department
    if department_filter:
        recent_transactions = Transaction.query.options(
            db.joinedload(Transaction.student)
        ).join(Student, Transaction.student_id == Student.id).filter(
            Student.department_id == department_filter
        ).order_by(Transaction.created_at.desc()).limit(10).all()
    else:
        recent_transactions = Transaction.query.options(
            db.joinedload(Transaction.student)
        ).order_by(Transaction.created_at.desc()).limit(10).all()
    
    # Get inventory summary for display
    inventory_summary = []
    for inv in inventory:
        inventory_summary.append({
            'name': inv.gown_type,
            'total': inv.total_count,
            'available': inv.get_available_count(),
            'issued': inv.get_issued_count()
        })
    
    # Get greeting
    time_greeting, funny_greeting = get_greeting()
    
    return render_template(
        'dashboard.html',
        time_greeting=time_greeting,
        funny_greeting=funny_greeting,
        total_students=total_students,
        total_gowns=total_gowns,
        available_gowns=available_gowns,
        issued_gowns=issued_gowns,
        active_transactions=active_transactions,
        returned_transactions=returned_transactions,
        overdue_count=overdue_count,
        recent_transactions=recent_transactions,
        inventory_summary=inventory_summary,
        department_name=current_user.department.name if current_user.department else None
    )


@main_bp.route('/audit-logs')
@login_required
def audit_logs():
    """View audit logs (SuperAdmin only)"""
    if not current_user.is_superadmin():
        flash('Access denied. SuperAdmin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 30
    
    # Filter by action if provided
    action_filter = request.args.get('action', '')
    query = AuditLog.query
    
    if action_filter:
        query = query.filter(AuditLog.action == action_filter)
    
    logs = query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get unique actions for filter dropdown
    actions = db.session.query(AuditLog.action).distinct().all()
    actions = [a[0] for a in actions]
    
    return render_template('audit_logs.html', logs=logs, actions=actions, action_filter=action_filter)


@main_bp.route('/export/transactions')
@login_required
def export_transactions():
    """Export transactions to CSV"""
    # Get all transactions
    transactions = Transaction.query.order_by(Transaction.created_at.desc()).all()
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'ID', 'Student Index', 'Student Name', 'Gown Type',
        'Issue Date', 'Expected Return', 'Actual Return', 'Status'
    ])
    
    # Data
    for t in transactions:
        writer.writerow([
            t.id,
            t.student.index_number if t.student else '',
            t.student.full_name if t.student else '',
            t.gown_type,
            t.issue_date.strftime('%Y-%m-%d') if t.issue_date else '',
            t.expected_return_date.strftime('%Y-%m-%d') if t.expected_return_date else '',
            t.actual_return_date.strftime('%Y-%m-%d') if t.actual_return_date else '',
            t.status
        ])
    
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=transactions.csv'}
    )


@main_bp.route('/api/student/lookup/<index_number>')
@login_required
def lookup_student(index_number):
    """API endpoint to lookup student by index number"""
    student = Student.query.filter_by(index_number=index_number).first()
    
    if not student:
        return jsonify({
            'status': 'not_found',
            'message': 'Student not found'
        })
    
    # Check if student has active rental
    has_active_rental = student.has_active_rental()
    active_tx = student.get_active_transaction()
    
    return jsonify({
        'status': 'found',
        'id': student.id,
        'index_number': student.index_number,
        'full_name': student.full_name,
        'programme': student.programme,
        'level': student.level,
        'department': student.department.name if student.department else None,
        'has_active_rental': has_active_rental,
        'active_gown_type': active_tx.gown_type if active_tx else None
    })


@main_bp.route('/api/student/search')
@login_required
def search_students():
    """API endpoint to search students by index number (for autocomplete)"""
    query = request.args.get('q', '')
    
    if len(query) < 2:
        return jsonify([])
    
    # Build base query
    base_query = Student.query
    
    # Filter by department if user is not a superadmin
    if not current_user.is_superadmin() and current_user.department_id:
        base_query = base_query.filter(Student.department_id == current_user.department_id)
    
    # Search students
    students = base_query.filter(
        Student.index_number.ilike(f'%{query}%')
    ).limit(10).all()
    
    return jsonify([{
        'id': s.id,
        'index_number': s.index_number,
        'full_name': s.full_name,
        'department': s.department.name if s.department else None,
        'has_active_rental': s.has_active_rental()
    } for s in students])
