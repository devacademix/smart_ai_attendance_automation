import re

views_file = 'app1/views.py'
with open(views_file, 'r', encoding='utf-8') as f:
    views_content = f.read()

new_views = """
# Teacher CRUD Views
def teacher_list(request):
    teachers = Teacher.objects.all()
    return render(request, 'teacher_list.html', {'teachers': teachers})

def teacher_create(request):
    if request.method == "POST":
        user_id = request.POST.get('user_id')
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        department_id = request.POST.get('department_id')

        user = get_object_or_404(User, id=user_id) if user_id else None
        department = get_object_or_404(Department, id=department_id) if department_id else None

        if user:
            Teacher.objects.create(
                user=user, name=name, email=email, 
                phone_number=phone_number, department=department
            )
            return redirect('teacher_list')
            
    users_without_teacher = User.objects.filter(teacher_profile__isnull=True)
    departments = Department.objects.all()
    return render(request, 'teacher_form.html', {
        'users': users_without_teacher,
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
        teacher.delete()
        return redirect('teacher_list')
    return render(request, 'teacher_confirm_delete.html', {'teacher': teacher})
"""

if 'def teacher_list(request):' not in views_content:
    with open(views_file, 'a', encoding='utf-8') as f:
        f.write(new_views)
    print("Added teacher views.")


urls_file = 'app1/urls.py'
with open(urls_file, 'r', encoding='utf-8') as f:
    urls_content = f.read()

new_urls = """
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('teachers/create/', views.teacher_create, name='teacher_create'),
    path('teachers/update/<int:pk>/', views.teacher_update, name='teacher_update'),
    path('teachers/delete/<int:pk>/', views.teacher_delete, name='teacher_delete'),
"""

if 'teacher_list' not in urls_content:
    # Insert before the closing bracket of urlpatterns
    urls_content = urls_content.replace(']', new_urls + '\n]')
    with open(urls_file, 'w', encoding='utf-8') as f:
        f.write(urls_content)
    print("Added teacher URLs.")
