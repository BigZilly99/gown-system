"""
University Gown Management System - Transaction Routes (Simplified)
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta

from app import db
from app.models import Student, Inventory, Transaction, AuditLog
from app.forms import IssueGownForm, ReturnGownForm
from app.access_control import admin_required

transactions_bp = Blueprint('transactions', __name__, url_prefix='/transactions')


@transactions_bp.route('/search-students')
@login_required
@admin_required
def search_students():
    """Search students by index number or name (for issuing gowns)"""
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify([])
    
    # Build base query
    base_query = Student.query
    
    # Filter by department if user is not a superadmin
    if not current_user.is_superadmin() and current_user.department_id:
        base_query = base_query.filter(Student.department_id == current_user.department_id)
    
    # Search students
    students = base_query.filter(
        db.or_(
            Student.index_number.ilike(f'%{query}%'),
            Student.full_name.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    # Return results
    results = []
    for s in students:
        # Check if student has active rental
        has_rental = s.has_active_rental()
        active_tx = s.get_active_transaction()
        
        results.append({
            'id': s.id,
            'index_number': s.index_number,
            'full_name': s.full_name,
            'level': s.level,
            'programme': s.programme,
            'department': s.department.name if s.department else None,
            'can_rent': not has_rental,
            'has_rental': has_rental,
            'active_gown_type': active_tx.gown_type if active_tx else None
        })
    
    return jsonify(results)


@transactions_bp.route('/')
@login_required
@admin_required
def index():
    """List all transactions (Admin & SuperAdmin)"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filters
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')
    
    query = Transaction.query
    
    # Filter by department if user is not a superadmin
    if not current_user.is_superadmin() and current_user.department_id:
        query = query.join(Student).filter(Student.department_id == current_user.department_id)
    
    if status_filter:
        query = query.filter(Transaction.status == status_filter)
    
    if search:
        query = query.join(Student).filter(
            (Student.index_number.ilike(f'%{search}%')) |
            (Student.full_name.ilike(f'%{search}%'))
        )
    
    transactions = query.order_by(Transaction.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template(
        'transactions/index.html',
        transactions=transactions,
        status_filter=status_filter,
        search=search
    )


@transactions_bp.route('/active')
@login_required
@admin_required
def active():
    """List active transactions (Admin & SuperAdmin)"""
    transactions = Transaction.query.filter(
        Transaction.status == 'Issued'
    ).order_by(Transaction.expected_return_date).all()
    
    return render_template('transactions/active.html', transactions=transactions)


@transactions_bp.route('/overdue')
@login_required
@admin_required
def overdue():
    """List overdue transactions (Admin & SuperAdmin)"""
    today = date.today()
    transactions = Transaction.query.filter(
        Transaction.status == 'Issued',
        Transaction.expected_return_date < today
    ).order_by(Transaction.expected_return_date).all()
    
    return render_template('transactions/overdue.html', transactions=transactions)


@transactions_bp.route('/issue', methods=['GET', 'POST'])
@login_required
@admin_required
def issue():
    """Issue gown to student (Admin & SuperAdmin)"""
    form = IssueGownForm()
    
    # Pre-populate return date (7 days from now)
    if request.method == 'GET':
        form.expected_return_date.data = date.today() + timedelta(days=7)
    
    if form.validate_on_submit():
        # Find student
        try:
            student_id = int(form.student_id.data)
        except ValueError:
            flash('Please select a valid student.', 'danger')
            return render_template('transactions/issue.html', form=form)
        
        student = Student.query.get(student_id)
        
        if not student:
            flash('Please select a valid student.', 'danger')
            return render_template('transactions/issue.html', form=form)
        
        # Check if student already has active rental
        if student.has_active_rental():
            flash(f'Student {student.full_name} already has an active gown rental.', 'danger')
            return render_template('transactions/issue.html', form=form)
        
        # Check inventory availability
        inventory = Inventory.query.filter_by(gown_type=form.gown_type.data).first()
        if not inventory:
            flash('Invalid gown type selected.', 'danger')
            return render_template('transactions/issue.html', form=form)
        
        available = inventory.get_available_count()
        if available <= 0:
            flash(f'No available {form.gown_type.data} in inventory.', 'danger')
            return render_template('transactions/issue.html', form=form)
        
        # Create transaction
        transaction = Transaction(
            student_id=student.id,
            gown_type=form.gown_type.data,
            issued_by=current_user.id,
            expected_return_date=form.expected_return_date.data,
            status='Issued',
            notes=form.notes.data
        )
        
        db.session.add(transaction)
        
        # Force commit to ensure it's saved
        db.session.commit()
        
        # Log the action
        log = AuditLog(
            user_id=current_user.id,
            action='Issue Gown',
            entity_type='Transaction',
            entity_id=transaction.id,
            details=f'Issued {form.gown_type.data} to student {student.index_number}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Gown issued to {student.full_name} successfully!', 'success')
        return redirect(url_for('transactions.index'))
    
    return render_template('transactions/issue.html', form=form)


@transactions_bp.route('/return', methods=['GET', 'POST'])
@login_required
@admin_required
def return_gown():
    """Return gown from student (Admin & SuperAdmin)"""
    form = ReturnGownForm()
    
    if form.validate_on_submit():
        # Find student
        try:
            student_id = int(form.student_id.data)
        except ValueError:
            flash('Please select a valid student.', 'danger')
            return render_template('transactions/return.html', form=form)
        
        student = Student.query.get(student_id)
        
        if not student:
            flash('Please select a valid student.', 'danger')
            return render_template('transactions/return.html', form=form)
        
        # Get active transaction
        transaction = student.get_active_transaction()
        
        if not transaction:
            flash(f'Student {student.full_name} has no active gown to return.', 'danger')
            return render_template('transactions/return.html', form=form)
        
        # Update transaction
        transaction.actual_return_date = datetime.utcnow()
        transaction.status = 'Returned'
        transaction.notes = (transaction.notes or '') + f'\nReturn notes: {form.notes.data}' if form.notes.data else transaction.notes
        
        # Log the action
        log = AuditLog(
            user_id=current_user.id,
            action='Return Gown',
            entity_type='Transaction',
            entity_id=transaction.id,
            details=f'Returned {transaction.gown_type} from student {student.index_number}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Gown returned successfully!', 'success')
        return redirect(url_for('transactions.index'))
    
    return render_template('transactions/return.html', form=form)


@transactions_bp.route('/<int:transaction_id>')
@login_required
def view(transaction_id):
    """View transaction details"""
    transaction = Transaction.query.get_or_404(transaction_id)
    
    return render_template('transactions/view.html', transaction=transaction)


@transactions_bp.route('/receipt/<int:transaction_id>')
@login_required
def receipt(transaction_id):
    """View transaction receipt"""
    transaction = Transaction.query.get_or_404(transaction_id)
    
    return render_template('transactions/receipt.html', transaction=transaction)


@transactions_bp.route('/quick-issue', methods=['POST'])
@login_required
@admin_required
def quick_issue():
    """Quick issue gown via AJAX"""
    student_index = request.form.get('student_index')
    gown_type = request.form.get('gown_type')
    return_date = request.form.get('return_date')
    
    # Find student
    student = Student.query.filter_by(index_number=student_index).first()
    if not student:
        return {'success': False, 'error': f'Student {student_index} not found'}, 404
    
    # Check if student has active rental
    if student.has_active_rental():
        return {'success': False, 'error': 'Student already has active rental'}, 400
    
    # Check inventory
    inventory = Inventory.query.filter_by(gown_type=gown_type).first()
    if not inventory or inventory.get_available_count() <= 0:
        return {'success': False, 'error': f'No available {gown_type} in inventory'}, 400
    
    # Parse return date
    try:
        expected_return = datetime.strptime(return_date, '%Y-%m-%d').date()
    except:
        return {'success': False, 'error': 'Invalid return date format'}, 400
    
    # Create transaction
    transaction = Transaction(
        student_id=student.id,
        gown_type=gown_type,
        issued_by=current_user.id,
        expected_return_date=expected_return,
        status='Issued'
    )
    
    db.session.add(transaction)
    
    # Log
    log = AuditLog(
        user_id=current_user.id,
        action='Quick Issue',
        entity_type='Transaction',
        details=f'Issued {gown_type} to {student.index_number}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    
    db.session.commit()
    
    return {
        'success': True,
        'message': f'Gown issued to {student.full_name}',
        'transaction_id': transaction.id
    }


@transactions_bp.route('/quick-return', methods=['POST'])
@login_required
@admin_required
def quick_return():
    """Quick return gown via AJAX"""
    student_index = request.form.get('student_index')
    
    # Find student
    student = Student.query.filter_by(index_number=student_index).first()
    if not student:
        return {'success': False, 'error': f'Student {student_index} not found'}, 404
    
    # Get active transaction
    transaction = student.get_active_transaction()
    if not transaction:
        return {'success': False, 'error': 'No active transaction found'}, 404
    
    # Update
    transaction.actual_return_date = datetime.utcnow()
    transaction.status = 'Returned'
    
    # Log
    log = AuditLog(
        user_id=current_user.id,
        action='Quick Return',
        entity_type='Transaction',
        details=f'Returned {transaction.gown_type} from {student.index_number}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    
    db.session.commit()
    
    return {
        'success': True,
        'message': f'Gown returned successfully'
    }
