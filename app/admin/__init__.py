# app/admin/__init__.py
from flask import Blueprint

# Defines the admin blueprint; routes are registered in routes.py
admin_bp = Blueprint(
    'admin',
    __name__,
    url_prefix='/admin',
    template_folder='templates/admin'
)

# Expose admin_required decorator so it can be imported elsewhere if needed
def admin_required(view_func):
    # Restrict access to admin users only
    from functools import wraps
    from flask import flash, redirect, url_for
    from flask_login import current_user

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        # Block access if the user is not authenticated or not an admin
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Admin access required.")
            return redirect(url_for('dashboard'))
        # Otherwise, all the original view function§
        return view_func(*args, **kwargs)
    return wrapped