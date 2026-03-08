"""
University Gown Management System - Gown Management Routes
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime

from app import db
from app.models import Gown, GownType, AuditLog
from app.forms import GownForm, GownTypeForm
from app.access_control import superadmin_required, admin_required

gowns_bp = Blueprint('gowns', __name__, url_prefix='/gowns')


@gowns_bp.route('/')
@login_required
@admin_required
def index():
    """List all gowns (Admin & SuperAdmin)"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filters
    status_filter = request.args.get('status', '')
    type_filter = request.args.get('type', '')
    search = request.args.get('search', '')
    
    query = Gown.query
    
    if status_filter:
        query = query.filter(Gown.status == status_filter)
    
    if type_filter:
        query = query.filter(Gown.gown_type_id == type_filter)
    
    if search:
        # Convert search to integer for ID search, or use string for notes search
        try:
            gown_id = int(search)
            query = query.filter(Gown.id == gown_id)
        except ValueError:
            # If not a valid integer, search in notes
            query = query.filter(Gown.notes.ilike(f'%{search}%'))
    
    gowns = query.order_by(Gown.id).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get gown types for filter
    gown_types = GownType.query.all()
    
    return render_template(
        'gowns/index.html',
        gowns=gowns,
        gown_types=gown_types,
        status_filter=status_filter,
        type_filter=type_filter,
        search=search
    )


@gowns_bp.route('/types')
@login_required
def types():
    """List all gown types"""
    if not current_user.is_superadmin():
        flash('Access denied. SuperAdmin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    gown_types = GownType.query.all()
    
    # Add counts to each type
    for gt in gown_types:
        gt.total_count = gt.get_total_count()
        gt.available_count = gt.get_available_count()
        gt.issued_count = gt.get_issued_count()
    
    return render_template('gowns/types.html', gown_types=gown_types)


@gowns_bp.route('/types/new', methods=['GET', 'POST'])
@login_required
def new_type():
    """Create new gown type"""
    if not current_user.is_superadmin():
        flash('Access denied. SuperAdmin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    form = GownTypeForm()
    
    if form.validate_on_submit():
        gown_type = GownType(
            name=form.name.data,
            description=form.description.data,
            deposit_amount=form.deposit_amount.data,
            rental_fee=form.rental_fee.data or 0.0
        )
        
        db.session.add(gown_type)
        db.session.commit()
        
        # Log the action
        log = AuditLog(
            user_id=current_user.id,
            action='Create Gown Type',
            entity_type='GownType',
            entity_id=gown_type.id,
            details=f'Created gown type {gown_type.name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Gown type {gown_type.name} created successfully!', 'success')
        return redirect(url_for('gowns.types'))
    
    return render_template('gowns/type_form.html', form=form, title='Add Gown Type')


@gowns_bp.route('/types/<int:type_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_type(type_id):
    """Edit gown type"""
    if not current_user.is_superadmin():
        flash('Access denied. SuperAdmin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    gown_type = GownType.query.get_or_404(type_id)
    form = GownTypeForm(obj=gown_type)
    
    if form.validate_on_submit():
        gown_type.name = form.name.data
        gown_type.description = form.description.data
        gown_type.deposit_amount = form.deposit_amount.data
        gown_type.rental_fee = form.rental_fee.data or 0.0
        
        db.session.commit()
        
        # Log the action
        log = AuditLog(
            user_id=current_user.id,
            action='Edit Gown Type',
            entity_type='GownType',
            entity_id=gown_type.id,
            details=f'Edited gown type {gown_type.name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Gown type {gown_type.name} updated successfully!', 'success')
        return redirect(url_for('gowns.types'))
    
    return render_template('gowns/type_form.html', form=form, title=f'Edit Gown Type: {gown_type.name}')


@gowns_bp.route('/types/<int:type_id>/delete', methods=['POST'])
@login_required
def delete_type(type_id):
    """Delete gown type"""
    if not current_user.is_superadmin():
        flash('Access denied. SuperAdmin privileges required.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    gown_type = GownType.query.get_or_404(type_id)
    
    # Check if there are gowns of this type
    if gown_type.get_total_count() > 0:
        flash('Cannot delete gown type with existing gowns.', 'danger')
        return redirect(url_for('gowns.types'))
    
    name = gown_type.name
    
    # Log before deletion
    log = AuditLog(
        user_id=current_user.id,
        action='Delete Gown Type',
        entity_type='GownType',
        entity_id=gown_type.id,
        details=f'Deleted gown type {name}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    
    db.session.delete(gown_type)
    db.session.commit()
    
    flash(f'Gown type {name} deleted successfully!', 'success')
    return redirect(url_for('gowns.types'))


@gowns_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    """Create new gown"""
    form = GownForm()
    
    # Populate gown types
    gown_types = GownType.query.all()
    form.gown_type.choices = [(0, 'Select Gown Type')] + [(gt.id, gt.name) for gt in gown_types]
    
    if not gown_types:
        flash('Please create a gown type first.', 'warning')
        return redirect(url_for('gowns.types'))
    
    if form.validate_on_submit():
        gown = Gown(
            gown_type_id=form.gown_type.data,
            size=form.size.data,
            status=form.status.data,
            condition=form.condition.data,
            notes=form.notes.data,
            purchase_date=form.purchase_date.data
        )
        
        db.session.add(gown)
        db.session.commit()
        
        # Log the action
        log = AuditLog(
            user_id=current_user.id,
            action='Create Gown',
            entity_type='Gown',
            entity_id=gown.id,
            details=f'Created gown {gown.id}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Gown created successfully!', 'success')
        return redirect(url_for('gowns.index'))
    
    return render_template('gowns/form.html', form=form, title='Add Gown')


@gowns_bp.route('/<int:gown_id>')
@login_required
def view(gown_id):
    """View gown details"""
    gown = Gown.query.get_or_404(gown_id)
    
    # Note: There is no direct relationship between Gown and Transaction
    # Transaction.gown_type is a string field, not a foreign key to Gown
    # To get transactions for this gown, you would need to filter by gown_type
    transactions = []
    
    return render_template('gowns/view.html', gown=gown, transactions=transactions)


@gowns_bp.route('/<int:gown_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(gown_id):
    """Edit gown"""
    gown = Gown.query.get_or_404(gown_id)
    form = GownForm(obj=gown)
    
    # Populate gown types
    gown_types = GownType.query.all()
    form.gown_type.choices = [(gt.id, gt.name) for gt in gown_types]
    
    if form.validate_on_submit():
        gown.gown_type_id = form.gown_type.data
        gown.size = form.size.data
        gown.status = form.status.data
        gown.condition = form.condition.data
        gown.notes = form.notes.data
        gown.purchase_date = form.purchase_date.data
        
        db.session.commit()
        
        # Log the action
        log = AuditLog(
            user_id=current_user.id,
            action='Edit Gown',
            entity_type='Gown',
            entity_id=gown.id,
            details=f'Edited gown {gown.id}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Gown updated successfully!', 'success')
        return redirect(url_for('gowns.index'))
    
    return render_template('gowns/form.html', form=form, title=f'Edit Gown: {gown.id}')


@gowns_bp.route('/<int:gown_id>/delete', methods=['POST'])
@login_required
def delete(gown_id):
    """Delete gown"""
    gown = Gown.query.get_or_404(gown_id)
    
    # Check if gown is currently issued
    if gown.status == 'Issued':
        flash('Cannot delete a gown that is currently issued.', 'danger')
        return redirect(url_for('gowns.index'))
    
    gown_id = gown.id
    
    # Log before deletion
    log = AuditLog(
        user_id=current_user.id,
        action='Delete Gown',
        entity_type='Gown',
        entity_id=gown.id,
        details=f'Deleted gown {gown_id}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    
    db.session.delete(gown)
    db.session.commit()
    
    flash(f'Gown {gown_id} deleted successfully!', 'success')
    return redirect(url_for('gowns.index'))


@gowns_bp.route('/lookup/<int:gown_id>')
@login_required
def lookup(gown_id):
    """Look up gown by ID"""
    gown = Gown.query.get_or_404(gown_id)
    
    return {
        'id': gown.id,
        'type': gown.gown_type.name if gown.gown_type else '',
        'type_id': gown.gown_type_id,
        'size': gown.size,
        'status': gown.status,
        'condition': gown.condition,
        'is_available': gown.status == 'Available'
    }


@gowns_bp.route('/available')
@login_required
def available():
    """Get available gowns (JSON)"""
    type_id = request.args.get('type_id', type=int)
    
    query = Gown.query.filter_by(status='Available')
    
    if type_id:
        query = query.filter_by(gown_type_id=type_id)
    
    gowns = query.all()
    
    return {
        'results': [{
            'id': g.id,
            'type': g.gown_type.name if g.gown_type else '',
            'size': g.size
        } for g in gowns]
    }
