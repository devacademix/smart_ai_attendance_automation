# 🔑 Super Admin — Complete Workflow

## Step 1: Login
```
URL: http://127.0.0.1:8000/login/
Credentials: superuser username + password
```

```mermaid
flowchart LR
    A[Visit /login/] --> B[Enter Username & Password]
    B --> C{is_staff / is_superuser?}
    C -->|Yes| D["🏠 Admin Dashboard (/admin-dashboard/)"]
    C -->|No| E[Student Dashboard]
```

---

## Step 2: Admin Dashboard (Home Screen)

```
URL: http://127.0.0.1:8000/admin-dashboard/
```

The dashboard shows **live analytics** at a glance:

| Metric | Description |
|---|---|
| 📊 Total Students | Count of all registered students |
| ✅ Total Attendance | All attendance records |
| 🟢 Present Today | Students present today |
| 🔴 Absent Today | Students absent today |
| ⏰ Late Today | Late check-ins today |
| 📷 Total Cameras | Configured cameras |
| 💰 Pending Fees | Students with unpaid fees |

---

## Step 3: All Admin Functions

```mermaid
flowchart TD
    ADMIN["🔑 Super Admin Dashboard"]
    
    ADMIN --> SM["👨‍🎓 Student Management"]
    ADMIN --> ATT["📸 Mark Attendance"]
    ADMIN --> FM["💰 Fee Management"]
    ADMIN --> LM["📝 Leave Management"]
    ADMIN --> CM["📚 Course Management"]
    ADMIN --> AC["🏫 Academic Config"]
    ADMIN --> CC["📷 Camera Config"]
    ADMIN --> EC["📧 Email Config"]
    ADMIN --> SS["⚙️ System Settings"]
    ADMIN --> LCP["⏰ Late Check-in Policy"]
    ADMIN --> DA["🛠️ Django Admin Panel"]
    
    SM --> SM1["Register Student"]
    SM --> SM2["View Student List"]
    SM --> SM3["Edit Student"]
    SM --> SM4["Delete Student"]
    SM --> SM5["Authorize Student"]
    SM --> SM6["View Attendance List"]
    
    AC --> AC1["Semesters"]
    AC --> AC2["Departments"]
    AC --> AC3["Sessions"]
```

---

## 📋 Feature-wise Detailed Workflow

### 🟢 A. Student Registration

```
URL: http://127.0.0.1:8000/register/
```

```mermaid
flowchart TD
    A["Click 'Register Student'"] --> B["Fill Registration Form"]
    B --> C["📝 Name, Roll Number"]
    B --> D["🏫 Select Semester, Department, Session"]
    B --> E["📸 Upload Face Photo"]
    E --> F["🤖 AI: FaceNet detects face & creates encoding"]
    F --> G{Face Detected?}
    G -->|✅ Yes| H["Student + User Account created"]
    H --> I["Redirect to Success Page"]
    G -->|❌ No| J["Error: Upload a clear face photo"]
```

> [!IMPORTANT]
> The uploaded photo must have a **clear, front-facing face**. The AI model (FaceNet) extracts a 512-dimensional face vector that is stored for future recognition.

---

### 🟢 B. Student List & Management

| Action | URL | What it does |
|---|---|---|
| **View All Students** | `/student-list/` | Shows all registered students |
| **Student Details** | `/student/<id>/` | Full profile + attendance history |
| **Edit Student** | `/student-edit/<id>/` | Update name, department, photo, etc. |
| **Delete Student** | `/student-delete/<id>/` | Remove student & their data |
| **Authorize Student** | `/student-authorize/<id>/` | Verify/authorize a student |
| **Attendance List** | `/student-attendance-list/` | View all attendance records |

---

### 🟢 C. 📸 Mark Attendance (Face Recognition — CORE)

```
URL: http://127.0.0.1:8000/mark-attendance/
```

```mermaid
flowchart TD
    A["Admin clicks 'Mark Attendance'"] --> B{Camera Type?}
    B -->|"Webcam"| C["Opens Local Webcam"]
    B -->|"IP Camera"| D["Connects to RTSP Stream"]
    
    C --> E["📹 Live Video Feed Starts"]
    D --> E
    
    E --> F["🔍 OpenCV detects faces in each frame"]
    F --> G["🤖 FaceNet generates face encoding"]
    G --> H["📊 Compare with ALL registered students"]
    H --> I{Match Found?}
    
    I -->|"✅ Yes (Similarity > Threshold)"| J["🟢 Student Identified!"]
    J --> K["Display Name on Video Feed"]
    K --> L["Mark Attendance: PRESENT"]
    L --> M{Late Check-in Policy?}
    M -->|"Within Time"| N["Status: ON TIME ✅"]
    M -->|"After Cutoff"| O["Status: LATE ⏰"]
    
    I -->|"❌ No Match"| P["Unknown Face — Skipped"]
    
    N --> Q["Save to Database with Timestamp"]
    O --> Q
    Q --> E
    P --> E
```

**How the AI works internally:**

```mermaid
flowchart LR
    A["Camera Frame"] --> B["MTCNN: Detect Face Box"]
    B --> C["Crop Face Region"]
    C --> D["Resize to 160x160"]
    D --> E["FaceNet InceptionResnetV1"]
    E --> F["512-dim Face Vector"]
    F --> G["Compare with stored vectors"]
    G --> H["Cosine Similarity / Distance"]
    H --> I{Distance < Threshold?}
    I -->|Yes| J["✅ Match Found"]
    I -->|No| K["❌ Unknown"]
```

---

### 🟢 D. Fee Management

| Action | URL | What it does |
|---|---|---|
| **Student List with Fees** | `/student-list-with-fees/` | All students + fee status |
| **Add Fee** | `/add-fee/<student_id>/` | Assign new fee to student |
| **Record Payment** | `/pay-fee/<student_id>/` | Record a fee payment |
| **Fee Details** | `/student-fee-details/<student_id>/` | View complete fee history |
| **Delete Payment** | `/delete-fee-payment/<id>/` | Remove a payment record |
| **Mark as Paid** | `/mark-fee-as-paid/<fee_id>/` | Manually mark fee as paid |

```mermaid
flowchart TD
    A["View Student List with Fees"] --> B["Select Student"]
    B --> C["Add Fee (Amount + Description)"]
    C --> D["Student owes ₹X"]
    D --> E["Record Payment (Full/Partial)"]
    E --> F{Fully Paid?}
    F -->|Yes| G["✅ Fee Cleared"]
    F -->|No| H["Remaining Balance Shown"]
    H --> E
```

---

### 🟢 E. Leave Management (`is_superuser` required)

```
URL: http://127.0.0.1:8000/leaves/
```

> [!IMPORTANT]
> Leave management requires **`is_superuser = True`**. Regular staff cannot approve/reject leaves.

```mermaid
flowchart TD
    A["View Leave Requests (/leaves/)"] --> B["See Pending Leave List"]
    B --> C["Select a Leave Request"]
    C --> D["View Details: Student, Dates, Reason"]
    D --> E{Decision}
    E -->|"✅ Approve"| F["Leave Approved"]
    F --> G["Attendance updated for leave dates"]
    E -->|"❌ Reject"| H["Leave Rejected"]
    E -->|"🗑️ Delete"| I["Leave Deleted"]
```

| Action | URL | Access |
|---|---|---|
| View All Leaves | `/leaves/` | Superuser only |
| Approve Leave | `/leaves/<id>/approve/` | Superuser only |
| Reject Leave | `/leaves/<id>/reject/` | Superuser only |
| Delete Leave | `/leaves/<id>/delete/` | Superuser only |

---

### 🟢 F. Course & Lesson Management (`is_staff` required)

```mermaid
flowchart TD
    A["Manage Courses (/manage-courses/)"] --> B["View All Courses"]
    B --> C["➕ Add New Course"]
    B --> D["✏️ Edit Course"]
    B --> E["🗑️ Delete Course"]
    B --> F["📖 Manage Lessons"]
    
    F --> G["View Lessons in Course"]
    G --> H["➕ Add Lesson (Title, Video, Content)"]
    G --> I["✏️ Edit Lesson"]
    G --> J["🗑️ Delete Lesson"]
```

| Action | URL |
|---|---|
| Manage Courses | `/manage-courses/` |
| Add Course | `/add-course/` |
| Edit Course | `/edit-course/<id>/` |
| Delete Course | `/delete-course/<id>/` |
| Manage Lessons | `/manage-lessons/<course_id>/` |
| Add Lesson | `/add-lesson/<course_id>/` |
| Edit Lesson | `/edit-lesson/<id>/` |
| Delete Lesson | `/delete-lesson/<id>/` |

---

### 🟢 G. Academic Configuration (CRUD)

```mermaid
flowchart LR
    CONFIG["⚙️ Academic Config"]
    CONFIG --> SEM["📅 Semesters (/semesters/)"]
    CONFIG --> DEP["🏢 Departments (/departments/)"]
    CONFIG --> SES["📆 Sessions (/sessions/)"]
    
    SEM --> SEM1["Create / Edit / Delete"]
    DEP --> DEP1["Create / Edit / Delete"]
    SES --> SES1["Create / Edit / Delete"]
```

| Module | List URL | Create | Edit | Delete |
|---|---|---|---|---|
| Semester | `/semesters/` | `/semesters/create/` | `/semesters/<pk>/update/` | `/semesters/<pk>/delete/` |
| Department | `/departments/` | `/departments/create/` | `/departments/<pk>/update/` | `/departments/<pk>/delete/` |
| Session | `/sessions/` | `/sessions/create/` | `/sessions/<pk>/update/` | `/sessions/<pk>/delete/` |

---

### 🟢 H. Camera Configuration

```
URL: http://127.0.0.1:8000/camera-config/
```

| Action | URL |
|---|---|
| View Cameras | `/camera-config/` |
| Add Camera | `/camera-config/create/` |
| Edit Camera | `/camera-config/update/<id>/` |
| Delete Camera | `/camera-config/delete/<id>/` |

> [!TIP]
> Configure IP cameras here (RTSP URL, camera name, location). These are used during attendance marking with the "IP Camera" option.

---

### 🟢 I. Email Configuration

| Action | URL |
|---|---|
| View Email Configs | `/email-configs/` |
| Add Config | `/add-email-config/` |
| Edit Config | `/edit-email-config/<id>/` |
| Delete Config | `/delete-email-config/<id>/` |

Used for **sending attendance notifications** to parents/students via email.

---

### 🟢 J. System Settings

```
URL: http://127.0.0.1:8000/settings/
```

| Action | URL |
|---|---|
| View Settings | `/settings/` |
| Create Setting | `/settings/create/` |
| Edit Setting | `/settings/<pk>/update/` |
| Delete Setting | `/settings/<pk>/delete/` |

---

### 🟢 K. Late Check-in Policies

```
URL: http://127.0.0.1:8000/late-checkin-policies/
```

Define rules for what counts as "late" attendance (e.g., after 9:15 AM = Late).

---

### 🟢 L. Django Admin Panel

```
URL: http://127.0.0.1:8000/admin/
```

> [!NOTE]
> Only **Superusers** can access the Django Admin Panel. This gives raw database access to all 15 models — useful for debugging and advanced management.

---

## 📧 Send Attendance Notifications

```
URL: http://127.0.0.1:8000/send-notifications/
Access: Staff only
```

Sends email notifications about attendance to configured recipients.

---

## 🗺️ Complete Super Admin Journey Map

```mermaid
flowchart TD
    START["🔐 Login as Super Admin"] --> DASH["📊 Admin Dashboard"]
    
    DASH --> SETUP["🔧 ONE-TIME SETUP"]
    SETUP --> S1["1. Create Semesters"]
    S1 --> S2["2. Create Departments"]
    S2 --> S3["3. Create Sessions"]
    S3 --> S4["4. Configure Cameras"]
    S4 --> S5["5. Set Email Config"]
    S5 --> S6["6. Set Late Check-in Policy"]
    S6 --> S7["7. Create Courses & Lessons"]
    
    DASH --> DAILY["📅 DAILY OPERATIONS"]
    DAILY --> D1["1. Register New Students"]
    D1 --> D2["2. Mark Attendance via Face Recognition"]
    D2 --> D3["3. Review Leave Requests"]
    D3 --> D4["4. Manage Fees & Payments"]
    D4 --> D5["5. Send Notifications"]
    D5 --> D6["6. View Reports & Analytics"]
```

---

## 🔑 Access Control Summary

| Feature | `is_staff` | `is_superuser` |
|---|---|---|
| Admin Dashboard | ✅ | ✅ |
| Student Management | ✅ | ✅ |
| Mark Attendance | ✅ | ✅ |
| Course Management | ✅ | ✅ |
| Fee Management | ✅ | ✅ |
| Send Notifications | ✅ | ✅ |
| **Leave Approve/Reject** | ❌ | ✅ |
| **Leave Delete** | ❌ | ✅ |
| **Django Admin Panel** | ❌ | ✅ |
