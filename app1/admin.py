from django.contrib import admin
from .models import (
    Semester, Department, Session, Course, Lesson, Student, 
    LateCheckInPolicy, Attendance, Fee, FeePayment, CameraConfiguration,EmailConfig,Leave, Teacher, AssignedClass
)

# Semester Model Admin
@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'description')
    search_fields = ('name',)
    ordering = ('start_date',)

# Department Model Admin
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

# Session Model Admin
@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date')
    search_fields = ('name',)
    ordering = ('start_date',)

# Course Model Admin
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'session', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('session',)
    ordering = ('created_at',)

# Lesson Model Admin
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('course', 'title', 'created_at', 'updated_at')
    search_fields = ('title',)
    list_filter = ('course',)

# Student Model Admin
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'roll_no', 'session', 'email', 'phone_number', 'authorized')
    search_fields = ('name', 'roll_no', 'email')
    list_filter = ('session', 'authorized')
    ordering = ('name',)

# LateCheckInPolicy Model Admin
@admin.register(LateCheckInPolicy)
class LateCheckInPolicyAdmin(admin.ModelAdmin):
    list_display = ('student', 'start_time', 'description')
    search_fields = ('student__name',)

# Attendance Model Admin
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'check_in_time', 'check_out_time', 'status', 'is_late')
    search_fields = ('student__name', 'date')
    list_filter = ('status', 'is_late', 'student__session')

# Fee Model Admin
@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ('student', 'total_fee', 'due_date', 'paid', 'balance', 'added_month', 'added_year')
    search_fields = ('student__name', 'student__roll_no')
    list_filter = ('paid', 'added_month', 'added_year')

# FeePayment Model Admin
@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('fee', 'amount', 'date')
    search_fields = ('fee__student__name', 'fee__student__roll_no')
    ordering = ('date',)

# CameraConfiguration Model Admin
@admin.register(CameraConfiguration)
class CameraConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'camera_source', 'threshold')
    search_fields = ('name', 'camera_source')



# Email Admin ##############################
class EmailConfigAdmin(admin.ModelAdmin):
    list_display = ('email_host', 'email_port', 'email_use_tls', 'email_host_user')  # Customize which fields to display
    search_fields = ('email_host', 'email_host_user')  # Add search functionality

# Register the model with the custom admin class
admin.site.register(EmailConfig, EmailConfigAdmin)



from django.contrib import admin
from .models import AdvancePayment

@admin.register(AdvancePayment)
class AdvancePaymentAdmin(admin.ModelAdmin):
    list_display = ('fee', 'amount', 'date', 'student_name', 'total_fee', 'current_balance')
    list_filter = ('date',)
    search_fields = ('fee__student__name', 'fee__id')
    date_hierarchy = 'date'

    def student_name(self, obj):
        return obj.fee.student.name
    student_name.short_description = "Student Name"

    def total_fee(self, obj):
        return obj.fee.total_fee
    total_fee.short_description = "Total Fee"

    def current_balance(self, obj):
        return obj.fee.balance
    current_balance.short_description = "Current Balance"

####################################################
from django.contrib import admin
from .models import Settings, Student

@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'student_name', 'check_out_time_threshold', 'is_global_setting')
    list_filter = ('student',)
    search_fields = ('student__name',)
    ordering = ('-id',)

    def student_name(self, obj):
        return obj.student.name if obj.student else 'Global'
    student_name.short_description = 'Student Name'

    def is_global_setting(self, obj):
        return obj.student is None
    is_global_setting.short_description = 'Global Setting'
    is_global_setting.boolean = True



from django.contrib import admin

@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('student', 'start_date', 'end_date', 'approved')
    list_filter = ('approved',)
    search_fields = ('student__name', 'reason')

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number', 'department')
    search_fields = ('name', 'email')

@admin.register(AssignedClass)
class AssignedClassAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'course', 'department', 'semester', 'get_cameras')
    search_fields = ('teacher__name', 'course__name')

    def get_cameras(self, obj):
        return ", ".join([c.name for c in obj.cameras.all()])
    get_cameras.short_description = 'Cameras'

