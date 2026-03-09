# Smart AI Attendance Automation

A comprehensive, AI-powered Face Recognition Attendance System built with Django and OpenCV. This platform provides an enterprise-grade solution for universities and schools to automate their attendance tracking using live camera feeds and facial recognition technology.

## 🌟 Key Features

### 👤 Role-Based Access Control
- **Super Admin Panel**: Full system control for managing all entities (Students, Teachers, Departments, Courses, Fees, Leaves).
- **Teacher Dashboard**: Dedicated interface for teachers to view their assigned classes, start live camera attendance sessions, and review student attendance records.
- **Student Dashboard**: Interface for students to view their attendance metrics, apply for leaves, and pay fee dues.

### 📸 AI Facial Recognition
- **Live Classroom Cameras**: Link IP cameras or webcams to specific classrooms.
- **Automated Attendance**: Once a teacher starts the camera feed, the system automatically detects students' faces, verifies them against the registered encodings, and marks them present.
- **Dynamic Check-in/Check-out**: System handles late check-ins and check-out tracking based on customized time policies.

### 🏫 Academic Management
- **Departments & Courses**: Manage university departments, subjects, lessons, and semesters.
- **Assigned Classes**: Assign teachers to specific courses and departments linked with physical classroom camera configurations.
- **Session & Semester tracking**: Easily manage academic years and periods.

### 💰 Fees & Leaves
- **Fee Management**: Track student fee payments, outstanding dues, and payment history.
- **Leave Applications**: Students can apply for leave. Admins can approve or reject them.

## 🛠️ Technology Stack
- **Backend**: Python, Django
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **AI/Computer Vision**: OpenCV, face_recognition, dlib, numpy
- **Database**: SQLite (Default) / PostgreSQL (Production ready)

## 🚀 Getting Started

### Prerequisites
Make sure you have Python 3.9+ and pip installed on your machine. You will also need a webcam or RTSP camera feed for testing.

*Note: For Windows users, installing `dlib` (used by `face_recognition`) requires CMake and Visual Studio C++ Build Tools.*

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/devacademix/smart_ai_attendance_automation.git
   cd smart_ai_attendance_automation
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(If `requirements.txt` is missing, you mainly need: `django`, `opencv-python`, `face_recognition`, `numpy`, `pygame`)*

4. **Run Database Migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create a Superuser (Admin):**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start the Development Server:**
   ```bash
   python manage.py runserver
   ```

7. **Access the application:**
   Open your browser and navigate to `http://127.0.0.1:8000/`.

## 📖 How to Use

1. **Setup Core Data (Admin):**
   Log in as Super Admin. Form the side menu, create Departments, Semesters, Courses, and Physical Camera Configurations.
2. **Register Students & Teachers:**
   Register new students (their face encodings are saved automatically upon photo upload). Create new teacher accounts directly from the dashboard.
3. **Assign Classes:**
   Go to **Manage Assigned Classes** and link a Teacher -> Course -> Department -> Semester -> Camera Setup.
4. **Mark Attendance (Teacher):**
   The teacher logs in, goes to their dashboard, and clicks **Mark Attendance** on the assigned class. The AI camera pops up and automatically captures/verifies students as they walk in.
5. **View Attendance:**
   Teachers can click **View Attendance** to see a full roster mapping of present/absent students for any given date.

## 🔒 Security & Compliance
- Full Role-Based Access Controls (RBAC).
- Extracted face embeddings are stored directly in the database logic.
- Built-in error handling and safe routing for all forms.

## 🤝 Contributing
Contributions, issues, and feature requests are welcome!

## 📝 License
This project is licensed under the MIT License.
