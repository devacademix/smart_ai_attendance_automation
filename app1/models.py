from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import time
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver





# Semester Model
class Semester(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Semester name (e.g., Fall 2024)")
    start_date = models.DateField(help_text="Start date of the semester")
    end_date = models.DateField(help_text="End date of the semester")
    description = models.TextField(help_text="Brief description of the semester", blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"
    
# Department Model
class Department(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.name

# Session Model
class Session(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"

# Course Model for Learning Materials
class Course(models.Model):
    name = models.CharField(max_length=255, unique=True, help_text="Course name")
    description = models.TextField(help_text="Course description")
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="courses")  # Linking to Session
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# Lesson Model for Learning Materials
class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=255, help_text="Title of the lesson")
    description = models.TextField(help_text="Brief description of the lesson", blank=True, null=True)
    youtube_embed_link = models.URLField(help_text="Embed link for YouTube video", blank=True, null=True)
    youtube_video_url = models.URLField(help_text="Direct YouTube video URL", blank=True, null=True)
    video_file = models.FileField(upload_to="lessons/videos/", blank=True, null=True, help_text="Upload video file for the lesson")
    lesson_notes = models.TextField(blank=True, null=True, help_text="Additional notes or materials for the lesson")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.course.name} - {self.title}"

# Updated Student Model with Courses, Lessons, and Session
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    phone_number = models.CharField(max_length=15)
    face_embedding = models.JSONField(blank=True, null=True)
    authorized = models.BooleanField(default=False)
    roll_no = models.CharField(max_length=20,unique=True)
    address = models.TextField()
    date_of_birth = models.DateField()
    joining_date = models.DateField()
    mother_name = models.CharField(max_length=255)
    father_name = models.CharField(max_length=255)

    # Linking the student with a session (1-to-many relationship)
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="students")

    # Linking the student with courses and lessons and semester
    courses = models.ManyToManyField(Course, related_name="students")
    department = models.ManyToManyField(Department, related_name="students")
    semester= models.ManyToManyField(Semester, related_name="students")

    def __str__(self):
        return self.name



# Late Check-In Policy Model
class LateCheckInPolicy(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name="late_checkin_policy")

    def get_default_start_time():
        return time(8, 0)  # Default time as 8:00 AM

    start_time = models.TimeField(default=get_default_start_time)
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.student.name} - Late Check-In After {self.start_time}"

# Signal to create default LateCheckInPolicy for each student
@receiver(post_save, sender=Student)
def create_late_checkin_policy(sender, instance, created, **kwargs):
    if created:
        LateCheckInPolicy.objects.create(student=instance)


# Attendance Model
class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('Present', 'Present'), ('Absent', 'Absent'), ('Leave', 'Leave')], default='Absent')
    is_late = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.student.name} - {self.date}"

    def mark_checked_in(self):
        self.check_in_time = timezone.now()
        self.status = 'Present'

        # Fetch the student's late check-in policy
        policy = self.student.late_checkin_policy
        if policy:
            # Convert the late check-in time to the local timezone
            current_local_time = timezone.localtime()
            late_check_in_threshold = current_local_time.replace(
                hour=policy.start_time.hour,
                minute=policy.start_time.minute,
                second=0,
                microsecond=0
            )

            # Check if the check-in time is late
            if self.check_in_time > late_check_in_threshold:
                self.is_late = True

        self.save()

    def mark_checked_out(self):
        if self.check_in_time:
            self.check_out_time = timezone.now()
            self.save()
        else:
            raise ValueError("Cannot mark check-out without check-in.")

    def calculate_duration(self):
        if self.check_in_time and self.check_out_time:
            duration = self.check_out_time - self.check_in_time
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        return None

    def save(self, *args, **kwargs):
        if not self.pk:  # Only on creation
            self.date = timezone.now().date()
        super().save(*args, **kwargs)

 #######################################################
# Fee Model
class Fee(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="fees")
    total_fee = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    paid = models.BooleanField(default=False)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    added_month = models.PositiveIntegerField()
    added_year = models.PositiveIntegerField()

    # New field for advance payment
    advance_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # New field for fee status (Paid, Pending, Partial)
    STATUS_CHOICES = [
        ('Paid', 'Paid'),
        ('Pending', 'Pending'),
        ('Partial', 'Partial'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"{self.student.name} - Total Fee: {self.total_fee}, Balance: {self.balance}, Status: {self.status}, Advance: {self.advance_payment}"

    def calculate_balance(self):
        # Calculate the total payment made for this fee
        payments = self.payments.aggregate(total=Sum('amount'))['total'] or 0
        total_paid = payments + self.advance_payment
        self.balance = self.total_fee - total_paid

        # Update the status based on the balance
        if self.balance == 0:
            self.paid = True
            self.status = 'Paid'
        elif self.balance < self.total_fee:
            self.paid = False
            self.status = 'Partial'
        else:
            self.paid = False
            self.status = 'Pending'

        self.save()

    # Method to mark fee as paid manually from the admin interface
    def mark_as_paid(self):
        self.paid = True
        self.balance = 0
        self.status = 'Paid'
        self.save()

    @classmethod
    def get_total_pending_fees(cls):
        # Calculate the total amount of unpaid fees (where paid is False)
        return cls.objects.filter(paid=False).aggregate(total_pending_fees=Sum('balance'))['total_pending_fees'] or 0.00


# FeePayment Model
class FeePayment(models.Model):
    fee = models.ForeignKey(Fee, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    
    # New field for payment method (Cash, UPI, Bank Transfer)
    PAYMENT_METHOD_CHOICES = [
        ('Cash', 'Cash'),
        ('UPI', 'UPI'),
        ('Bank Transfer', 'Bank Transfer'),
    ]
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHOD_CHOICES, default='Cash')

    def __str__(self):
        return f"Payment of {self.amount} for {self.fee.student.name} on {self.date} via {self.payment_method}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Recalculate the balance for the fee when a payment is made
        self.fee.calculate_balance()


# Advanced FeePayment Model (for manual advance payments)
class AdvancePayment(models.Model):
    fee = models.ForeignKey(Fee, on_delete=models.CASCADE, related_name="advance_payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Advance Payment of {self.amount} for {self.fee.student.name} on {self.date}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Add the advance payment to the fee and recalculate the balance
        self.fee.advance_payment += self.amount
        self.fee.calculate_balance()




######################################################################
class CameraConfiguration(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Give a name to this camera configuration")
    camera_source = models.CharField(max_length=255, help_text="Camera index (0 for default webcam or RTSP/HTTP URL for IP camera)")
    threshold = models.FloatField(default=0.6, help_text="Face recognition confidence threshold")
    location = models.CharField(max_length=255, null=True, default='Gate 1', help_text="Location of the camera (optional)")

    def __str__(self):
        return self.name



# Email Settings
class EmailConfig(models.Model):
    email_host = models.CharField(max_length=255)
    email_port = models.IntegerField()
    email_use_tls = models.BooleanField(default=True)
    email_host_user = models.CharField(max_length=255)
    email_host_password = models.CharField(max_length=255)

    def __str__(self):
        return f"Email Configuration for {self.email_host_user}"
    
###########################################################
from django.db import models

class Settings(models.Model):
    student = models.OneToOneField('Student', on_delete=models.CASCADE, related_name='settings', null=True, blank=True)  # Link to student
    check_out_time_threshold = models.IntegerField(default=60)  # Default 8 hours in seconds

    def __str__(self):
        return f"Settings (Student: {self.student.name if self.student else 'Global'}, Check-out Time Threshold: {self.check_out_time_threshold} seconds)"

# Signal to create default Settings for each student
@receiver(post_save, sender=Student)
def create_default_settings(sender, instance, created, **kwargs):
    if created:
        Settings.objects.create(student=instance)  # Automatically create the Settings object for the new student




class Leave(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="leaves")
    start_date = models.DateField(help_text="Leave start date")
    end_date = models.DateField(help_text="Leave end date")
    reason = models.TextField(help_text="Reason for the leave", blank=True, null=True)
    approved = models.BooleanField(default=False, help_text="Whether the leave has been approved")

    def __str__(self):
        return f"{self.student.name} - {self.start_date} to {self.end_date} ({'Approved' if self.approved else 'Pending'})"

# Teacher Model
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="teacher_profile")
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="teachers")

    def __str__(self):
        return self.name

# Teacher Assigned Class Mapping
class AssignedClass(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="assigned_classes")
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    camera = models.ForeignKey(CameraConfiguration, on_delete=models.SET_NULL, null=True, blank=True, help_text="Camera attached to this class")

    def __str__(self):
        return f"{self.teacher.name} - {self.course.name} ({self.department.name} - {self.semester.name})"
