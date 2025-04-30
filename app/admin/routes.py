# app/admin/routes.py
import logging
import calendar
from datetime import datetime, timedelta

from flask import render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from sqlalchemy import extract

from app.extensions import db
from app.models import User, UploadedDocument, QueryHistory
from . import admin_bp, admin_required

logger = logging.getLogger(__name__)

# Admin dashboard
@admin_bp.route('/dashboard')
@login_required
@admin_required
def admin_dashboard():
    # Get the timeframe and search query from the request
    timeframe    = request.args.get("timeframe", "day").lower()
    search_query = request.args.get("q", "").strip()
    now          = datetime.utcnow()

    # Global metrics
    total_users     = User.query.count()
    total_documents = UploadedDocument.query.count()
    total_queries   = QueryHistory.query.count()

    # count of distinct users who ran 1 or more queries in the last 7 days
    week_ago     = now - timedelta(days=7)
    active_users = (
        db.session.query(QueryHistory.user_id)
                  .filter(QueryHistory.timestamp >= week_ago)
                  .distinct()
                  .count()
    )

    # Build timeseries data
    if timeframe == "month":
        year, month = now.year, now.month
        labels = [calendar.month_abbr[m] for m in range(1, month + 1)]
        user_growth = [
            # Count users who joined in each month of the current year
            User.query.filter(
                extract('year', User.date_joined) == year,
                extract('month', User.date_joined) == m
            ).count()
            for m in range(1, month + 1)
        ]
        # Count documents uploaded in each month of the current year
        doc_uploads = [
            UploadedDocument.query.filter(
                extract('year', UploadedDocument.upload_date) == year,
                extract('month', UploadedDocument.upload_date) == m
            ).count()
            for m in range(1, month + 1)
        ]
        # Count queries made in each month of the current year
        query_counts = [
            QueryHistory.query.filter(
                extract('year', QueryHistory.timestamp) == year,
                extract('month', QueryHistory.timestamp) == m
            ).count()
            for m in range(1, month + 1)
        ]
    elif timeframe == "week":
        # For weekly data - last 4 weeks
        weeks = 4
        delta = timedelta(weeks=1)
        start = now - delta * weeks
        labels = []
        user_growth = []
        doc_uploads = []
        query_counts = []
        # For each week, get the start date and count users/documents/queries
        for _ in range(weeks):
            labels.append(start.strftime("%Y-%m-%d"))
            user_growth.append(
                User.query.filter(
                    User.date_joined >= start,
                    User.date_joined <  start + delta
                ).count()
            )
            doc_uploads.append(
                UploadedDocument.query.filter(
                    UploadedDocument.upload_date >= start,
                    UploadedDocument.upload_date <  start + delta
                ).count()
            )
            query_counts.append(
                QueryHistory.query.filter(
                    QueryHistory.timestamp >= start,
                    QueryHistory.timestamp <  start + delta
                ).count()
            )
            start += delta
    else:  
        # For daily data - last 7 days
        days = 7
        delta = timedelta(days=1)
        start = now - delta * days
        labels = []
        user_growth = []
        doc_uploads = []
        query_counts = []
        # For each day, get the start date and count users/documents/queries
        for _ in range(days):
            labels.append(start.strftime("%Y-%m-%d"))
            user_growth.append(
                User.query.filter(
                    User.date_joined >= start,
                    User.date_joined <  start + delta
                ).count()
            )
            doc_uploads.append(
                UploadedDocument.query.filter(
                    UploadedDocument.upload_date >= start,
                    UploadedDocument.upload_date <  start + delta
                ).count()
            )
            query_counts.append(
                QueryHistory.query.filter(
                    QueryHistory.timestamp >= start,
                    QueryHistory.timestamp <  start + delta
                ).count()
            )
            start += delta

    # Prepare data for the graph
    graph_data = {
        "user_growth":   {"labels": labels, "values": user_growth},
        "doc_uploads":   {"labels": labels, "values": doc_uploads},
        "query_counts":  {"labels": labels, "values": query_counts},
    }

    # User lookup
    user_lookup = []
    if search_query:
        results = User.query.filter(
            (User.username.ilike(f"%{search_query}%")) |
            (User.email.ilike(f"%{search_query}%"))
        ).all()
        for u in results:
            user_lookup.append({
                "id":            u.id,
                "username":      u.username,
                "email":         u.email,
                "is_admin":      u.is_admin,
                "doc_count":     UploadedDocument.query.filter_by(user_id=u.id).count(),
                "query_count":   QueryHistory.query.filter_by(user_id=u.id).count(),
                "date_joined":   u.date_joined.strftime("%Y-%m-%d"),
                "last_activity": u.last_activity.strftime("%Y-%m-%d %H:%M:%S"),
            })

    # Render the admin dashboard template
    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_documents=total_documents,
        total_queries=total_queries,
        active_users=active_users,
        graph_data=graph_data,
        timeframe=timeframe,
        search_query=search_query,
        user_lookup=user_lookup,
    )

# Promote user to admin
@admin_bp.route('/promote_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def promote_user(user_id):
    # Get the user by ID
    u = User.query.get_or_404(user_id)
    # Check if the user is already an admin
    if u.is_admin:
        flash(f"User {u.username} is already an admin.")
    else:
        # Give admin privileges by changing boolean value
        u.is_admin = True
        try:
            db.session.commit()
            flash(f"User {u.username} promoted to admin successfully.")
        except Exception as e:
            db.session.rollback()
            logger.error("Error promoting user: %s", e)
            flash("There was an error promoting this user.")
    # Redirect to the admin dashboard
    return redirect(url_for('admin.admin_dashboard'))

# Demote user from admin (admin self-demotion only)
@admin_bp.route('/demote_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def demote_user(user_id):
    # Get the user by ID
    u = User.query.get_or_404(user_id)
    # Only allow self-demotion
    if u.id != current_user.id:
        flash("You cannot demote another admin.")
    else:
        # Remove admin privileges by changing boolean value
        u.is_admin = False
        try:
            db.session.commit()
            flash("You have demoted yourself.")
            # Redirect to logout after self-demotion
            return redirect(url_for('auth.logout'))
        except Exception as e:
            db.session.rollback()
            logger.error("Error demoting user: %s", e)
            flash("Error demoting your account.")
    # Redirect to the admin dashboard
    return redirect(url_for('admin.admin_dashboard'))