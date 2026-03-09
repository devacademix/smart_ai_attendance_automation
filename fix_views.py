import sys

def fix_views():
    with open('app1/views.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    start_idx = -1
    for i, line in enumerate(lines):
        if line.startswith('def start_teacher_camera(request, class_id):'):
            start_idx = i - 1 # Include the @login_required decorator if any
            if not lines[start_idx].startswith('@login_required'):
                start_idx = i
            break
            
    if start_idx == -1:
        print("Could not find start_teacher_camera function")
        return
        
    truncate_lines = lines[:start_idx]
    
    new_code = """@login_required
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
"""
    with open('app1/views.py', 'w', encoding='utf-8') as f:
        f.writelines(truncate_lines)
        f.write(new_code)
    print("Fixed views.py!")

if __name__ == '__main__':
    fix_views()
