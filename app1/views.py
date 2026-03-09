import os
import cv2
import numpy as np
import torch
from facenet_pytorch import InceptionResnetV1, MTCNN
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from .models import Student, Attendance, Teacher, AssignedClass
from django.core.files.base import ContentFile
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
import time
from django.utils.timezone import now
import base64
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Student, Attendance,CameraConfiguration,EmailConfig,Settings
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now as timezone_now
from datetime import datetime, timedelta
from django.utils.timezone import localtime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Student, Attendance
from django.db.models import Count
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.core.files.base import ContentFile
from django.contrib.auth.models import Group
import pygame  # Import pygame for playing sounds
import threading
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse
from django.contrib import messages
from .models import LateCheckInPolicy
from .forms import LateCheckInPolicyForm
from django.shortcuts import render, get_object_or_404
from .models import Student, Fee, FeePayment
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db.models import Sum
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.shortcuts import render
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .forms import StudentEditForm
from django.core.mail import send_mail
from django.shortcuts import render
from django.contrib import messages
from django.template.loader import render_to_string
from .models import Attendance, EmailConfig,Leave  # Import models
from django.shortcuts import render, get_object_or_404, redirect
from .models import Semester, Department, Session
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import EmailConfig
from .forms import CourseForm, LessonForm
from django.shortcuts import render, get_object_or_404
from .models import Course, Lesson
###############################################################


####################################################################
# Home page view
def home(request):
    # Check if the user is authenticated
    if not request.user.is_authenticated:
        return render(request, 'home.html')  # Display the home page for unauthenticated users
    
    # If the user is authenticated, check if they are admin or student
    if request.user.is_staff:
        return redirect('admin_dashboard')
    
    try:
        # Attempt to fetch the student's profile
        student_profile = Student.objects.get(user=request.user)
        # If the student profile exists, redirect to the student dashboard
        return redirect('student_dashboard')
    except Student.DoesNotExist:
        # If no student profile exists, redirect to an error page or home page
        return render(request, 'home.html')  # You can customize this if needed

##############################################################
def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    
    # Count total students
    total_students = Student.objects.count()

    # Total attendance records for today
    total_attendance = Attendance.objects.count()

    # Total present students for today
    total_present = Attendance.objects.filter(status='Present').count()

    # Total absent students for today
    total_absent = Attendance.objects.filter(status='Absent').count()

    # Total late check-ins for today
    total_late_checkins = Attendance.objects.filter(is_late=True).count()

    # Total check-ins for today
    total_checkins = Attendance.objects.filter(check_in_time__isnull=False).count()

    # Total check-outs for today
    total_checkouts = Attendance.objects.filter(check_out_time__isnull=False).count()

    # Total number of cameras
    total_cameras = CameraConfiguration.objects.count()
    # Total number of cameras
    total_course = Course.objects.count()

    # Total pending fees
    total_pending_fees = Fee.get_total_pending_fees()

    # Passing the data to the template
    context = {
        'total_students': total_students,
        'total_attendance': total_attendance,
        'total_present': total_present,
        'total_absent': total_absent,
        'total_late_checkins': total_late_checkins,
        'total_checkins': total_checkins,
        'total_checkouts': total_checkouts,
        'total_cameras': total_cameras,
        'total_course': total_course,
        'total_pending_fees': total_pending_fees,  # Added total pending fees to context
    }

    return render(request, 'admin/admin-dashboard.html', context)

##############################################################

def mark_attendance(request):
    return render(request, 'Mark_attendance.html')

#############################################################
# Initialize MTCNN and InceptionResnetV1
mtcnn = MTCNN(keep_all=True)
resnet = InceptionResnetV1(pretrained='vggface2').eval()

# Function to detect and encode faces
def detect_and_encode(image):
    with torch.no_grad():
        boxes, _ = mtcnn.detect(image)
        if boxes is not None:
            faces = []
            for box in boxes:
                face = image[int(box[1]):int(box[3]), int(box[0]):int(box[2])]
                if face.size == 0:
                    continue
                face = cv2.resize(face, (160, 160))
                face = np.transpose(face, (2, 0, 1)).astype(np.float32) / 255.0
                face_tensor = torch.tensor(face).unsqueeze(0)
                encoding = resnet(face_tensor).detach().numpy().flatten()
                faces.append(encoding)
            return faces
    return []

# Function to encode uploaded images
def encode_uploaded_images():
    known_face_encodings = []
    known_face_names = []

    # Fetch only authorized students
    uploaded_images = Student.objects.filter(authorized=True)

    for student in uploaded_images:
        # Use the face_embedding stored in the model directly
        if student.face_embedding:
            known_face_encodings.append(np.array(student.face_embedding))
            known_face_names.append(student.name)

    return known_face_encodings, known_face_names

# Function to recognize faces
def recognize_faces(known_encodings, known_names, test_encodings, threshold=0.6):
    recognized_names = []
    for test_encoding in test_encodings:
        distances = np.linalg.norm(known_encodings - test_encoding, axis=1)
        min_distance_idx = np.argmin(distances)
        if distances[min_distance_idx] < threshold:
            recognized_names.append(known_names[min_distance_idx])
        else:
            recognized_names.append('Not Recognized')
    return recognized_names

#####################################################################

############################################################################
@csrf_exempt
def capture_and_recognize(request):
    if request.method != 'POST':
        return JsonResponse({'message': 'Invalid request method.'}, status=405)

    try:
        current_time = timezone.now()
        today = current_time.date()

        # Fetch global settings
        settings = Settings.objects.first()
        if not settings:
            return JsonResponse({'message': 'Settings not configured.'}, status=500)

        global_check_out_threshold_seconds = settings.check_out_time_threshold

        # Mark absent students and update leave attendance
        update_leave_attendance(today)

        # Parse image data from request
        data = json.loads(request.body)
        student_name = data.get('student_name')
        image_data = data.get('image')
        if not image_data:
            return JsonResponse({'message': 'No image data received.'}, status=400)

        # Decode the Base64 image
        image_data = image_data.split(',')[1]  # Remove Base64 prefix
        image_bytes = base64.b64decode(image_data)
        np_img = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

        # Convert BGR to RGB for face recognition
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect and encode faces
        test_face_encodings = detect_and_encode(frame_rgb)
        if not test_face_encodings:
            return JsonResponse({'message': 'No face detected.'}, status=200)

        # Retrieve known face encodings and recognize faces
        known_face_encodings, known_face_names = encode_uploaded_images()
        if not known_face_encodings:
            return JsonResponse({'message': 'No known faces available.'}, status=200)

        recognized_names = recognize_faces(
            np.array(known_face_encodings),
            known_face_names,
            test_face_encodings,
            threshold=0.6
        )

        # Prepare and update attendance records
        attendance_response = []
        for name in recognized_names:
            if name == 'Not Recognized':
                attendance_response.append({
                    'name': 'Unknown',
                    'status': 'Face not recognized',
                    'check_in_time': None,
                    'check_out_time': None,
                    'image_url': '/static/notrecognize.png',
                    'play_sound': False
                })
                continue

            student = Student.objects.filter(name=name).first()
            if not student:
                continue

            # Use student-specific setting if available, otherwise use global setting
            student_threshold_seconds = (
                student.settings.check_out_time_threshold
                if student.settings and student.settings.check_out_time_threshold is not None
                else global_check_out_threshold_seconds
            )

            # Check if the student already has an attendance record for today
            attendance = Attendance.objects.filter(student=student, date=today).first()

            if not attendance:
                # If no attendance record exists for the student, create one
                attendance = Attendance.objects.create(student=student, date=today, status='Absent')

            # Handle attendance update for students
            if attendance.status == 'Leave':
                attendance_response.append({
                    'name': name,
                    'status': 'Leave',
                    'check_in_time': None,
                    'check_out_time': None,
                    'image_url': '/static/enjoye.jpg',
                    'play_sound': False
                })
            elif attendance.check_in_time is None:
                # Mark checked-in if not already checked-in
                attendance.mark_checked_in()
                attendance.save()

                attendance_response.append({
                    'name': name,
                    'status': 'Checked-in',
                    'check_in_time': attendance.check_in_time.isoformat() if attendance.check_in_time else None,
                    'check_out_time': None,
                    'image_url': '/static/success.png',
                    'play_sound': True
                })
            elif attendance.check_out_time is None and current_time >= attendance.check_in_time + timedelta(seconds=student_threshold_seconds):
                # Mark checked-out if applicable
                attendance.mark_checked_out()
                attendance.save()

                attendance_response.append({
                    'name': name,
                    'status': 'Checked-out',
                    'check_in_time': attendance.check_in_time.isoformat(),
                    'check_out_time': attendance.check_out_time.isoformat(),
                    'image_url': '/static/success.png',
                    'play_sound': True
                })
            else:
                attendance_response.append({
                    'name': name,
                    'status': 'Already checked-in' if not attendance.check_out_time else 'Already checked-out',
                    'check_in_time': attendance.check_in_time.isoformat(),
                    'check_out_time': attendance.check_out_time.isoformat() if attendance.check_out_time else None,
                    'image_url': '/static/success.png',
                    'play_sound': False
                })

        return JsonResponse({'attendance': attendance_response}, status=200)

    except Exception as e:
        return JsonResponse({'message': f"Error: {str(e)}"}, status=500)


def update_leave_attendance(today):
    """
    Function to update attendance for students on leave and those without leave approval (Absent).
    """
    # Fetch the leaves approved for today
    approved_leaves = Leave.objects.filter(
        start_date__lte=today,
        end_date__gte=today,
        approved=True
    )

    # Create a set of students with approved leave for today
    approved_leave_students = {leave.student.id for leave in approved_leaves}

    # Debugging log to check approved leaves and student ids
    # print(f"Approved Leave Students IDs: {approved_leave_students}")

    # Mark attendance for leave students
    students = Student.objects.all()
    for student in students:
        # Check if the student has an attendance record for today
        existing_attendance = Attendance.objects.filter(student=student, date=today).first()

        # If the student has approved leave and no attendance record, mark as "Leave"
        if student.id in approved_leave_students:
            if not existing_attendance:
                # print(f"Marking {student.name} as Leave")  # Debug log
                Attendance.objects.create(student=student, date=today, status='Leave')
        else:
            # If no approved leave and no attendance record, mark as "Absent"
            if not existing_attendance:
                # print(f"Marking {student.name} as Absent")  # Debug log
                Attendance.objects.create(student=student, date=today, status='Absent')


#######################################################################

# Function to detect and encode faces
def detect_and_encode_uploaded_image_for_register(image):
    with torch.no_grad():
        boxes, _ = mtcnn.detect(image)
        if boxes is not None:
            for box in boxes:
                face = image[int(box[1]):int(box[3]), int(box[0]):int(box[2])]
                if face.size == 0:
                    continue
                face = cv2.resize(face, (160, 160))
                face = np.transpose(face, (2, 0, 1)).astype(np.float32) / 255.0
                face_tensor = torch.tensor(face).unsqueeze(0)
                encoding = resnet(face_tensor).detach().numpy().flatten()
                return encoding
    return None
############################################################################################
# View to register a student
def register_student(request):
    if request.method == 'POST':
        try:
            # Get student information from the form
            name = request.POST.get('name')
            email = request.POST.get('email')
            phone_number = request.POST.get('phone_number')
            image_file = request.FILES.get('image')  # Uploaded image
            roll_no = request.POST.get('roll_no')
            address = request.POST.get('address')
            date_of_birth = request.POST.get('date_of_birth')
            joining_date = request.POST.get('joining_date')
            mother_name = request.POST.get('mother_name')
            father_name = request.POST.get('father_name')
            semester_ids = request.POST.getlist('semester')
            department_ids = request.POST.getlist('department')
            course_ids = request.POST.getlist('courses')
            session_id = request.POST.get('session')

            username = request.POST.get('username')
            password = request.POST.get('password')

            # Check for existing username
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists. Please choose another one.')
                return render(request, 'register_student.html')

            # Check for existing roll number
            if Student.objects.filter(roll_no=roll_no).exists():
                messages.error(request, 'Roll number already exists. Please use a different roll number.')
                return render(request, 'register_student.html')

            # Process the uploaded image to extract face embedding
            image_array = np.frombuffer(image_file.read(), np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            face_embedding = detect_and_encode_uploaded_image_for_register(image_rgb)

            if face_embedding is None:
                messages.error(request, 'No face detected in the uploaded image. Please upload a clear face image.')
                return render(request, 'register_student.html')

            # Create the user
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()

            # Get the session object
            session = Session.objects.get(id=session_id)

            # Create the student record
            student = Student(
                user=user,
                name=name,
                email=email,
                phone_number=phone_number,
                face_embedding=face_embedding.tolist(),  # Save the face embedding
                authorized=False,
                roll_no=roll_no,
                address=address,
                date_of_birth=date_of_birth,
                joining_date=joining_date,
                mother_name=mother_name,
                father_name=father_name,
                session=session,
            )
            student.save()

            # Associate courses, departments, and semesters
            student.courses.set(Course.objects.filter(id__in=course_ids))
            student.department.set(Department.objects.filter(id__in=department_ids))
            student.semester.set(Semester.objects.filter(id__in=semester_ids))

            messages.success(request, 'Registration successful! Welcome.')
            return redirect('register_success')

        except Exception as e:
            print(f"Error during registration: {e}")
            messages.error(request, 'An error occurred during registration. Please try again.')
            return render(request, 'register_student.html')

    # Query all necessary data to pass to the template
    semesters = Semester.objects.all()
    sessions = Session.objects.all()
    departments = Department.objects.all()
    courses = Course.objects.all()

    return render(request, 'register_student.html', {
        'semesters': semesters,
        'sessions': sessions,
        'departments': departments,
        'courses': courses,
    })


########################################################################

# Success view after capturing student information and image
def register_success(request):
    return render(request, 'register_success.html')

#########################################################################

#this is for showing Attendance list
def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def student_attendance_list(request):
    # Get the search query, date filter, roll number filter, and attendance status filter from the request
    search_query = request.GET.get('search', '')
    date_filter = request.GET.get('attendance_date', '')
    roll_no_filter = request.GET.get('roll_no', '')  # Filter by roll number
    status_filter = request.GET.get('status', '')  # Filter by status (Present/Absent)

    # Get all students
    students = Student.objects.all()

    # Filter students based on the search query (name)
    if search_query:
        students = students.filter(name__icontains=search_query)

    # Filter students based on roll number if provided
    if roll_no_filter:
        students = students.filter(roll_no__icontains=roll_no_filter)

    # Prepare the attendance data
    student_attendance_data = []
    total_attendance_count = 0  # Initialize the total attendance count

    for student in students:
        # Get the attendance records for each student
        attendance_records = Attendance.objects.filter(student=student)

        # Filter by date if provided
        if date_filter:
            # Assuming date_filter is in the format YYYY-MM-DD
            attendance_records = attendance_records.filter(date=date_filter)

        # Filter by status if provided
        if status_filter:
            attendance_records = attendance_records.filter(status=status_filter)

        # Order attendance records by date
        attendance_records = attendance_records.order_by('date')

        # Count the attendance records for this student
        student_attendance_count = attendance_records.count()
        total_attendance_count += student_attendance_count  # Add to the total count

        student_attendance_data.append({
            'student': student,
            'attendance_records': attendance_records,
            'attendance_count': student_attendance_count  # Add count per student
        })

    context = {
        'student_attendance_data': student_attendance_data,
        'search_query': search_query,  # Pass the search query to the template
        'date_filter': date_filter,    # Pass the date filter to the template
        'roll_no_filter': roll_no_filter,  # Pass the roll number filter to the template
        'status_filter': status_filter,  # Pass the status filter to the template
        'total_attendance_count': total_attendance_count  # Pass the total attendance count to the template
    }

    return render(request, 'student_attendance_list.html', context)



######################################################################

@staff_member_required
def student_list(request):
    students = Student.objects.all()
    return render(request, 'student_list.html', {'students': students})

@staff_member_required
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    return render(request, 'student_detail.html', {'student': student})

@staff_member_required
def student_authorize(request, pk):
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        authorized = request.POST.get('authorized', False)
        student.authorized = bool(authorized)
        student.save()
        return redirect('student-list')
    
    return render(request, 'student_authorize.html', {'student': student})

###############################################################################

def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        form = StudentEditForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student details updated successfully.')
            return redirect('student-detail', pk=student.pk)  # Redirect to the student detail page
    else:
        form = StudentEditForm(instance=student)

    return render(request, 'student_edit.html', {'form': form, 'student': student})
###########################################################
# This views is for Deleting student
@staff_member_required
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        student.delete()
        messages.success(request, 'Student deleted successfully.')
        return redirect('student-list')  # Redirect to the student list after deletion
    
    return render(request, 'student_delete_confirm.html', {'student': student})

########################################################################

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Check if the user is a staff or student by checking if they have a linked Student profile
            try:
                # Attempt to fetch the student's profile
                student_profile = Student.objects.get(user=user)
                # If the student profile exists, redirect to the student dashboard
                return redirect('student_dashboard')
            except Student.DoesNotExist:
                pass
            
            # Check if the user has a linked Teacher profile
            try:
                teacher_profile = Teacher.objects.get(user=user)
                return redirect('teacher_dashboard')
            except Teacher.DoesNotExist:
                pass
                
            # If no student or teacher profile exists, assume the user is a staff/admin member
            return redirect('admin_dashboard')

        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')

#########################################################################

# This is for user logout
def user_logout(request):
    logout(request)
    return redirect('login')  # Replace 'login' with your desired redirect URL after logout
##############################################################################

#######################################################################################    

@staff_member_required
def send_attendance_notifications(request):
    from django.core.mail import get_connection, send_mail
    from smtplib import SMTPException
    
    # Fetch email configuration from the database
    email_config = EmailConfig.objects.first()

    if email_config is None:
        messages.error(request, "No email configuration found!")
        return render(request, 'notification_sent.html')

    # Create a dynamic connection backend to avoid global settings mutation issues
    try:
        connection = get_connection(
            host=email_config.email_host,
            port=email_config.email_port,
            username=email_config.email_host_user,
            password=email_config.email_host_password,
            use_tls=email_config.email_use_tls
        )
    except Exception as e:
        messages.error(request, f"Failed to initialize email connection: {e}")
        return render(request, 'notification_sent.html')

    # Filter late students who haven't been notified
    late_attendance_records = Attendance.objects.filter(is_late=True, email_sent=False)
    # Filter absent students who haven't been notified
    absent_students = Attendance.objects.filter(status='Absent', email_sent=False)

    success_count = 0
    error_count = 0

    # Process late students
    for record in late_attendance_records:
        student = record.student
        subject = f"Late Check-in Notification for {student.name}"

        # Render the email content from the HTML template for late students
        html_message = render_to_string(
            'email_templates/late_attendance_email.html',
            {'student': student, 'record': record}
        )

        try:
            send_mail(
                subject,
                "This is an HTML email. Please enable HTML content to view it.",
                email_config.email_host_user,
                [student.email],
                fail_silently=False,
                html_message=html_message,
                connection=connection
            )
            # Mark email as sent to avoid resending
            record.email_sent = True
            record.save()
            success_count += 1
        except Exception as e:
            error_count += 1
            messages.error(request, f"Failed to send email to {student.email}: {e}")

    # Process absent students
    for record in absent_students:
        student = record.student
        subject = "Absent Attendance Notification"

        # Render the email content from the HTML template for absent students
        html_message = render_to_string(
            'email_templates/absent_attendance_email.html',
            {'student': student, 'record': record}
        )

        try:
            send_mail(
                subject,
                "This is an HTML email. Please enable HTML content to view it.",
                email_config.email_host_user,
                [student.email],
                fail_silently=False,
                html_message=html_message,
                connection=connection
            )
            record.email_sent = True
            record.save()
            success_count += 1
        except Exception as e:
            error_count += 1
            messages.error(request, f"Failed to send email to {student.email}: {e}")

    # Fetch students who already received the email (email_sent=True)
    already_notified_students = Attendance.objects.filter(email_sent=True).order_by('-date')

    if success_count > 0:
        messages.success(request, f"Successfully sent {success_count} attendance notifications!")
    if success_count == 0 and error_count == 0:
        messages.info(request, "No new unsent notifications pending.")

    return render(request, 'notification_sent.html', {
        'notified_students': already_notified_students
    })


############################################################################################

@staff_member_required
def student_list_with_fees(request):
    search_query = request.GET.get('search', '')  # Get the search query from the URL

    # Filter students based on the search query in the name or semester field.
    # If 'semester' is a ForeignKey, use 'semester__name' or the actual field you want to search on.
    students = Student.objects.filter(
        name__icontains=search_query
    ) | Student.objects.filter(
        semester__name__icontains=search_query  # Adjust this field if 'semester' is a ForeignKey
    )

    student_data = []
    for student in students:
        total_fee = student.fees.aggregate(total_fee=Sum('total_fee'))['total_fee'] or 0
        total_payment = student.fees.aggregate(total_payment=Sum('payments__amount'))['total_payment'] or 0
        balance = total_fee - total_payment
        fee_status = 'Paid' if balance <= 0 else 'Pending'
        student_data.append({
            'student': student,
            'total_fee': total_fee,
            'total_payment': total_payment,
            'balance': balance,
            'fee_status': fee_status,
        })

    return render(request, 'student_list_with_fees.html', {'student_data': student_data, 'search_query': search_query})

##############################################################################


@staff_member_required
def add_fee_for_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        try:
            total_fee = float(request.POST['total_fee'])
            due_date = request.POST['due_date']
            advance_payment = float(request.POST.get('advance_payment', '0') or '0')
            added_month = int(request.POST['added_month'].split('-')[1])
            added_year = int(request.POST['added_year'])
            
            # Automatically calculate initial balance and status
            balance = total_fee - advance_payment
            status = 'Paid' if balance <= 0 else 'Partial' if balance < total_fee else 'Pending'
            
            # Create the Fee record
            Fee.objects.create(
                student=student,
                total_fee=total_fee,
                due_date=due_date,
                balance=balance,
                added_month=added_month,
                added_year=added_year,
                advance_payment=advance_payment,
                status=status,
            )
            
            # Add a success message
            messages.success(request, f"Fee of ₹{total_fee} has been successfully added for {student.name}.")
            
            # Redirect to the student's fee details page after adding the fee
            return HttpResponseRedirect(reverse('student_fee_details', args=[student.id]))
        
        except ValueError as e:
            # Handle ValueError (e.g., invalid number format)
            messages.error(request, "Invalid data entered. Please check the fee details.")
        except Exception as e:
            # Catch other errors
            messages.error(request, f"An error occurred: {str(e)}")
    
    return render(request, 'fee/add_fee_for_student.html', {'student': student})


# View to mark fee payment for a student
#########################################################################################
from django.db import models

@staff_member_required
def pay_fee_for_student(request, fee_id):
    fee = get_object_or_404(Fee, id=fee_id)
    
    # Calculate the remaining balance (total fee - paid amount)
    total_paid = fee.payments.aggregate(total_paid=models.Sum('amount'))['total_paid'] or 0
    remaining_balance = fee.total_fee - total_paid

    if request.method == 'POST':
        try:
            payment_amount = float(request.POST['payment_amount'])
            payment_method = request.POST['payment_method']

            if payment_amount <= 0:
                messages.error(request, "Payment amount must be greater than zero.")
                return render(request, 'fee/pay_fee_for_student.html', {'fee': fee})

            if payment_amount > remaining_balance:
                messages.error(request, f"Payment amount cannot exceed the remaining balance of ₹{remaining_balance}.")
                return render(request, 'fee/pay_fee_for_student.html', {'fee': fee})

            # Create the payment record
            FeePayment.objects.create(fee=fee, amount=payment_amount, payment_method=payment_method)

            # Recalculate balance after payment
            fee.calculate_balance()

            messages.success(request, f"Payment of ₹{payment_amount} successfully processed.")
            return HttpResponseRedirect(reverse('student_fee_details', args=[fee.student.id]))

        except ValueError:
            messages.error(request, "Invalid payment amount. Please enter a valid number.")
            return render(request, 'fee/pay_fee_for_student.html', {'fee': fee})

    return render(request, 'fee/pay_fee_for_student.html', {'fee': fee})
############################################################################
# View to view detailed fees and payments for a student
@staff_member_required
def student_fee_details(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    fees = student.fees.all()
    total_paid = sum(fee.payments.aggregate(total=Sum('amount'))['total'] or 0 for fee in fees)
    total_balance = sum(fee.balance for fee in fees)
    return render(request, 'fee/student_fee_details.html', {
        'student': student,
        'fees': fees,
        'total_paid': total_paid,
        'total_balance': total_balance,
    })

# View to delete a fee payment (optional feature for management)
@staff_member_required
def delete_fee_payment(request, payment_id):
    payment = get_object_or_404(FeePayment, id=payment_id)
    fee = payment.fee
    payment.delete()
    fee.calculate_balance()  # Recalculate balance after deletion
    return HttpResponseRedirect(reverse('student_fee_details', args=[fee.student.id]))

# View to mark fee as paid manually (useful for admins)
@staff_member_required
def mark_fee_as_paid(request, fee_id):
    fee = get_object_or_404(Fee, id=fee_id)
    fee.mark_as_paid()  # Mark the fee as paid
    return HttpResponseRedirect(reverse('student_list_with_fees'))

##################################################################################
# views.py

@staff_member_required
def late_checkin_policy_list(request):
    policies = LateCheckInPolicy.objects.select_related('student').all()
    return render(request, 'latecheckinpolicy_list.html', {'policies': policies})

def create_late_checkin_policy(request):
    if request.method == 'POST':
        form = LateCheckInPolicyForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data['student']
            if LateCheckInPolicy.objects.filter(student=student).exists():
                messages.error(request, f"A late check-in policy for {student} already exists.")
            else:
                form.save()
                messages.success(request, "Late check-in policy created successfully!")
                return redirect('late_checkin_policy_list')
    else:
        form = LateCheckInPolicyForm()

    return render(request, 'latecheckinpolicy_form.html', {'form': form})

@staff_member_required
def update_late_checkin_policy(request, policy_id):
    policy = get_object_or_404(LateCheckInPolicy, id=policy_id)
    if request.method == 'POST':
        form = LateCheckInPolicyForm(request.POST, instance=policy)
        if form.is_valid():
            form.save()
            messages.success(request, "Late check-in policy updated successfully!")
            return redirect('late_checkin_policy_list')
    else:
        form = LateCheckInPolicyForm(instance=policy)

    return render(request, 'latecheckinpolicy_form.html', {'form': form, 'policy': policy})

@staff_member_required
def delete_late_checkin_policy(request, policy_id):
    policy = get_object_or_404(LateCheckInPolicy, id=policy_id)
    if request.method == 'POST':
        policy.delete()
        messages.success(request, "Late check-in policy deleted successfully!")
        return redirect('late_checkin_policy_list')
    return render(request, 'latecheckinpolicy_confirm_delete.html', {'policy': policy})

#######################################################################################


#########################################################################################
def capture_and_recognize_with_cam(request):
    stop_events = []  # List to store stop events for each thread
    camera_threads = []  # List to store threads for each camera
    camera_windows = []  # List to store window names
    error_messages = []  # List to capture errors from threads

    def process_frame(cam_config, stop_event):
        """Thread function to capture and process frames for each camera."""
        cap = None
        window_created = False  # Flag to track if the window was created
        try:
            # Check if the camera source is a number (local webcam) or a string (IP camera URL)
            if cam_config.camera_source.isdigit():
                cap = cv2.VideoCapture(int(cam_config.camera_source))  # Use integer index for webcam
            else:
                cap = cv2.VideoCapture(cam_config.camera_source)  # Use string for IP camera URL

            if not cap.isOpened():
                raise Exception(f"Unable to access camera {cam_config.name}.")

            threshold = cam_config.threshold

            # Initialize pygame mixer for sound playback
            pygame.mixer.init()
            success_sound = pygame.mixer.Sound('static/success.wav')  # Load sound path

            window_name = f'Camera Location - {cam_config.location}'
            camera_windows.append(window_name)  # Track the window name

            while not stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    print(f"Failed to capture frame for camera: {cam_config.name}")
                    break  # If frame capture fails, break from the loop

                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                test_face_encodings = detect_and_encode(frame_rgb)  # Function to detect and encode face in frame

                if test_face_encodings:
                    known_face_encodings, known_face_names = encode_uploaded_images()  # Load known face encodings once
                    if known_face_encodings:
                        names = recognize_faces(
                            np.array(known_face_encodings), known_face_names, test_face_encodings, threshold
                        )

                        for name, box in zip(names, mtcnn.detect(frame_rgb)[0]):
                            if box is not None:
                                (x1, y1, x2, y2) = map(int, box)
                                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                cv2.putText(frame, name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

                                if name != 'Not Recognized':
                                    students = Student.objects.filter(name=name)
                                    if students.exists():
                                        student = students.first()
                                        print(f"Recognized student: {student.name}")  # Debugging log

                                        # Fetch the check-out time threshold
                                        if student.settings:
                                            check_out_threshold_seconds = student.settings.check_out_time_threshold

                                        # Check if attendance exists for today
                                        attendance, created = Attendance.objects.get_or_create(
                                            student=student, date=now().date()
                                        )

                                        if attendance.check_in_time is None:
                                            attendance.mark_checked_in()
                                            success_sound.play()
                                            cv2.putText(
                                                frame, f"{name}, checked in.", (50, 50), 
                                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA
                                            )
                                            print(f"Attendance checked in for {student.name}")
                                        elif attendance.check_out_time is None:
                                            if now() >= attendance.check_in_time + timedelta(seconds=check_out_threshold_seconds):
                                                attendance.mark_checked_out()
                                                success_sound.play()
                                                cv2.putText(
                                                    frame, f"{name}, checked out.", (50, 50), 
                                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA
                                                )
                                                print(f"Attendance checked out for {student.name}")
                                            else:
                                                cv2.putText(
                                                    frame, f"{name}, already checked in.", (50, 50), 
                                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA
                                                )
                                        else:
                                            cv2.putText(
                                                frame, f"{name}, already checked out.", (50, 50), 
                                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA
                                            )
                                            print(f"Attendance already completed for {student.name}")

                # Display frame in a separate window for each camera
                if not window_created:
                    cv2.namedWindow(window_name)  # Only create window once
                    window_created = True  # Mark window as created
                cv2.imshow(window_name, frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    stop_event.set()  # Signal the thread to stop when 'q' is pressed
                    break

        except Exception as e:
            print(f"Error in thread for {cam_config.name}: {e}")
            error_messages.append(str(e))  # Capture error message
        finally:
            if cap is not None:
                cap.release()
            if window_created:
                cv2.destroyWindow(window_name)  # Only destroy if window was created

    try:
        # Get all camera configurations
        cam_configs = CameraConfiguration.objects.all()
        if not cam_configs.exists():
            raise Exception("No camera configurations found. Please configure them in the admin panel.")

        # Create threads for each camera configuration
        for cam_config in cam_configs:
            stop_event = threading.Event()
            stop_events.append(stop_event)

            camera_thread = threading.Thread(target=process_frame, args=(cam_config, stop_event))
            camera_threads.append(camera_thread)
            camera_thread.start()

        # Keep the main thread running while cameras are being processed
        while any(thread.is_alive() for thread in camera_threads):
            time.sleep(1)  # Non-blocking wait, allowing for UI responsiveness

    except Exception as e:
        error_messages.append(str(e))  # Capture the error message
    finally:
        # Ensure all threads are signaled to stop
        for stop_event in stop_events:
            stop_event.set()

        # Ensure all windows are closed in the main thread
        for window in camera_windows:
            if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) >= 1:  # Check if window exists
                cv2.destroyWindow(window)

    # Check if there are any error messages
    if error_messages:
        # Join all error messages into a single string
        full_error_message = "\n".join(error_messages)
        return render(request, 'error.html', {'error_message': full_error_message})  # Render the error page with message

    return redirect('student_attendance_list')

##############################################################################

# Function to handle the creation of a new camera configuration
@login_required
@user_passes_test(is_admin)
def camera_config_create(request):
    # Check if the request method is POST, indicating form submission
    if request.method == "POST":
        # Retrieve form data from the request
        name = request.POST.get('name')
        camera_source = request.POST.get('camera_source')
        threshold = request.POST.get('threshold')

        try:
            # Save the data to the database using the CameraConfiguration model
            CameraConfiguration.objects.create(
                name=name,
                camera_source=camera_source,
                threshold=threshold,
            )
            # Redirect to the list of camera configurations after successful creation
            return redirect('camera_config_list')

        except IntegrityError:
            # Handle the case where a configuration with the same name already exists
            messages.error(request, "A configuration with this name already exists.")
            # Render the form again to allow user to correct the error
            return render(request, 'camera/camera_config_form.html')

    # Render the camera configuration form for GET requests
    return render(request, 'camera/camera_config_form.html')


# READ: Function to list all camera configurations
@login_required
@user_passes_test(is_admin)
def camera_config_list(request):
    # Retrieve all CameraConfiguration objects from the database
    configs = CameraConfiguration.objects.all()
    # Render the list template with the retrieved configurations
    return render(request, 'camera/camera_config_list.html', {'configs': configs})


# UPDATE: Function to edit an existing camera configuration
@login_required
@user_passes_test(is_admin)
def camera_config_update(request, pk):
    # Retrieve the specific configuration by primary key or return a 404 error if not found
    config = get_object_or_404(CameraConfiguration, pk=pk)

    # Check if the request method is POST, indicating form submission
    if request.method == "POST":
        # Update the configuration fields with data from the form
        config.name = request.POST.get('name')
        config.camera_source = request.POST.get('camera_source')
        config.threshold = request.POST.get('threshold')
        config.success_sound_path = request.POST.get('success_sound_path')

        # Save the changes to the database
        config.save()  

        # Redirect to the list page after successful update
        return redirect('camera_config_list')  
    
    # Render the configuration form with the current configuration data for GET requests
    return render(request, 'camera/camera_config_form.html', {'config': config})


# DELETE: Function to delete a camera configuration
@login_required
@user_passes_test(is_admin)
def camera_config_delete(request, pk):
    # Retrieve the specific configuration by primary key or return a 404 error if not found
    config = get_object_or_404(CameraConfiguration, pk=pk)

    # Check if the request method is POST, indicating confirmation of deletion
    if request.method == "POST":
        # Delete the record from the database
        config.delete()  
        # Redirect to the list of camera configurations after deletion
        return redirect('camera_config_list')

    # Render the delete confirmation template with the configuration data
    return render(request, 'camera/camera_config_delete.html', {'config': config})



######################## start Student views  ####################################
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Student, Attendance, Fee, FeePayment, Session, Semester, Course, Department

@login_required
def student_dashboard(request):
    try:
        # Get the student object for the currently logged-in user
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Student record does not exist for this user.")
        return redirect('admin_dashboard')  # Redirect to home or profile creation page if student does not exist

    # Calculate total present, total absent, and total late attendance for the student
    total_late_count = Attendance.objects.filter(student=student, is_late=True).count()
    total_present = Attendance.objects.filter(student=student, status='Present').count()
    total_absent = Attendance.objects.filter(student=student, status='Absent').count()

    # Calculate total attendance count (Present + Absent + Late)
    total_classes = total_present + total_absent + total_late_count

    # Calculate attendance percentage
    if total_classes > 0:
        attendance_percentage = (total_present / total_classes) * 100
    else:
        attendance_percentage = 0  # If there are no attendance records, set percentage to 0

    # Retrieve the most recent attendance record for the student
    attendance_records = student.attendance_set.all().order_by('-date')[:2]

    # Retrieve fee details for the student
    fee = Fee.objects.filter(student=student, paid=False).first()  # Get the unpaid fee record (if any)
    fee_payment_records = FeePayment.objects.filter(fee=fee) if fee else []

    # Retrieve session, semester, courses, and department associated with the student
    session = student.session  # Get the session the student is enrolled in
    semesters = student.semester.all()  # Get the list of semesters the student is associated with
    courses = student.courses.all()  # Get the courses the student is enrolled in
    departments = student.department.all()  # Get the departments the student is part of

    context = {
        'student': student,
        'total_present': total_present,
        'total_absent': total_absent,
        'total_late_count': total_late_count,
        'attendance_percentage': attendance_percentage,  # Pass the attendance percentage
        'attendance_records': attendance_records,
        'fee': fee,
        'fee_payment_records': fee_payment_records,
        'session': session,
        'semesters': semesters,
        'courses': courses,
        'departments': departments,
    }

    return render(request, 'student/student-dashboard.html', context)


##############################################################
from django.db.models import Q
@login_required
def student_attendance(request):
    user = request.user
    student = Student.objects.get(user=user)  # Fetch the logged-in student's profile
    
    # Filters for search and date
    search_query = request.GET.get('search', '')
    date_filter = request.GET.get('attendance_date', '')
    
    # Query attendance records for the student
    attendance_records = Attendance.objects.filter(student=student)
    
    if search_query:
        attendance_records = attendance_records.filter(Q(student__name__icontains=search_query) | 
                                                      Q(student__roll_no__icontains=search_query))
    
    if date_filter:
        attendance_records = attendance_records.filter(date=date_filter)
    
    # Render the attendance records
    return render(request, 'student/student_attendance.html', {
        'student_attendance_data': attendance_records,
        'search_query': search_query,
        'date_filter': date_filter
    })


##############################################################

@login_required
def student_fee_detail(request):
    # Get the currently logged-in user's student profile
    student = get_object_or_404(Student, user=request.user)

    # Retrieve fee details for the student
    fee_details = Fee.objects.filter(student=student).order_by('-due_date')

    # Pass the data to the template
    context = {
        'student': student,
        'fee_details': fee_details,
    }
    return render(request, 'student/student_fee_detail.html', context)



# ###############################################

# View for listing all courses
def course_list(request):
    student = request.user.student_profile  # Access the student's profile (assuming the User model has a one-to-one relationship with Student)
    courses = student.courses.all()  # Fetch courses related to the logged-in student
    return render(request, 'courses/course_list.html', {'courses': courses})


# View for displaying details of a single course and its lessons
# View for displaying details of a single course and its lessons
def course_detail(request, course_id):
    student = request.user.student_profile  # Access the student's profile
    course = get_object_or_404(Course, id=course_id)
    
    # Ensure the student is enrolled in the course before fetching lessons
    if course not in student.courses.all():
        # Optionally, raise a 404 or redirect if the student is not enrolled in this course
        return redirect('courses:course_list')  # Redirecting to course list page if the student is not enrolled
    
    lessons = course.lessons.all()  # Fetch lessons related to the course
    return render(request, 'courses/course_detail.html', {'course': course, 'lessons': lessons})


# View for displaying a single lesson
# View for displaying a single lesson
def lesson_detail(request, lesson_id):
    student = request.user.student_profile  # Access the student's profile
    lesson = get_object_or_404(Lesson, id=lesson_id)

    # Ensure the lesson belongs to a course that the student is enrolled in
    if lesson.course not in student.courses.all():
        # Optionally, raise a 404 or redirect if the student is not enrolled in this course
        return redirect('courses:course_list')  # Redirect to course list if the lesson is not associated with a course the student is enrolled in
    
    return render(request, 'courses/lesson_detail.html', {'lesson': lesson})




########################################################################


# Check if the user is an admin
def is_admin(user):
    return user.is_staff

# Admin view for Course management
@user_passes_test(is_admin)
def manage_courses(request):
    courses = Course.objects.prefetch_related("lessons").all()
    return render(request, "admin/manage_courses.html", {"courses": courses})

@user_passes_test(is_admin)
def add_course(request):
    if request.method == "POST":
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Course created successfully!")
            return redirect("manage_courses")
    else:
        form = CourseForm()
    return render(request, "admin/add_course.html", {"form": form})

@user_passes_test(is_admin)
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == "POST":
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Course updated successfully!")
            return redirect("manage_courses")
    else:
        form = CourseForm(instance=course)
    return render(request, "admin/edit_course.html", {"form": form})

@user_passes_test(is_admin)
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    course.delete()
    messages.success(request, "Course deleted successfully!")
    return redirect("manage_courses")

# Admin view for Lesson management
@user_passes_test(is_admin)
def manage_lessons(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    lessons = course.lessons.all()
    return render(request, "admin/manage_lessons.html", {"course": course, "lessons": lessons})

@user_passes_test(is_admin)
def add_lesson(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == "POST":
        form = LessonForm(request.POST, request.FILES)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            messages.success(request, "Lesson created successfully!")
            return redirect("manage_lessons", course_id=course.id)
    else:
        form = LessonForm()
    return render(request, "admin/add_lesson.html", {"form": form, "course": course})

@user_passes_test(is_admin)
def edit_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if request.method == "POST":
        form = LessonForm(request.POST, request.FILES, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, "Lesson updated successfully!")
            return redirect("manage_lessons", course_id=lesson.course.id)
    else:
        form = LessonForm(instance=lesson)
    return render(request, "admin/edit_lesson.html", {"form": form, "course": lesson.course})

@user_passes_test(is_admin)
def delete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course_id = lesson.course.id
    lesson.delete()
    messages.success(request, "Lesson deleted successfully!")
    return redirect("manage_lessons", course_id=course_id)


# ##############################################################################

# View to add a new email configuration
def add_email_config(request):
    if request.method == 'POST':
        email_host = request.POST.get('email_host')
        email_port = request.POST.get('email_port')
        email_use_tls = request.POST.get('email_use_tls') == 'on'
        email_host_user = request.POST.get('email_host_user')
        email_host_password = request.POST.get('email_host_password')

        # Create and save the new EmailConfig instance
        EmailConfig.objects.create(
            email_host=email_host,
            email_port=email_port,
            email_use_tls=email_use_tls,
            email_host_user=email_host_user,
            email_host_password=email_host_password
        )

        messages.success(request, "Email configuration added successfully.")
        return redirect('view_email_configs')  # Redirect to view the email configs

    return render(request, 'email/add_email_config.html')

# View to edit an existing email configuration
def edit_email_config(request, email_config_id):
    email_config = get_object_or_404(EmailConfig, id=email_config_id)

    if request.method == 'POST':
        email_config.email_host = request.POST.get('email_host')
        email_config.email_port = request.POST.get('email_port')
        email_config.email_use_tls = request.POST.get('email_use_tls') == 'on'
        email_config.email_host_user = request.POST.get('email_host_user')
        email_config.email_host_password = request.POST.get('email_host_password')

        email_config.save()
        messages.success(request, "Email configuration updated successfully.")
        return redirect('view_email_configs')  # Redirect to view the email configs

    return render(request, 'email/edit_email_config.html', {'email_config': email_config})

# View to delete an email configuration
def delete_email_config(request, email_config_id):
    email_config = get_object_or_404(EmailConfig, id=email_config_id)
    email_config.delete()
    messages.success(request, "Email configuration deleted successfully.")
    return redirect('view_email_configs')  # Redirect to view the email configs

# View to list all email configurations
def view_email_configs(request):
    email_configs = EmailConfig.objects.all()
    return render(request, 'email/view_email_configs.html', {'email_configs': email_configs})


###################################################################################

# Semester Views
def semester_list(request):
    semesters = Semester.objects.all()
    return render(request, 'semester_list.html', {'semesters': semesters})

def semester_create(request):
    if request.method == "POST":
        name = request.POST['name']
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        description = request.POST.get('description', '')
        Semester.objects.create(name=name, start_date=start_date, end_date=end_date, description=description)
        return redirect('semester_list')
    return render(request, 'semester_form.html')

def semester_update(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    if request.method == "POST":
        semester.name = request.POST['name']
        semester.start_date = request.POST['start_date']
        semester.end_date = request.POST['end_date']
        semester.description = request.POST.get('description', '')
        semester.save()
        return redirect('semester_list')
    return render(request, 'semester_form.html', {'semester': semester})

def semester_delete(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    if request.method == "POST":
        semester.delete()
        return redirect('semester_list')
    return render(request, 'semester_confirm_delete.html', {'semester': semester})


# Department Views
def department_list(request):
    departments = Department.objects.all()
    return render(request, 'department_list.html', {'departments': departments})

def department_create(request):
    if request.method == "POST":
        name = request.POST['name']
        description = request.POST.get('description', '')
        Department.objects.create(name=name, description=description)
        return redirect('department_list')
    return render(request, 'department_form.html')

def department_update(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == "POST":
        department.name = request.POST['name']
        department.description = request.POST.get('description', '')
        department.save()
        return redirect('department_list')
    return render(request, 'department_form.html', {'department': department})

def department_delete(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == "POST":
        department.delete()
        return redirect('department_list')
    return render(request, 'department_confirm_delete.html', {'department': department})


# Session Views
def session_list(request):
    sessions = Session.objects.all()
    return render(request, 'session_list.html', {'sessions': sessions})

def session_create(request):
    if request.method == "POST":
        name = request.POST['name']
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        Session.objects.create(name=name, start_date=start_date, end_date=end_date)
        return redirect('session_list')
    return render(request, 'session_form.html')

def session_update(request, pk):
    session = get_object_or_404(Session, pk=pk)
    if request.method == "POST":
        session.name = request.POST['name']
        session.start_date = request.POST['start_date']
        session.end_date = request.POST['end_date']
        session.save()
        return redirect('session_list')
    return render(request, 'session_form.html', {'session': session})

def session_delete(request, pk):
    session = get_object_or_404(Session, pk=pk)
    if request.method == "POST":
        session.delete()
        return redirect('session_list')
    return render(request, 'session_confirm_delete.html', {'session': session})


##############################################################################

from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import redirect, render

def create_settings(request):
    students = Student.objects.all()
    if request.method == 'POST':
        student_id = request.POST.get('student')
        check_out_time_threshold = request.POST.get('check_out_time_threshold')

        student = Student.objects.get(id=student_id) if student_id else None

        # Check if settings already exist for the selected student
        if student and Settings.objects.filter(student=student).exists():
            messages.error(request, f"Check-out Threshold  for student '{student.name}' already exist.")
            return redirect('create_settings')

        # Create new settings
        try:
            Settings.objects.create(
                student=student, 
                check_out_time_threshold=check_out_time_threshold
            )
            # Success message
            messages.success(request, "Settings created successfully!")
        except IntegrityError:
            messages.error(request, "An error occurred while saving the settings. Please try again.")
            return redirect('create_settings')

        return redirect('settings_list')

    return render(request, 'settings_form.html', {'students': students})



# Read settings (list view)
def settings_list(request):
    settings = Settings.objects.all()
    for setting in settings:
        time_in_seconds = setting.check_out_time_threshold

        if time_in_seconds < 60:
            setting.formatted_time = f"{time_in_seconds} seconds"
        elif time_in_seconds < 3600:
            minutes = time_in_seconds // 60
            setting.formatted_time = f"{minutes} minutes"
        else:
            hours = time_in_seconds // 3600
            setting.formatted_time = f"{hours} hours"

    return render(request, 'settings_list.html', {'settings': settings})

# Update settings
def update_settings(request, pk):
    settings = get_object_or_404(Settings, pk=pk)
    
    if request.method == 'POST':
        student_id = request.POST.get('student')
        check_out_time_threshold = request.POST.get('check_out_time_threshold', 60)
        
        settings.student = get_object_or_404(Student, id=student_id) if student_id else None
        settings.check_out_time_threshold = check_out_time_threshold
        settings.save()
        return redirect('settings_list')
    
    students = Student.objects.all()
    return render(request, 'settings_form.html', {'settings': settings, 'students': students})

# Delete settings
def delete_settings(request, pk):
    settings = get_object_or_404(Settings, pk=pk)
    if request.method == 'POST':
        settings.delete()
        return redirect('settings_list')
    return render(request, 'settings_confirm_delete.html', {'settings': settings})


#################################################################################
from django.shortcuts import render, get_object_or_404, redirect
from .models import Leave

# Function to list all leave records
def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def leave_list(request):
    leaves = Leave.objects.all()
    return render(request, 'leave_list.html', {'leaves': leaves})

# Function to delete a leave record
def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def leave_delete(request, pk):
    leave = get_object_or_404(Leave, pk=pk)
    if request.method == "POST":
        leave.delete()
        return redirect('leave_list')
    return render(request, 'leave_confirm_delete.html', {'leave': leave})

# Function to approve a leave
def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def leave_approve(request, pk):
    leave = get_object_or_404(Leave, pk=pk)
    leave.approved = True
    leave.save()
    return redirect('leave_list')

# Function to reject a leave
def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def leave_reject(request, pk):
    leave = get_object_or_404(Leave, pk=pk)
    leave.approved = False
    leave.save()
    return redirect('leave_list')


#########################################################################
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Leave
from .forms import LeaveForm

@login_required
def Student_leave_list(request):
    # Fetch the leave records of the currently logged-in student
    student_profile = Student.objects.get(user=request.user)
    # Get the leave records for the student
    student_leaves = Leave.objects.filter(student=student_profile)

    return render(request, 'student/leave_list.html', {'student_leaves': student_leaves})

@login_required
def apply_leave(request):
    # Handle the leave application form
    if request.method == 'POST':
        form = LeaveForm(request.POST)
        if form.is_valid():
            # Associate the leave request with the logged-in student
            leave = form.save(commit=False)
            student_profile = Student.objects.get(user=request.user)
            leave.student = student_profile
            leave.save()

            return redirect('Student_leave_list')  # Redirect to the leave list after submitting

    else:
        form = LeaveForm()

    return render(request, 'student/apply_leave.html', {'form': form})

#########################################################################
# TEACHER WORKFLOW VIEWS
#########################################################################

@login_required
def teacher_dashboard(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        return redirect('admin_dashboard')
    
    assigned_classes = AssignedClass.objects.filter(teacher=teacher)
    
    return render(request, 'teacher/teacher_dashboard.html', {
        'teacher': teacher,
        'assigned_classes': assigned_classes
    })

@login_required
def teacher_mark_attendance(request, class_id):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        return redirect('login')

    assigned_class = get_object_or_404(AssignedClass, id=class_id, teacher=teacher)
    
    camera = assigned_class.camera
    course = assigned_class.course

    return render(request, 'teacher/teacher_mark_attendance.html', {
        'teacher': teacher,
        'assigned_class': assigned_class,
        'camera': camera,
        'course': course
    })

@login_required
def start_teacher_camera(request, class_id):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        return redirect('login')

    assigned_class = get_object_or_404(AssignedClass, id=class_id, teacher=teacher)
    cam_config = assigned_class.camera
    
    # Filter students that match course, department, semester
    students_in_class = Student.objects.filter(
        courses=assigned_class.course,
        department=assigned_class.department,
        semester=assigned_class.semester
    )
    
    cap = None
    window_name = f'Teacher Camera - {cam_config.location}'
    try:
        if cam_config.camera_source.isdigit():
            cap = cv2.VideoCapture(int(cam_config.camera_source))
        else:
            cap = cv2.VideoCapture(cam_config.camera_source)

        if not cap.isOpened():
            messages.error(request, "Unable to access the assigned camera.")
            return redirect('teacher_mark_attendance', class_id=class_id)

        threshold = cam_config.threshold
        pygame.mixer.init()
        success_sound = pygame.mixer.Sound('static/success.wav')
        
        cv2.namedWindow(window_name)

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            test_face_encodings = detect_and_encode(frame_rgb)
            
            if test_face_encodings:
                known_face_encodings, known_face_names = encode_uploaded_images()
                for test_face_encoding in test_face_encodings:
                    distances = [np.linalg.norm(test_face_encoding - known_face_encoding) for known_face_encoding in known_face_encodings]
                    
                    if not distances:
                        continue
                        
                    min_distance_idx = np.argmin(distances)
                    min_distance = distances[min_distance_idx]
                    
                    if min_distance <= threshold:
                        name = known_face_names[min_distance_idx]
                        if name != "Unknown":
                            # Verify if the student belongs to this class
                            student = students_in_class.filter(name=name).first()
                            
                            if student:
                                # Process attendance
                                with transaction.atomic():
                                    global_settings = Settings.objects.first()
                                    check_out_threshold_seconds = global_settings.check_out_time_threshold if global_settings else 28800
                                    
                                    # Modified Attendance object creation - include the course
                                    attendance, created = Attendance.objects.get_or_create(
                                        student=student, date=now().date(), course=assigned_class.course
                                    )

                                    if attendance.check_in_time is None:
                                        attendance.mark_checked_in()
                                        success_sound.play()
                                        cv2.putText(frame, f"{name}, checked in.", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                                    elif attendance.check_out_time is None:
                                        if now() >= attendance.check_in_time + timedelta(seconds=check_out_threshold_seconds):
                                            attendance.mark_checked_out()
                                            success_sound.play()
                                            cv2.putText(frame, f"{name}, checked out.", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                                        else:
                                            cv2.putText(frame, f"{name}, already checked in.", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
                                    else:
                                        cv2.putText(frame, f"{name}, already checked out.", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

            cv2.imshow(window_name, frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        messages.error(request, f"Camera error: {str(e)}")
    finally:
        if cap is not None:
            cap.release()
        cv2.destroyWindow(window_name)

    messages.success(request, "Camera attendance session ended.")
    return redirect('teacher_mark_attendance', class_id=class_id)

# Teacher CRUD Views

@login_required
def teacher_view_attendance(request, class_id):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        return redirect('login')

    assigned_class = get_object_or_404(AssignedClass, id=class_id, teacher=teacher)
    
    students_in_class = Student.objects.filter(
        courses=assigned_class.course,
        department=assigned_class.department,
        semester=assigned_class.semester
    )
    
    filter_date_str = request.GET.get('date')
    if filter_date_str:
        filter_date = filter_date_str
    else:
        filter_date = now().date()
        
    attendances_map = {a.student_id: a for a in Attendance.objects.filter(
        student__in=students_in_class,
        course=assigned_class.course,
        date=filter_date
    ).select_related('student')}
    
    attendance_records = []
    for student in students_in_class:
        att = attendances_map.get(student.id)
        if att:
            attendance_records.append({
                'student': student,
                'status': att.status,
                'check_in_time': att.check_in_time,
                'check_out_time': att.check_out_time,
                'is_late': att.is_late
            })
        else:
            attendance_records.append({
                'student': student,
                'status': 'Absent',
                'check_in_time': None,
                'check_out_time': None,
                'is_late': False
            })
    
    return render(request, 'teacher/teacher_view_attendance.html', {
        'teacher': teacher,
        'assigned_class': assigned_class,
        'attendances': attendance_records,
        'filter_date': str(filter_date)
    })


def teacher_list(request):
    teachers = Teacher.objects.all()
    return render(request, 'teacher_list.html', {'teachers': teachers})

def teacher_create(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        department_id = request.POST.get('department_id')

        # Check if username exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Please choose a different one.")
            departments = Department.objects.all()
            return render(request, 'teacher_form.html', {'departments': departments})

        # Create user
        user = User.objects.create_user(username=username, password=password, email=email)
        
        # Determine department
        department = get_object_or_404(Department, id=department_id) if department_id else None

        # Create Teacher Profile
        Teacher.objects.create(
            user=user, name=name, email=email, 
            phone_number=phone_number, department=department
        )
        return redirect('teacher_list')
            
    departments = Department.objects.all()
    return render(request, 'teacher_form.html', {
        'departments': departments
    })

def teacher_update(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == "POST":
        teacher.name = request.POST.get('name')
        teacher.email = request.POST.get('email')
        teacher.phone_number = request.POST.get('phone_number')
        department_id = request.POST.get('department_id')
        teacher.department = get_object_or_404(Department, id=department_id) if department_id else None
        
        # Check if password change is requested
        password = request.POST.get('password')
        if password:
            teacher.user.set_password(password)
            teacher.user.save()
            
        teacher.save()
        return redirect('teacher_list')
        
    departments = Department.objects.all()
    return render(request, 'teacher_form.html', {
        'teacher': teacher,
        'departments': departments
    })

def teacher_delete(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == "POST":
        user = teacher.user # Also delete the associated user
        teacher.delete()
        user.delete()
        return redirect('teacher_list')
    return render(request, 'teacher_confirm_delete.html', {'teacher': teacher})

# Assigned Class CRUD Views
def assigned_class_list(request):
    assigned_classes = AssignedClass.objects.all()
    return render(request, 'assigned_class_list.html', {'assigned_classes': assigned_classes})

def assigned_class_create(request):
    if request.method == "POST":
        teacher_id = request.POST.get('teacher_id')
        course_id = request.POST.get('course_id')
        department_id = request.POST.get('department_id')
        semester_id = request.POST.get('semester_id')
        camera_id = request.POST.get('camera_id')

        teacher = get_object_or_404(Teacher, id=teacher_id) if teacher_id else None
        course = get_object_or_404(Course, id=course_id) if course_id else None
        department = get_object_or_404(Department, id=department_id) if department_id else None
        semester = get_object_or_404(Semester, id=semester_id) if semester_id else None
        camera = get_object_or_404(CameraConfiguration, id=camera_id) if camera_id else None

        if teacher and course and department and semester:
            AssignedClass.objects.create(
                teacher=teacher, course=course, department=department, 
                semester=semester, camera=camera
            )
            return redirect('assigned_class_list')
            
    teachers = Teacher.objects.all()
    courses = Course.objects.all()
    departments = Department.objects.all()
    semesters = Semester.objects.all()
    cameras = CameraConfiguration.objects.all()
    
    return render(request, 'assigned_class_form.html', {
        'teachers': teachers,
        'courses': courses,
        'departments': departments,
        'semesters': semesters,
        'cameras': cameras
    })

def assigned_class_update(request, pk):
    assigned_class = get_object_or_404(AssignedClass, pk=pk)
    if request.method == "POST":
        teacher_id = request.POST.get('teacher_id')
        course_id = request.POST.get('course_id')
        department_id = request.POST.get('department_id')
        semester_id = request.POST.get('semester_id')
        camera_id = request.POST.get('camera_id')

        assigned_class.teacher = get_object_or_404(Teacher, id=teacher_id) if teacher_id else assigned_class.teacher
        assigned_class.course = get_object_or_404(Course, id=course_id) if course_id else assigned_class.course
        assigned_class.department = get_object_or_404(Department, id=department_id) if department_id else assigned_class.department
        assigned_class.semester = get_object_or_404(Semester, id=semester_id) if semester_id else assigned_class.semester
        assigned_class.camera = get_object_or_404(CameraConfiguration, id=camera_id) if camera_id else None
        
        assigned_class.save()
        return redirect('assigned_class_list')
        
    teachers = Teacher.objects.all()
    courses = Course.objects.all()
    departments = Department.objects.all()
    semesters = Semester.objects.all()
    cameras = CameraConfiguration.objects.all()
    
    return render(request, 'assigned_class_form.html', {
        'assigned_class': assigned_class,
        'teachers': teachers,
        'courses': courses,
        'departments': departments,
        'semesters': semesters,
        'cameras': cameras
    })

def assigned_class_delete(request, pk):
    assigned_class = get_object_or_404(AssignedClass, pk=pk)
    if request.method == "POST":
        assigned_class.delete()
        return redirect('assigned_class_list')
    return render(request, 'assigned_class_confirm_delete.html', {'assigned_class': assigned_class})
