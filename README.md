# KNEC Exam Management System

A comprehensive Django-based examination management system for Kenya National Examinations Council (KNEC), supporting KEPSEA Grade 6, KCPE, and KCSE examinations.

## 👤 Developer Information

**Developer:** Steve Ongera  
**Contact:** 0112284093  
**Email:** steveongera001@gmail.com  
**GitHub:** steve-ongera

---

## 📋 Table of Contents

- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [User Roles](#user-roles)
- [Key Features](#key-features)
- [Models Overview](#models-overview)
- [Admin Interface](#admin-interface)
- [Security Features](#security-features)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

---

## 🚀 Features

### Core Functionality
- **Multi-level Exam Support**: KEPSEA Grade 6 (CBC), KCPE Class 8 (8-4-4), and KCSE Form 4
- **Role-Based Access Control**: Admin, KNEC Staff, Marks Entry Clerks, School Administrators
- **Birth Certificate Verification**: Fraud prevention through government registry integration
- **Automated Grading**: Flexible grading schemes per academic year and subject
- **Result Release Management**: Controlled result release with M-Pesa payment integration
- **School Performance Analytics**: Comprehensive reporting and rankings
- **Audit Trail**: Complete activity logging for compliance

### Security Features
- Email-based authentication
- Temporary account expiry for marks entry clerks
- Fraud attempt detection and logging
- Birth certificate validation (one certificate per exam level)
- IP tracking and user agent logging
- Session management

---

## 💻 System Requirements

### Prerequisites
- Python 3.8+
- Django 4.2+
- PostgreSQL 12+ (recommended) or SQLite for development
- Redis (for caching and session management)
- M-Pesa Daraja API credentials (for payment processing)

### Python Packages
```txt
Django>=4.2.0
psycopg2-binary>=2.9.0
Pillow>=10.0.0
django-environ>=0.10.0
celery>=5.3.0
redis>=4.5.0
requests>=2.31.0
```

---

## 📦 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/knec-exam-system.git
cd knec-exam-system
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the project root:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=knec_exam_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password
EMAIL_USE_TLS=True

# M-Pesa Configuration
MPESA_ENVIRONMENT=sandbox  # or 'production'
MPESA_CONSUMER_KEY=your_consumer_key
MPESA_CONSUMER_SECRET=your_consumer_secret
MPESA_SHORTCODE=your_shortcode
MPESA_PASSKEY=your_passkey
MPESA_CALLBACK_URL=https://yourdomain.com/api/mpesa/callback/

# Redis
REDIS_URL=redis://localhost:6379/0

# Media and Static Files
MEDIA_URL=/media/
MEDIA_ROOT=media/
STATIC_URL=/static/
STATIC_ROOT=staticfiles/
```

### 5. Database Setup
```bash
# Create database migrations
python manage.py makemigrations main_application

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 6. Load Initial Data (Optional)
```bash
# Load education levels
python manage.py loaddata initial_education_levels.json

# Load school categories
python manage.py loaddata initial_school_categories.json

# Load sample grading schemes
python manage.py loaddata initial_grading_schemes.json
```

### 7. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### 8. Run Development Server
```bash
python manage.py runserver
```

Access the application at `http://localhost:8000/`  
Admin interface: `http://localhost:8000/admin/`

---

## 🔧 Configuration

### System Configuration
Access Django admin → System Configuration to set:
- **Result Access Fee**: Fee for accessing results (KES)
- **Results Release Enabled**: Global toggle for result access
- **Marks Entry Enabled**: Enable/disable marks entry
- **Marks Entry Deadline**: Deadline for entering marks
- **Maintenance Mode**: Put system in maintenance mode

### Academic Year Setup
1. Create an Academic Year (e.g., 2024/2025)
2. Mark it as active
3. Only one academic year can be active at a time

### Grading Schemes
1. Create grading schemes for each education level
2. Define grade ranges (A, B+, B, etc.) with min/max scores
3. Assign point values for aggregate calculation
4. Can be subject-specific or overall

---

## 👥 User Roles

### 1. System Administrator (ADMIN)
- Full system access
- User management
- System configuration
- Grading scheme management
- Result release control

### 2. KNEC Staff (KNEC_STAFF)
- School registration
- Candidate verification
- Marks entry permission management
- Report generation
- Result release management

### 3. Marks Entry Clerk (MARKS_ENTRY)
- Temporary access
- Enter marks for assigned subjects/schools
- Time-limited permissions
- Account auto-expires after deadline

### 4. School Administrator (SCHOOL_ADMIN)
- Candidate registration
- View school performance
- Manage school staff
- Access school reports

### 5. School Staff (SCHOOL_STAFF)
- View candidates
- Basic reporting
- Limited access to school data

---

## ✨ Key Features

### 1. Candidate Registration
```python
# Automatic index number generation
# Format: SCHOOLCODE-YEAR-SEQUENCE
# Example: SC001-2024-0001

# Birth certificate verification required for minors
# One certificate can only be used once per exam level
```

### 2. Marks Entry
- Bulk marks entry interface
- Real-time grade calculation
- Subject-specific permissions
- Audit trail for all entries
- Validation against grading schemes

### 3. Result Processing
```python
# Automatic aggregate calculation
# Position ranking (school, county, national)
# Mean grade computation
# Grade distribution analysis
```

### 4. Payment Integration
- M-Pesa STK Push for result access
- Payment verification
- Receipt generation
- Refund handling for failed transactions

### 5. Reporting & Analytics
- School performance reports
- Grade distribution analysis
- County and national rankings
- Performance trends over years
- Export to PDF/Excel

---

## 📊 Models Overview

### User Management
- **User**: Custom user model with role-based access
- **UserActivityLog**: Complete audit trail
- **MarksEntryPermission**: Temporary permissions for clerks

### Academic Structure
- **AcademicYear**: 2024/2025 format
- **EducationLevel**: KEPSEA, KCPE, KCSE
- **Subject**: Subject definitions per level
- **GradingScheme**: Flexible grading per year
- **GradeRange**: Grade boundaries and points

### Schools
- **SchoolCategory**: Primary, JSS, Senior Secondary
- **School**: School registration
- **SchoolAdministrator**: User-school relationships

### Candidates & Results
- **BirthCertificateRegistry**: Government database simulation
- **Candidate**: Student registration
- **ExamResult**: Individual subject results
- **AggregateResult**: Overall performance

### Financial
- **ResultAccessPayment**: M-Pesa payment tracking

### Security
- **FraudAttemptLog**: Fraud detection logging
- **SystemConfiguration**: Global settings

### Communications
- **Notification**: User notifications
- **SystemAnnouncement**: System-wide announcements

---

## 🎛️ Admin Interface

### Dashboard Features
- Quick statistics overview
- Recent activity feed
- Pending approvals
- System health indicators

### Custom Admin Actions
- Bulk result release
- Account expiry extension
- Report regeneration
- Fraud alert investigation
- Payment reconciliation

### Filters & Search
- Advanced filtering on all models
- Full-text search capabilities
- Date range filters
- Status-based filtering

---

## 🔒 Security Features

### Authentication
- Email-based login
- Password complexity requirements
- Session timeout
- IP tracking

### Authorization
- Role-based permissions
- Resource-level access control
- Time-bound permissions
- Action logging

### Data Protection
- Birth certificate validation
- Duplicate prevention
- Fraud detection
- Encrypted sensitive data

### Audit Trail
- All user actions logged
- IP and user agent tracking
- Change history
- Fraud attempt logging

---

## 🔌 API Endpoints

### Authentication
```
POST /api/auth/login/
POST /api/auth/logout/
POST /api/auth/refresh/
```

### Candidates
```
GET    /api/candidates/
POST   /api/candidates/
GET    /api/candidates/{id}/
PUT    /api/candidates/{id}/
DELETE /api/candidates/{id}/
```

### Results
```
GET  /api/results/
POST /api/results/
GET  /api/results/{candidate_id}/
POST /api/results/bulk-entry/
```

### Payments
```
POST /api/payments/initiate/
GET  /api/payments/{transaction_id}/
POST /api/payments/callback/
```

### Reports
```
GET /api/reports/school/{school_id}/
GET /api/reports/county/{county}/
GET /api/reports/national/
GET /api/reports/export/{format}/
```

---

## 🧪 Testing

### Run Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test main_application

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Test Categories
- Unit tests for models
- Integration tests for views
- API endpoint tests
- Security tests
- Performance tests

---

## 🚀 Deployment

### Production Setup

#### 1. Update Settings
```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

#### 2. Use Production Database
```bash
# PostgreSQL recommended
pip install psycopg2-binary
```

#### 3. Configure Web Server
**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location /static/ {
        alias /path/to/staticfiles/;
    }
    
    location /media/ {
        alias /path/to/media/;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Gunicorn:**
```bash
gunicorn knec_exam_system.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

#### 4. Set Up Celery for Background Tasks
```bash
celery -A knec_exam_system worker -l info
celery -A knec_exam_system beat -l info
```

#### 5. Configure Backups
```bash
# Database backup
pg_dump knec_exam_db > backup_$(date +%Y%m%d).sql

# Media files backup
tar -czf media_backup_$(date +%Y%m%d).tar.gz media/
```

---

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Code Standards
- Follow PEP 8 style guide
- Write meaningful commit messages
- Add tests for new features
- Update documentation
- Comment complex logic

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 Support

For support, please contact:

**Steve Ongera**  
📧 Email: steveongera001@gmail.com  
📱 Phone: 0112284093

---

## 🙏 Acknowledgments

- Kenya National Examinations Council (KNEC)
- Django Framework
- M-Pesa Daraja API
- All contributors and testers

---

## 📅 Version History

### Version 1.0.0 (Current)
- Initial release
- Core functionality implemented
- Admin interface complete
- M-Pesa integration
- Security features implemented

### Upcoming Features
- SMS notifications
- Mobile app integration
- Advanced analytics dashboard
- Multi-language support
- Offline marks entry capability

---

## 🔧 Troubleshooting

### Common Issues

#### Database Connection Error
```bash
# Check PostgreSQL service
sudo systemctl status postgresql

# Verify credentials in .env file
```

#### Media Files Not Loading
```bash
# Ensure MEDIA_ROOT is correctly set
# Check file permissions
chmod -R 755 media/
```

#### M-Pesa Callback Not Working
```bash
# Verify callback URL is publicly accessible
# Check MPESA_CALLBACK_URL in .env
# Review M-Pesa API logs
```

---

**Built with ❤️ by Steve Ongera**