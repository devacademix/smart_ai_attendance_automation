# -*- coding: utf-8 -*-
"""
app1/permissions.py
===================
Reusable permission decorators for Smart AI Attendance System.

Usage:
    from .permissions import staff_required, admin_required, student_required

    @staff_required
    def my_staff_view(request): ...

    @admin_required
    def my_admin_view(request): ...

    @student_required
    def my_student_view(request): ...
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


# ───────────────────────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────────────────────

def _has_student_profile(user):
    """
    Return True if the user has an associated Student profile.
    The Student model uses:  user = OneToOneField(User, related_name='student_profile')
    A non-staff, non-superuser user is considered a student.
    """
    if user.is_staff or user.is_superuser:
        return False
    return hasattr(user, 'student_profile')


def _redirect_unauthorized(request):
    """Redirect to the proper dashboard when the user lacks permission."""
    user = request.user
    if user.is_staff or user.is_superuser:
        messages.warning(request, "You do not have permission to access that page.")
        return redirect('admin_dashboard')
    # Default: student
    messages.warning(request, "You are not authorized to access that page.")
    return redirect('student_dashboard')


# ───────────────────────────────────────────────────────────────────────────────
# Concrete decorators
# ───────────────────────────────────────────────────────────────────────────────

def admin_required(view_func):
    """
    Allow only superusers (is_superuser=True).
    Everyone else is redirected appropriately.
    """
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        return _redirect_unauthorized(request)
    return _wrapped


def staff_required(view_func):
    """
    Allow staff AND superusers (is_staff=True or is_superuser=True).
    Plain student accounts are redirected to student_dashboard.
    """
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if request.user.is_staff or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        return _redirect_unauthorized(request)
    return _wrapped


def student_required(view_func):
    """
    Allow only users that have a Student profile.
    Staff/admin are redirected to admin_dashboard.
    """
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if _has_student_profile(request.user):
            return view_func(request, *args, **kwargs)
        return _redirect_unauthorized(request)
    return _wrapped
