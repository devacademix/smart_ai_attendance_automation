from django.urls import path
from . import views

urlpatterns = [
    # Home and Dashboard Views
    path('', views.home, name='home'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),

    # Student Registration and Attendance
    path('register_student/', views.register_student, name='register_student'),
    path('mark_attendance', views.mark_attendance, name='mark_attendance'),
    path('register_success/', views.register_success, name='register_success'),
    path('students/', views.student_list, name='student-list'),
    path('students/<int:pk>/', views.student_detail, name='student-detail'),
    path('students/attendance/', views.student_attendance_list, name='student_attendance_list'),
    path('students/<int:pk>/authorize/', views.student_authorize, name='student-authorize'),
    path('students/<int:pk>/delete/', views.student_delete, name='student-delete'),
    path('student/edit/<int:pk>/', views.student_edit, name='student-edit'),
    path('student-fee-detail/', views.student_fee_detail, name='student_fee_detail'),
    
    # Capture and Recognize Views
    path('capture-and-recognize/', views.capture_and_recognize, name='capture_and_recognize'),
    path('recognize_with_cam/', views.capture_and_recognize_with_cam, name='capture_and_recognize_with_cam'),
    
    # User Authentication Views
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Attendance Notifications
    path('send_attendance_notifications', views.send_attendance_notifications, name='send_attendance_notifications'),
    
    # Student Fees Management
    path('students-fees/', views.student_list_with_fees, name='student_list_with_fees'),
    path('students-fees/<int:student_id>/add_fee/', views.add_fee_for_student, name='add_fee_for_student'),
    path('fee/<int:fee_id>/pay/', views.pay_fee_for_student, name='pay_fee_for_student'),
    path('students-fees/<int:student_id>/fee_details/', views.student_fee_details, name='student_fee_details'),
    path('payment/<int:payment_id>/delete/', views.delete_fee_payment, name='delete_fee_payment'),
    path('fee/<int:fee_id>/mark_paid/', views.mark_fee_as_paid, name='mark_fee_as_paid'),
    
    # Late Check-in Policies
    path('late_checkin_policy_list/', views.late_checkin_policy_list, name='late_checkin_policy_list'),
    path('late-checkin-policies/create/', views.create_late_checkin_policy, name='create_late_checkin_policy'),
    path('late-checkin-policies/<int:policy_id>/update/',views.update_late_checkin_policy, name='update_late_checkin_policy'),
    path('delete-late-checkin-policy/<int:policy_id>/', views.delete_late_checkin_policy, name='delete_late_checkin_policy'),
    
    ########################################################### Camera Configurations
    path('camera-config/', views.camera_config_create, name='camera_config_create'),
    path('camera-config/list/', views.camera_config_list, name='camera_config_list'),
    path('camera-config/update/<int:pk>/', views.camera_config_update, name='camera_config_update'),
    path('camera-config/delete/<int:pk>/', views.camera_config_delete, name='camera_config_delete'),
    
    # Attendance (General View)
    path('attendance/', views.student_attendance, name='student_attendance'),

    path('admin-courses/', views.manage_courses, name='manage_courses'),
    path('admin-courses/add/', views.add_course, name='add_course'),
    path('admin-courses/edit/<int:course_id>/', views.edit_course, name='edit_course'),
    path('admin-courses/delete/<int:course_id>/', views.delete_course, name='delete_course'),
    path('admin-courses/<int:course_id>/lessons/', views.manage_lessons, name='manage_lessons'),
    path('admin-courses/<int:course_id>/lessons/add/', views.add_lesson, name='add_lesson'),
    path('admin-lessons/edit/<int:lesson_id>/', views.edit_lesson, name='edit_lesson'),
    path('admin-lessons/delete/<int:lesson_id>/', views.delete_lesson, name='delete_lesson'),
    # Similarly, add URLs for lessons
    path('courses/', views.course_list, name='course_list'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('lessons/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    # For email adding and upateing and editing
    path('email-configs/', views.view_email_configs, name='view_email_configs'),
    path('email-configs/add/', views.add_email_config, name='add_email_config'),
    path('email-configs/edit/<int:email_config_id>/', views.edit_email_config, name='edit_email_config'),
    path('email-configs/delete/<int:email_config_id>/', views.delete_email_config, name='delete_email_config'),

     # Semester URLs
    path('semesters/', views.semester_list, name='semester_list'),
    path('semesters/create/', views.semester_create, name='semester_create'),
    path('semesters/update/<int:pk>/', views.semester_update, name='semester_update'),
    path('semesters/delete/<int:pk>/', views.semester_delete, name='semester_delete'),

    # Department URLs
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/update/<int:pk>/', views.department_update, name='department_update'),
    path('departments/delete/<int:pk>/', views.department_delete, name='department_delete'),

    # Session URLs
    path('sessions/', views.session_list, name='session_list'),
    path('sessions/create/', views.session_create, name='session_create'),
    path('sessions/update/<int:pk>/', views.session_update, name='session_update'),
    path('sessions/delete/<int:pk>/', views.session_delete, name='session_delete'),
    # This url is for check out time policy settings
    path('settings-list/', views.settings_list, name='settings_list'),
    path('settings/create/', views.create_settings, name='create_settings'),
    path('settings/<int:pk>/update/', views.update_settings, name='update_settings'),
    path('settings/<int:pk>/delete/', views.delete_settings, name='delete_settings'),
    #######################################
    path('leaves/', views.leave_list, name='leave_list'),
    path('leaves/<int:pk>/delete/', views.leave_delete, name='leave_delete'),
    path('leaves/<int:pk>/approve/', views.leave_approve, name='leave_approve'),
    path('leaves/<int:pk>/reject/', views.leave_reject, name='leave_reject'),
    ###########################################
    path('Student_leave_list/', views.Student_leave_list, name='Student_leave_list'),
    path('apply_leave/', views.apply_leave, name='apply_leave'),
    
    # Teacher URLs
    path('teacher-dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/mark-attendance/<int:class_id>/', views.teacher_mark_attendance, name='teacher_mark_attendance'),
    path('teacher/start-camera/<int:class_id>/', views.start_teacher_camera, name='start_teacher_camera'),

    path('teacher/view-attendance/<int:class_id>/', views.teacher_view_attendance, name='teacher_view_attendance'),



    path('teachers/', views.teacher_list, name='teacher_list'),
    path('teachers/create/', views.teacher_create, name='teacher_create'),
    path('teachers/update/<int:pk>/', views.teacher_update, name='teacher_update'),
    path('teachers/delete/<int:pk>/', views.teacher_delete, name='teacher_delete'),


    path('assigned-classes/', views.assigned_class_list, name='assigned_class_list'),
    path('assigned-classes/create/', views.assigned_class_create, name='assigned_class_create'),
    path('assigned-classes/update/<int:pk>/', views.assigned_class_update, name='assigned_class_update'),
    path('assigned-classes/delete/<int:pk>/', views.assigned_class_delete, name='assigned_class_delete'),

]
