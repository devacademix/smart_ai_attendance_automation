import re

views_file = 'app1/views.py'
with open(views_file, 'r', encoding='utf-8') as f:
    views_content = f.read()

new_views = """
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
"""

if 'def assigned_class_list(request):' not in views_content:
    with open(views_file, 'a', encoding='utf-8') as f:
        f.write(new_views)
    print("Added Assigned Class views.")


urls_file = 'app1/urls.py'
with open(urls_file, 'r', encoding='utf-8') as f:
    urls_content = f.read()

new_urls = """
    path('assigned-classes/', views.assigned_class_list, name='assigned_class_list'),
    path('assigned-classes/create/', views.assigned_class_create, name='assigned_class_create'),
    path('assigned-classes/update/<int:pk>/', views.assigned_class_update, name='assigned_class_update'),
    path('assigned-classes/delete/<int:pk>/', views.assigned_class_delete, name='assigned_class_delete'),
"""

if 'assigned_class_list' not in urls_content:
    # Insert before the closing bracket of urlpatterns
    urls_content = urls_content.replace(']', new_urls + '\n]')
    with open(urls_file, 'w', encoding='utf-8') as f:
        f.write(urls_content)
    print("Added Assigned Class URLs.")
