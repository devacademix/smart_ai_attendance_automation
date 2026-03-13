# 🚀 VPS Deployment Checklist

## ✅ Pre-Deployment (Local Testing)

- [ ] **Test web-based camera streaming locally**
  ```bash
  python manage.py runserver
  # Access: http://127.0.0.1:8000
  ```
  
- [ ] **Verify all new files exist:**
  - [ ] `app1/web_camera_stream.py`
  - [ ] `templates/teacher/teacher_camera_stream.html`
  - [ ] `VPS_CAMERA_SOLUTION.md`
  - [ ] `DEPLOYMENT_CHECKLIST.md` (this file)

- [ ] **Test both camera launch methods:**
  - [ ] Desktop mode (for local testing)
  - [ ] Web-based mode (for VPS)

- [ ] **Verify URLs work:**
  - [ ] `/teacher/mark-attendance/<class_id>/`
  - [ ] `/teacher/camera-stream/<class_id>/`
  - [ ] `/teacher/camera-stream/<class_id>/<camera_id>/`

---

## 📦 VPS Deployment Steps

### Step 1: Upload Code to VPS

```bash
# SSH into your VPS
ssh user@your-vps-ip.com

# Navigate to project directory
cd /path/to/your/project

# Pull latest code (if using Git)
git pull origin main

# OR upload files manually (SCP/SFTP)
# scp -r * user@your-vps-ip.com:/path/to/project/
```

### Step 2: Install Dependencies

```bash
# Activate virtual environment
source /path/to/venv/bin/activate

# Install/update requirements
pip install -r requirements.txt
```

### Step 3: Run Migrations

```bash
# Apply database migrations
python manage.py migrate
```

### Step 4: Collect Static Files

```bash
# Collect all static files (REQUIRED)
python manage.py collectstatic --noinput

# Verify staticfiles directory was created
ls -la staticfiles/
```

### Step 5: Check File Permissions

```bash
# Ensure web server can read/write files
sudo chown -R www-data:www-data /path/to/project
sudo chmod -R 755 /path/to/project/staticfiles
sudo chmod -R 755 /path/to/project/media
```

### Step 6: Restart Web Server

```bash
# For Gunicorn/Systemd
sudo systemctl restart your_app_name
sudo systemctl status your_app_name

# OR for uWSGI
sudo systemctl restart uwsgi

# OR for Apache
sudo systemctl restart apache2
```

### Step 7: Clear Browser Cache

```bash
# On your browser, press Ctrl+Shift+Delete
# Or use Incognito/Private mode for testing
```

---

## 🔍 Post-Deployment Verification

### Test 1: Access Home Page
- [ ] Open browser: `http://your-vps-ip.com` or `https://your-domain.com`
- [ ] Verify page loads without errors
- [ ] Check static files (CSS/JS) are loading

### Test 2: Login as Teacher
- [ ] Login with teacher credentials
- [ ] Verify dashboard loads correctly

### Test 3: Navigate to Mark Attendance
- [ ] Click "Mark Attendance" on an assigned class
- [ ] Verify both buttons appear:
  - "Launch Live Recognition (Desktop)"
  - "Launch Web-Based Camera Stream"

### Test 4: Test Web-Based Camera Stream
- [ ] Click "Launch Web-Based Camera Stream"
- [ ] Verify camera feed appears in browser
- [ ] Check face recognition is working
- [ ] Verify student names appear when recognized
- [ ] Check attendance is being marked

### Test 5: Multi-Camera Support (if applicable)
- [ ] If multiple cameras assigned, verify grid layout
- [ ] Check all camera feeds are streaming
- [ ] Verify labels show correct camera names/locations

### Test 6: Check Logs
```bash
# View Django/Gunicorn logs
sudo journalctl -u your_service_name -f

# Check for any errors
tail -f /var/log/nginx/error.log  # If using NGINX
```

---

## ⚠️ Troubleshooting Common Issues

### Issue 1: "Static files not found" or 404 errors

**Solution:**
```bash
# Re-run collectstatic
python manage.py collectstatic --noinput

# Check STATIC_ROOT in settings.py
# Should be: STATIC_ROOT = BASE_DIR / 'staticfiles'

# Verify web server config serves /static/ from STATIC_ROOT
```

### Issue 2: "ModuleNotFoundError: No module named 'app1.web_camera_stream'"

**Solution:**
```bash
# Verify file exists
ls -la app1/web_camera_stream.py

# Check file permissions
chmod 644 app1/web_camera_stream.py

# Restart server
sudo systemctl restart your_app
```

### Issue 3: Camera stream shows "Loading..." forever

**Solutions:**
1. **Check camera accessibility:**
   ```bash
   # Test RTSP stream with VLC or ffplay
   ffplay rtsp://camera-ip/stream
   ```

2. **Verify firewall rules:**
   ```bash
   # Allow outbound connections to camera
   sudo ufw allow out to any port 554  # RTSP
   ```

3. **Check Django logs:**
   ```bash
   sudo journalctl -u your_service -f | grep -i camera
   ```

### Issue 4: "No cameras assigned" error

**Solution:**
1. Login to Django Admin (`/admin`)
2. Go to "Camera Configurations"
3. Add/edit camera:
   - Name: e.g., "Classroom 101"
   - Camera Source: `0` (webcam) or RTSP URL
   - Threshold: `0.6`
   - Location: e.g., "Gate 1"
4. Go to "Assigned Classes"
5. Edit your class and assign the camera

### Issue 5: Face recognition not working

**Check:**
```bash
# Open Django shell
python manage.py shell

# Test student data
from app1.models import Student
students = Student.objects.filter(authorized=True)
print(f"Authorized students: {students.count()}")

# Check face embeddings
for student in students:
    if student.face_embedding:
        print(f"{student.name}: Has embedding ✓")
    else:
        print(f"{student.name}: NO embedding ✗")
```

---

## 🔐 Security Checklist

- [ ] **Set DEBUG = False in settings.py**
  ```python
  DEBUG = False
  ```

- [ ] **Update ALLOWED_HOSTS**
  ```python
  ALLOWED_HOSTS = ['your-domain.com', 'your-vps-ip.com']
  ```

- [ ] **Use HTTPS (SSL Certificate)**
  ```bash
  # Install Let's Encrypt
  sudo certbot --nginx -d your-domain.com
  
  # Auto-renewal
  sudo certbot renew --dry-run
  ```

- [ ] **Secure Django Admin**
  - Change default admin URL
  - Use strong passwords
  - Enable 2FA if possible

- [ ] **Database Backup**
  ```bash
  # Backup SQLite database
  cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d)
  
  # Or setup automated backups
  ```

- [ ] **Firewall Configuration**
  ```bash
  # Allow only necessary ports
  sudo ufw allow 22/tcp    # SSH
  sudo ufw allow 80/tcp    # HTTP
  sudo ufw allow 443/tcp   # HTTPS
  sudo ufw enable
  ```

---

## 📊 Performance Monitoring

### Monitor Server Resources

```bash
# CPU and Memory usage
htop

# Disk space
df -h

# Network connections
netstat -tulpn

# Process list
ps aux | grep gunicorn
```

### Monitor Application

```bash
# View real-time logs
sudo journalctl -u your_service -f

# Check active connections
watch -n 1 'netstat -an | grep ESTABLISHED | wc -l'

# Monitor response times (in logs)
tail -f /var/log/nginx/access.log
```

### Optimize if Needed

- **If CPU is high:**
  - Reduce camera resolution
  - Lower frame rate in `web_camera_stream.py`
  - Use hardware acceleration (GPU)

- **If Memory is high:**
  - Reduce number of simultaneous streams
  - Optimize image quality settings
  - Increase VPS RAM

- **If Network is slow:**
  - Use lower bitrate for streams
  - Implement adaptive streaming
  - Use CDN for static files

---

## 🎯 Success Criteria

Your deployment is successful when:

✅ Homepage loads over HTTP/HTTPS  
✅ Can login as teacher  
✅ See both camera launch buttons  
✅ Web-based stream works in browser  
✅ Face recognition detects students  
✅ Attendance is marked automatically  
✅ Multi-camera grid works (if applicable)  
✅ No errors in logs  
✅ Static files load correctly  
✅ Stream auto-reconnects if dropped  

---

## 📞 Quick Reference Commands

```bash
# Restart application
sudo systemctl restart your_app

# Check status
sudo systemctl status your_app

# View logs
sudo journalctl -u your_app -f

# Reload Nginx (if using)
sudo systemctl reload nginx

# Test configuration
sudo nginx -t

# Python shell
python manage.py shell

# Create admin user
python manage.py createsuperuser

# Backup database
cp db.sqlite3 backup_$(date +%Y%m%d).sqlite3
```

---

## 📝 Next Steps After Deployment

1. **Monitor for 24 hours** - Watch for any issues
2. **Test with real students** - Verify face recognition accuracy
3. **Train teachers** - Show them how to use web-based streaming
4. **Document issues** - Keep a log of any problems/solutions
5. **Setup monitoring** - Use tools like Uptime Robot, New Relic, etc.
6. **Plan scaling** - If adding more cameras/classes

---

**Deployment Date:** _________________  
**Deployed By:** _________________  
**VPS IP/Domain:** _________________  
**Notes:** _________________

---

**Version:** 1.0  
**Last Updated:** 2026-03-13  
**Status:** ✅ Ready for Production Deployment
