# 🎓 Smart Attendance System — Complete Project Workflow

## 📌 Overview

This is a **Django-based Face Recognition Attendance System** that uses **AI/ML (FaceNet + OpenCV)** to automatically detect and recognize student faces via camera, mark attendance, and manage the entire academic workflow including fees, leaves, courses, and email notifications.

---

## 🏗️ Tech Stack

| Technology | Purpose |
|---|---|
| **Django 5.0.7** | Web framework (Backend + Frontend) |
| **SQLite** | Database |
| **FaceNet (PyTorch)** | Face recognition AI model |
| **OpenCV** | Camera capture & image processing |
| **HTML/CSS/JS** | Frontend templates |
| **Pygame** | Audio/media support |

---

## 🗂️ Project Structure

```
Face-recognition-attandance-system-v3/
├── Project101/          # Django project settings
│   ├── settings.py      # Configuration
│   ├── urls.py          # Root URL routing
│   ├── wsgi.py / asgi.py
├── app1/                # Main application
│   ├── models.py        # 15 Database models
│   ├── views.py         # 60+ view functions
│   ├── urls.py          # All URL routes
│   ├── forms.py         # Django forms
│   ├── admin.py         # Admin panel config
├── templates/           # HTML templates
│   ├── home.html        # Landing page
│   ├── login.html       # Login page
│   ├── Mark_attendance.html
│   ├── register_student.html
│   ├── student/         # Student dashboard
│   ├── camera/          # Camera config
│   ├── courses/         # Course management
│   ├── fee/             # Fee management
│   ├── email/           # Email config
├── media/               # Uploaded student images
├── static/              # CSS, JS, images
├── db.sqlite3           # SQLite database
```

---

## 📊 Database Models (15 Models)

```mermaid
erDiagram
    User ||--|| Student : "has profile"
    Student ||--o{ Attendance : "has"
    Student ||--o{ Fee : "has"
    Student ||--o{ Leave : "applies"
    Fee ||--o{ FeePayment : "has payments"
    Fee ||--o{ AdvancePayment : "has advances"
    
    Semester ||--o{ Student : "enrolled in"
    Department ||--o{ Student : "belongs to"
    Session ||--o{ Student : "part of"
    Course ||--o{ Lesson : "contains"
    
    Settings }|--|| User : "configured by"
    CameraConfiguration }|--|| User : "managed by"
    EmailConfig }|--|| User : "set by"
    LateCheckInPolicy }|--|| User : "defined by"
```

| # | Model | Purpose |
|---|---|---|
| 1 | **Semester** | Academic semesters (1st, 2nd, etc.) |
| 2 | **Department** | Departments (CS, IT, etc.) |
| 3 | **Session** | Academic sessions (2024-25, etc.) |
| 4 | **Course** | Courses with video lessons |
| 5 | **Lesson** | Individual lessons within courses |
| 6 | **Student** | Student profiles with face images |
| 7 | **LateCheckInPolicy** | Late attendance rules |
| 8 | **Attendance** | Daily attendance records |
| 9 | **Fee** | Fee records per student |
| 10 | **FeePayment** | Fee payment transactions |
| 11 | **AdvancePayment** | Advance fee payments |
| 12 | **CameraConfiguration** | IP camera settings |
| 13 | **EmailConfig** | Email notification config |
| 14 | **Settings** | System-wide settings |
| 15 | **Leave** | Student leave applications |

---

## 🔄 Complete Workflow

### 1️⃣ Authentication Flow

```mermaid
flowchart LR
    A[User visits /] --> B[Home Page]
    B --> C[Click Login]
    C --> D[/login/ page]
    D --> E{Credentials Valid?}
    E -->|Yes + Admin| F[Admin Dashboard]
    E -->|Yes + Student| G[Student Dashboard]
    E -->|No| D
    F --> H[Logout → /login/]
    G --> H
```

- **Admin users** (`is_staff=True`) → Redirected to **Admin Dashboard** (`/admin-dashboard/`)
- **Student users** → Redirected to **Student Dashboard** (`/student-dashboard/`)

---

### 2️⃣ Student Registration Flow (Admin)

```mermaid
flowchart TD
    A[Admin → Register Student] --> B[/register/]
    B --> C[Fill Form: Name, Roll No, Semester, Department, Session]
    C --> D[Upload Face Photo]
    D --> E[AI: detect_and_encode_uploaded_image]
    E --> F{Face Detected?}
    F -->|Yes| G[Save Student + Face Encoding]
    G --> H[Create Django User Account]
    H --> I[/register-success/]
    F -->|No| J[Error: No face found]
```

> [!IMPORTANT]
> During registration, the system uses **FaceNet AI model** to detect the face in the uploaded photo and creates a **face encoding (embedding)** that is stored for later recognition.

---

### 3️⃣ 📸 Face Recognition Attendance Flow (Core Feature)

```mermaid
flowchart TD
    A[Admin → Mark Attendance] --> B[/mark-attendance/]
    B --> C[Open Camera / IP Camera]
    C --> D[Capture Live Video Frame]
    D --> E[OpenCV: Detect Faces in Frame]
    E --> F[FaceNet: Generate Face Encoding]
    F --> G[Compare with All Stored Encodings]
    G --> H{Match Found?}
    H -->|Yes| I[Identify Student]
    I --> J[Mark Attendance as PRESENT]
    J --> K[Check Late Check-in Policy]
    K --> L[Save Attendance Record with Timestamp]
    H -->|No| M[Unknown Face - Skip]
    L --> D
    M --> D
```

**Key Functions:**
- `capture_and_recognize()` — Uses webcam
- `capture_and_recognize_with_cam()` — Uses IP camera (RTSP)
- `recognize_faces()` — AI comparison logic
- `detect_and_encode()` — Face encoding generation
- `process_frame()` — Real-time frame processing

> [!NOTE]
> The system supports both **local webcam** and **IP cameras** (configured via Camera Configuration). It runs real-time face detection and matches against all registered students.

---

### 4️⃣ Admin Dashboard Features

```mermaid
flowchart TD
    AD[Admin Dashboard] --> A[📸 Mark Attendance]
    AD --> B[👨‍🎓 Student Management]
    AD --> C[💰 Fee Management]
    AD --> D[📚 Course Management]
    AD --> E[⚙️ Settings]
    AD --> F[📧 Email Config]
    AD --> G[📷 Camera Config]
    AD --> H[📅 Leave Management]
    
    B --> B1[Register / List / Edit / Delete Students]
    B --> B2[Authorize Students]
    B --> B3[View Attendance Lists]
    
    C --> C1[Add Fees]
    C --> C2[Record Payments]
    C --> C3[View Fee Details]
    
    D --> D1[Add/Edit/Delete Courses]
    D --> D2[Add/Edit/Delete Lessons]
    
    E --> E1[Semester / Department / Session CRUD]
    E --> E2[Late Check-in Policies]
    E --> E3[System Settings]
    
    H --> H1[View Leave Requests]
    H --> H2[Approve / Reject Leaves]
```

---

### 5️⃣ Student Dashboard Features

```mermaid
flowchart TD
    SD[Student Dashboard] --> A[📊 View My Attendance]
    SD --> B[💰 View My Fees]
    SD --> C[📚 Browse Courses]
    SD --> D[📝 Apply for Leave]
    SD --> E[📋 View Leave Status]
    
    C --> C1[Course List]
    C1 --> C2[Course Detail]
    C2 --> C3[Watch Lesson Videos]
```

---

### 6️⃣ Fee Management Flow

```mermaid
flowchart LR
    A[Admin adds Fee] --> B[Student owes amount]
    B --> C[Admin records Payment]
    C --> D{Fully Paid?}
    D -->|Yes| E[Fee marked as Paid ✅]
    D -->|No| F[Partial payment recorded]
    F --> C
```

---

### 7️⃣ Leave Management Flow

```mermaid
flowchart LR
    A[Student applies Leave] --> B[Leave Request Created - Pending]
    B --> C[Admin Reviews]
    C --> D{Decision}
    D -->|Approve| E[Leave Approved ✅]
    D -->|Reject| F[Leave Rejected ❌]
    E --> G[Attendance updated for leave dates]
```

---

## 🔗 All URL Routes

| URL | Function | Access |
|---|---|---|
| `/` | Home page | Public |
| `/login/` | User login | Public |
| `/logout/` | User logout | Authenticated |
| `/admin-dashboard/` | Admin dashboard | Admin |
| `/mark-attendance/` | Face recognition attendance | Admin |
| `/register/` | Register new student | Admin |
| `/student-list/` | List all students | Admin |
| `/student/<id>/` | Student details | Admin |
| `/student-authorize/<id>/` | Authorize student | Admin |
| `/student-dashboard/` | Student dashboard | Student |
| `/student-attendance/` | Student's own attendance | Student |
| `/student-fee-detail/` | Student's own fees | Student |
| `/apply_leave/` | Apply for leave | Student |
| `/Student_leave_list/` | Student's leave list | Student |
| `/courses/` | Course listing | Authenticated |
| `/camera-config/` | Camera settings | Admin |
| `/semesters/` | Manage semesters | Admin |
| `/departments/` | Manage departments | Admin |
| `/sessions/` | Manage sessions | Admin |
| `/settings/` | System settings | Admin |
| `/late-checkin-policies/` | Late policies | Admin |
| `/email-configs/` | Email configuration | Admin |
| `/admin/` | Django admin panel | Superuser |

---

## 🚀 How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run migrations
python manage.py makemigrations
python manage.py migrate

# 3. Create superuser (admin)
python manage.py createsuperuser

# 4. Start server
python manage.py runserver

# 5. Open browser
# Home: http://127.0.0.1:8000/
# Login: http://127.0.0.1:8000/login/
# Admin: http://127.0.0.1:8000/admin/
```

---

## 🔑 User Roles

| Role | Access | How to Create |
|---|---|---|
| **Superuser** | Full Django Admin + App Admin | `python manage.py createsuperuser` |
| **Staff/Admin** | App Admin Dashboard | Create user with `is_staff=True` |
| **Student** | Student Dashboard only | Auto-created during student registration |

> [!TIP]
> When you register a new student via `/register/`, a Django **User account is automatically created** for that student. The student can then login with their credentials to access the Student Dashboard.
