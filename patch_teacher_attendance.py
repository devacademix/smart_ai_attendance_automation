import re

views_file = 'app1/views.py'
with open(views_file, 'r', encoding='utf-8') as f:
    views_content = f.read()

new_views = """
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
        
    attendances = Attendance.objects.filter(
        student__in=students_in_class,
        course=assigned_class.course,
        date=filter_date
    ).select_related('student')
    
    return render(request, 'teacher/teacher_view_attendance.html', {
        'teacher': teacher,
        'assigned_class': assigned_class,
        'attendances': attendances,
        'filter_date': str(filter_date)
    })
"""

if 'def teacher_view_attendance(request, class_id):' not in views_content:
    # Insert before the closing # TEACHER WORKFLOW VIEWS
    if 'def teacher_list(request):' in views_content:
        views_content = views_content.replace('def teacher_list(request):', new_views + '\n\ndef teacher_list(request):')
        with open(views_file, 'w', encoding='utf-8') as f:
            f.write(views_content)
        print("Added teacher_view_attendance views.")

urls_file = 'app1/urls.py'
with open(urls_file, 'r', encoding='utf-8') as f:
    urls_content = f.read()

new_urls = """
    path('teacher/view-attendance/<int:class_id>/', views.teacher_view_attendance, name='teacher_view_attendance'),
"""

if 'teacher_view_attendance' not in urls_content:
    urls_content = urls_content.replace("path('teacher/start-camera/<int:class_id>/', views.start_teacher_camera, name='start_teacher_camera'),", 
                                       "path('teacher/start-camera/<int:class_id>/', views.start_teacher_camera, name='start_teacher_camera'),\n" + new_urls)
    with open(urls_file, 'w', encoding='utf-8') as f:
        f.write(urls_content)
    print("Added teacher_view_attendance URLs.")
