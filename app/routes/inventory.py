"""
University Gown Management System - Inventory Routes (SuperAdmin Only)
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime

from app import db
from app.models import Inventory, AuditLog
from app.forms import InventoryForm
from app.access_control import superadmin_required

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')


@inventory_bp.route('/')
@login_required
@superadmin_required
def index():
    """View and manage inventory (SuperAdmin only)"""
    inventory_items = Inventory.query.all()
    
    # Ensure both inventory types exist
    gown_types = ['GCTU Gowns', 'Gowns Rented from Out of Campus']
    for gt in gown_types:
        existing = Inventory.query.filter_by(gown_type=gt).first()
        if not existing:
            new_inv = Inventory(gown_type=gt, total_count=1)
            db.session.add(new_inv)
    db.session.commit()
    
    # Refresh after ensuring existence
    inventory_items = Inventory.query.all()
    
    return render_template('inventory/index.html', inventory=inventory_items)


@inventory_bp.route('/edit/<int:inventory_id>', methods=['GET', 'POST'])
@login_required
@superadmin_required
def edit(inventory_id):
    """Edit inventory count (SuperAdmin only)"""
    inventory = Inventory.query.get_or_404(inventory_id)
    form = InventoryForm(obj=inventory)
    
    if form.validate_on_submit():
        # Check if new count is less than currently issued
        issued_count = inventory.get_issued_count()
        if form.total_count.data < issued_count:
            flash(f'Cannot set total to {form.total_count.data}. Currently {issued_count} gowns are issued.', 'danger')
            return render_template('inventory/edit.html', form=form, inventory=inventory)
        
        inventory.total_count = form.total_count.data
        db.session.commit()
        
        # Log the action
        log = AuditLog(
            user_id=current_user.id,
            action='Update Inventory',
            entity_type='Inventory',
            entity_id=inventory.id,
            details=f'Updated {inventory.gown_type} total count to {inventory.total_count}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Inventory updated successfully!', 'success')
        return redirect(url_for('inventory.index'))
    
    return render_template('inventory/edit.html', form=form, inventory=inventory)
