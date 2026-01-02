# BIWC Membership System - DEPLOYMENT GUIDE

## Quick Start

### Running Locally

1. **Install Python 3.7+** from python.org
2. **Navigate to project directory**:
   ```
   cd c:\Users\Enoch\OneDrive\Desktop\membership
   ```

3. **Create virtual environment** (if needed):
   ```
   python -m venv .venv
   ```

4. **Activate virtual environment**:
   ```
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

5. **Install dependencies**:
   ```
   pip install -r requirements.txt
   ```

6. **Run the application**:
   ```
   python app.py
   ```

7. **Open in browser**:
   - Go to: http://localhost:5000
   - Home page displays with member statistics
   - Register new members via /register
   - View members directory via /members

---

## Deployment Checklist

### Before Production Deployment

- [ ] Change `app.secret_key` to a random secure key
- [ ] Set `app.debug = False` in production
- [ ] Use environment variables for sensitive data
- [ ] Set up database backups
- [ ] Configure logging
- [ ] Enable HTTPS/SSL
- [ ] Set up error monitoring
- [ ] Test all forms thoroughly
- [ ] Verify email delivery (if adding email features)
- [ ] Load test with expected member count

---

## Deployment Options

### Option 1: Local/Church Network Deployment

**Best for**: Small churches, internal use

**Steps**:
1. Install Python on church computer
2. Run `python app.py`
3. Share URL on local network: `http://[your-ip]:5000`
4. Members access from church computers/mobile

**Pros**:
- Free
- Full control
- Offline capable

**Cons**:
- Computer must stay on
- Only local access
- Limited scalability

---

### Option 2: Heroku Deployment

**Best for**: Cloud hosting, global access, free tier available

**Prerequisites**:
- Heroku account (free)
- Git installed

**Steps**:

1. **Create Procfile** (in project root):
   ```
   web: gunicorn -w 4 -b 0.0.0.0:$PORT wsgi:app
   ```

2. **Create runtime.txt**:
   ```
   python-3.11.0
   ```

3. **Initialize Git** (if not already):
   ```
   git init
   git add .
   git commit -m "Initial commit"
   ```

4. **Install Heroku CLI** and login:
   ```
   heroku login
   heroku create your-biwc-membership
   ```

5. **Deploy**:
   ```
   git push heroku main
   ```

6. **Access**:
   - https://your-biwc-membership.herokuapp.com

---

### Option 3: PythonAnywhere Deployment

**Best for**: Beginner-friendly, reliable, paid hosting

**Steps**:

1. Create account at pythonanywhere.com
2. Upload files via web interface
3. Configure web app settings
4. Set Python version to 3.11
5. Configure WSGI file
6. Access your domain

---

### Option 4: AWS EC2 Deployment

**Best for**: Enterprise, maximum control, scalability

**Requirements**:
- AWS account
- EC2 instance (Ubuntu/Amazon Linux)
- Domain name (optional)

**Steps**:

1. **Launch EC2 Instance**:
   - Ubuntu 20.04 LTS
   - t2.micro (free tier)
   - Configure security groups

2. **Connect via SSH**:
   ```
   ssh -i your-key.pem ubuntu@your-instance-ip
   ```

3. **Install dependencies**:
   ```
   sudo apt update
   sudo apt install python3-pip python3-venv nginx
   ```

4. **Clone/upload project**:
   ```
   git clone <your-repo>
   cd membership
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Configure Nginx** as reverse proxy
6. **Run with Gunicorn**:
   ```
   gunicorn -w 4 -b 127.0.0.1:5000 wsgi:app
   ```

7. **Use systemd for auto-restart**

---

### Option 5: DigitalOcean Deployment

**Best for**: Affordable, easy to use, good documentation

**Similar to AWS**, but simpler:

1. Create Droplet (Ubuntu 20.04)
2. SSH into server
3. Install Python, Nginx, PostgreSQL (optional)
4. Deploy application
5. Configure domain

Cost: ~$5-10/month for basic droplet

---

## Database Configuration

### SQLite (Current - Good for small churches)

```python
DATABASE = 'church_members.db'
```

**Upgrade to PostgreSQL for larger databases**:

1. Install PostgreSQL
2. Create database:
   ```sql
   CREATE DATABASE biwc_members;
   CREATE USER biwc WITH PASSWORD 'secure-password';
   ALTER ROLE biwc SET client_encoding TO 'utf8';
   ALTER ROLE biwc SET default_transaction_isolation TO 'read committed';
   ALTER ROLE biwc SET default_transaction_deferrable TO on;
   GRANT ALL PRIVILEGES ON DATABASE biwc_members TO biwc;
   ```

3. Install Python driver:
   ```
   pip install psycopg2-binary
   ```

4. Update connection string:
   ```python
   import os
   DATABASE_URL = os.environ.get('DATABASE_URL')
   # Connection logic
   ```

---

## Security Best Practices

### 1. Environment Variables

Create `.env` file (NOT committed to git):
```
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost/dbname
DEBUG=False
FLASK_ENV=production
```

Load in app.py:
```python
import os
from dotenv import load_dotenv

load_dotenv()
app.secret_key = os.getenv('SECRET_KEY')
```

### 2. HTTPS/SSL

For production, use SSL certificate:

**Free option - Let's Encrypt**:
```
certbot certonly --standalone -d yourdomain.com
```

Configure Nginx/Apache to use certificate

### 3. Password Hashing

When adding user authentication:
```python
from werkzeug.security import generate_password_hash, check_password_hash

# Create password
hashed = generate_password_hash('password123')

# Check password
if check_password_hash(hashed, 'password123'):
    print("Password correct!")
```

### 4. Input Validation

Already implemented but ensure:
- Email format validation ✅
- Phone number format ✅
- Required fields check ✅
- SQL injection prevention (using ? parameters) ✅
- XSS prevention (Jinja2 escapes by default) ✅

### 5. Backup Strategy

**Daily backups**:
```bash
# Create backup script
#!/bin/bash
cp church_members.db church_members.db.backup_$(date +%Y%m%d_%H%M%S)
```

Schedule with cron (Linux/Mac):
```
0 2 * * * /home/user/backup.sh  # Daily at 2 AM
```

---

## Monitoring & Logging

### Application Logging

```python
import logging

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@app.route('/register', methods=['POST'])
def register():
    logging.info(f'New registration: {email}')
    # ...
```

### Monitor Key Metrics

- Member registrations per day
- Page load times
- Database query performance
- Server resource usage
- Error rates

---

## Scaling for Growth

### Stage 1: 0-100 Members
- Current setup (SQLite)
- Local deployment or small VPS
- Cost: Free-$5/month

### Stage 2: 100-500 Members
- PostgreSQL database
- Standard hosting (PythonAnywhere/DigitalOcean)
- Cost: $5-15/month

### Stage 3: 500+ Members
- Database optimization
- Caching layer (Redis)
- Multiple servers
- CDN for static files
- Cost: $20-50+/month

---

## Feature Additions

### 1. Email Notifications

```python
from flask_mail import Mail, Message

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'
app.config['MAIL_PASSWORD'] = 'app-specific-password'

mail = Mail(app)

@app.route('/register', methods=['POST'])
def register():
    # ... registration code ...
    msg = Message('Welcome to BIWC!', 
                  recipients=[email])
    msg.body = f'Welcome {first_name}!'
    mail.send(msg)
```

### 2. Member Login

```python
from flask_login import LoginManager, UserMixin

login_manager = LoginManager()
login_manager.init_app(app)

class Member(UserMixin):
    def __init__(self, id):
        self.id = id

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Login logic
    pass
```

### 3. Admin Dashboard

```python
@app.route('/admin')
@login_required
def admin_dashboard():
    stats = get_member_stats()
    recent = get_recent_members(10)
    return render_template('admin_dashboard.html', 
                          stats=stats, recent=recent)
```

### 4. Export to CSV

```python
import csv
from io import StringIO
from flask import send_file

@app.route('/export-csv')
def export_csv():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM members')
    
    output = StringIO()
    writer = csv.writer(output)
    # Write data...
    
    return send_file(output, 
                    mimetype='text/csv',
                    as_attachment=True)
```

---

## Troubleshooting

### Issue: Database Locked
**Solution**:
```python
import time
time.sleep(1)  # Retry connection
```

### Issue: 404 on CSS/JS
**Check**:
- Static files exist in `/static/` folder
- URL in template: `{{ url_for('static', filename='style.css') }}`

### Issue: Form not submitting
**Debug**:
- Check form `name` attributes
- Verify POST method
- Check console for JavaScript errors

### Issue: Slow page load
**Optimize**:
- Add database indexes
- Cache static files
- Minimize CSS/JS
- Use CDN for large files

---

## Support Resources

- **Flask Documentation**: https://flask.palletsprojects.com/
- **Python SQLite**: https://docs.python.org/3/library/sqlite3.html
- **Bootstrap CSS**: https://getbootstrap.com/docs/
- **Font Awesome**: https://fontawesome.com/docs

---

## Maintenance Schedule

### Daily
- Monitor error logs
- Check server uptime
- Verify database backup

### Weekly
- Review member registrations
- Check for database errors
- Update logs

### Monthly
- Full database backup
- Review security logs
- Update Python packages
- Performance analysis

### Quarterly
- Security audit
- Performance optimization
- Feature planning

---

## Contact & Support

**For questions about deployment**:
- Phone: +233 547 265 306
- Email: members@biwckwabenya.org
- Location: Kwabenya, Accra, Ghana

---

**Last Updated**: January 2, 2025
**Version**: 1.0.0

May God bless your ministry! 🙏⛪
