# -*- coding: utf-8 -*-
"""
app1/middleware.py
==================
Role-Based Access Control middleware for Smart AI Attendance System.

Provides a global, view-agnostic safety net that enforces access rules for
every incoming request, independent of view-level decorators.

Role mapping:
  - Superuser  → unrestricted access everywhere
  - Staff/Admin → can reach all admin/staff paths
  - Student     → can only reach student-specific paths
  - Public      → login & home pages only (unauthenticated traffic)

Redirect rules when access is denied:
  - Unauthenticated  → /login/
  - Student hitting staff route → /student-dashboard/
  - Staff hitting student route → /admin-dashboard/
"""

from django.shortcuts import redirect


# ── Allow-list for paths that NEVER require authentication ──────────────────
PUBLIC_PATHS = {
    '/',
    '/login/',
    '/register_success/',
}

# ── Prefixes that only staff/admin/superusers may visit ────────────────────
STAFF_PREFIXES = (
    '/admin-dashboard/',
    '/students/',
    '/register_student/',
    '/mark_attendance',
    '/students-fees/',
    '/fee/',
    '/payment/',
    '/late_checkin_policy_list/',
    '/late-checkin-policies/',
    '/delete-late-checkin-policy/',
    '/camera-config/',
    '/admin-courses/',
    '/email-configs/',
    '/semesters/',
    '/departments/',
    '/sessions/',
    '/settings',
    '/send_attendance_notifications',
    '/teachers/',
    '/assigned-classes/',
    '/monitor-cameras/',
    '/student/edit/',
    '/student-attendance-list/',
    '/student_attendance_list/',
)

# ── Prefixes reserved for superusers only ──────────────────────────────────
SUPERUSER_PREFIXES = (
    '/admin/',
    '/leaves/',
)

# ── Prefixes that belong to students only ──────────────────────────────────
STUDENT_PREFIXES = (
    '/student-dashboard/',
    '/attendance/',
    '/student-fee-detail/',
    '/apply_leave/',
    '/Student_leave_list/',
)

# ── Shared paths (any authenticated user) ─────────────────────────────────
AUTHENTICATED_PREFIXES = (
    '/logout/',
    '/courses/',
    '/teacher/',
    '/teacher-dashboard/',
)


class RoleBasedAccessMiddleware:
    """
    Light-weight middleware that redirects requests that violate the
    role-based access policy without raising 403 / 404 errors.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        user = request.user

        # 1️⃣  Public paths – always allowed
        if path in PUBLIC_PATHS:
            return self.get_response(request)

        # 2️⃣  Django admin – handled internally; skip our middleware
        if path.startswith('/admin/'):
            return self.get_response(request)

        # 3️⃣  Unauthenticated – send to login
        if not user.is_authenticated:
            return redirect('login')

        # 4️⃣  Superuser – no restrictions
        if user.is_superuser:
            return self.get_response(request)

        # 5️⃣  Superuser-only paths – block non-superusers
        if any(path.startswith(p) for p in SUPERUSER_PREFIXES):
            if not user.is_superuser:
                return self._unauthorized_redirect(request)
            return self.get_response(request)

        # 6️⃣  Staff-only paths – block plain students
        if any(path.startswith(p) for p in STAFF_PREFIXES):
            if user.is_staff:
                return self.get_response(request)
            return self._unauthorized_redirect(request)

        # 7️⃣  Student-only paths – block staff
        if any(path.startswith(p) for p in STUDENT_PREFIXES):
            if self._is_student(user):
                return self.get_response(request)
            return self._unauthorized_redirect(request)

        # 8️⃣  Shared authenticated paths – already authenticated ✓
        if any(path.startswith(p) for p in AUTHENTICATED_PREFIXES):
            return self.get_response(request)

        # 9️⃣  Fallback – let the view's own decorator decide
        return self.get_response(request)

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _is_student(user) -> bool:
        # The Student model uses related_name='student_profile'
        # We also treat any non-staff, non-superuser user as a student
        if user.is_staff or user.is_superuser:
            return False
        return hasattr(user, 'student_profile')

    @staticmethod
    def _unauthorized_redirect(request):
        """Redirect to the correct dashboard based on the user's role."""
        user = request.user
        if user.is_staff or user.is_superuser:
            return redirect('admin_dashboard')
        # Default: treat as student
        return redirect('student_dashboard')
