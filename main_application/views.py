from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Q, Sum
from django.utils import timezone
from datetime import timedelta
from .models import (
    User, Candidate, ExamResult, AggregateResult, School, 
    AcademicYear, Subject, ResultAccessPayment, FraudAttemptLog,
    UserActivityLog, SchoolPerformanceReport, EducationLevel
)
import json


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_activity(request, user, action, description):
    """Log user activity"""
    UserActivityLog.objects.create(
        user=user,
        action=action,
        description=description,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
    )


def login_view(request):
    """
    Unified login view for all user types
    Redirects to appropriate dashboard based on user role
    """
    # Redirect if already logged in
    if request.user.is_authenticated:
        return redirect_to_dashboard(request.user)
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember_me', False)
        
        # Authenticate user
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            # Check if account is active
            if not user.is_active:
                messages.error(request, 'Your account has been deactivated. Please contact support.')
                return render(request, 'main_application/login.html')
            
            # Check if account has expired (for marks entry clerks)
            if user.is_account_expired:
                messages.error(request, 'Your account has expired. Please contact KNEC staff for renewal.')
                return render(request, 'main_application/login.html')
            
            # Check account expiry
            if user.account_expires_at and timezone.now() > user.account_expires_at:
                user.is_account_expired = True
                user.is_active = False
                user.save()
                messages.error(request, 'Your account has expired. Please contact KNEC staff for renewal.')
                return render(request, 'main_application/login.html')
            
            # Login user
            login(request, user)
            
            # Set session expiry
            if not remember_me:
                request.session.set_expiry(0)  # Session expires when browser closes
            else:
                request.session.set_expiry(1209600)  # 2 weeks
            
            # Update last login IP
            user.last_login_ip = get_client_ip(request)
            user.save(update_fields=['last_login_ip'])
            
            # Log activity
            log_activity(request, user, 'LOGIN', f'User {user.email} logged in successfully')
            
            # Success message
            messages.success(request, f'Welcome back, {user.get_full_name()}!')
            
            # Redirect to appropriate dashboard
            return redirect_to_dashboard(user)
        else:
            # Log failed attempt
            ip_address = get_client_ip(request)
            FraudAttemptLog.objects.create(
                attempt_type='UNAUTHORIZED_ACCESS',
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                description=f'Failed login attempt for email: {email}'
            )
            messages.error(request, 'Invalid email or password. Please try again.')
    
    return render(request, 'auth/login.html')


def redirect_to_dashboard(user):
    """Redirect user to appropriate dashboard based on role"""
    dashboard_mapping = {
        'ADMIN': 'admin_dashboard',
        'KNEC_STAFF': 'knec_dashboard',
        'MARKS_ENTRY': 'marks_entry_dashboard',
        'SCHOOL_ADMIN': 'school_admin_dashboard',
        'SCHOOL_STAFF': 'school_staff_dashboard',
    }
    
    dashboard_url = dashboard_mapping.get(user.user_type, 'admin_dashboard')
    return redirect(dashboard_url)


@login_required
def logout_view(request):
    """Logout view"""
    user = request.user
    log_activity(request, user, 'LOGOUT', f'User {user.email} logged out')
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@login_required
def admin_dashboard(request):
    """
    Admin Dashboard with comprehensive statistics and graphs
    """
    # Check if user is admin
    if not request.user.is_admin:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect_to_dashboard(request.user)
    
    # Get active academic year
    active_year = AcademicYear.objects.filter(is_active=True).first()
    
    # Get date ranges
    today = timezone.now()
    last_30_days = today - timedelta(days=30)
    last_7_days = today - timedelta(days=7)
    
    # ===== STATISTICS =====
    
    # User Statistics
    total_users = User.objects.filter(is_active=True).count()
    admin_users = User.objects.filter(user_type='ADMIN', is_active=True).count()
    knec_staff = User.objects.filter(user_type='KNEC_STAFF', is_active=True).count()
    marks_entry_clerks = User.objects.filter(user_type='MARKS_ENTRY', is_active=True).count()
    school_users = User.objects.filter(
        user_type__in=['SCHOOL_ADMIN', 'SCHOOL_STAFF'], 
        is_active=True
    ).count()
    
    # School Statistics
    total_schools = School.objects.filter(is_active=True).count()
    primary_schools = School.objects.filter(
        category__name='PRIMARY', 
        is_active=True
    ).count()
    secondary_schools = School.objects.filter(
        category__name__in=['JSS', 'SENIOR'], 
        is_active=True
    ).count()
    
    # Candidate Statistics
    total_candidates = Candidate.objects.filter(is_active=True).count()
    if active_year:
        current_year_candidates = Candidate.objects.filter(
            academic_year=active_year,
            is_active=True
        ).count()
    else:
        current_year_candidates = 0
    
    # Results Statistics
    total_results = ExamResult.objects.count()
    released_results = AggregateResult.objects.filter(is_released=True).count()
    pending_results = AggregateResult.objects.filter(is_released=False).count()
    
    # Payment Statistics
    total_payments = ResultAccessPayment.objects.filter(status='completed').count()
    total_revenue = ResultAccessPayment.objects.filter(
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    recent_payments = ResultAccessPayment.objects.filter(
        status='completed',
        payment_date__gte=last_30_days
    ).count()
    
    # Fraud Statistics
    total_fraud_attempts = FraudAttemptLog.objects.count()
    unresolved_fraud = FraudAttemptLog.objects.filter(is_resolved=False).count()
    recent_fraud = FraudAttemptLog.objects.filter(
        created_at__gte=last_7_days
    ).count()
    
    # ===== GRAPH DATA =====
    
    # 1. Candidates Registration Trend (Last 6 months)
    six_months_ago = today - timedelta(days=180)
    candidates_by_month = []
    for i in range(6):
        month_start = today - timedelta(days=30 * (5 - i))
        month_end = today - timedelta(days=30 * (4 - i))
        count = Candidate.objects.filter(
            registration_date__gte=month_start,
            registration_date__lt=month_end
        ).count()
        candidates_by_month.append({
            'month': month_start.strftime('%b'),
            'count': count
        })
    
    # 2. Results by Education Level
    results_by_level = []
    for level in EducationLevel.objects.filter(is_active=True):
        count = AggregateResult.objects.filter(
            candidate__education_level=level,
            is_released=True
        ).count()
        results_by_level.append({
            'level': level.get_name_display(),
            'count': count
        })
    
    # 3. Grade Distribution (Overall)
    grade_distribution = AggregateResult.objects.filter(
        is_released=True
    ).values('mean_grade').annotate(
        count=Count('id')
    ).order_by('mean_grade')
    
    grades_data = []
    grade_order = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'D-', 'E']
    for grade in grade_order:
        count = next((item['count'] for item in grade_distribution if item['mean_grade'] == grade), 0)
        grades_data.append({
            'grade': grade,
            'count': count
        })
    
    # 4. School Performance (Top 10 Schools)
    top_schools = []
    if active_year:
        school_reports = SchoolPerformanceReport.objects.filter(
            academic_year=active_year
        ).select_related('school').order_by('-mean_score')[:10]
        
        for report in school_reports:
            top_schools.append({
                'school': report.school.name,
                'mean_score': float(report.mean_score)
            })
    
    # 5. User Activity (Last 7 days)
    activity_by_day = []
    for i in range(7):
        day = today - timedelta(days=6 - i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        count = UserActivityLog.objects.filter(
            timestamp__gte=day_start,
            timestamp__lte=day_end
        ).count()
        
        activity_by_day.append({
            'day': day.strftime('%a'),
            'count': count
        })
    
    # 6. Payment Trends (Last 30 days)
    payment_by_day = []
    for i in range(30, 0, -3):  # Every 3 days
        day = today - timedelta(days=i)
        day_end = today - timedelta(days=i - 3)
        
        amount = ResultAccessPayment.objects.filter(
            status='completed',
            payment_date__gte=day,
            payment_date__lt=day_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        payment_by_day.append({
            'date': day.strftime('%d %b'),
            'amount': float(amount)
        })
    
    # 7. User Distribution by Type
    user_type_distribution = [
        {'type': 'Admin', 'count': admin_users},
        {'type': 'KNEC Staff', 'count': knec_staff},
        {'type': 'Marks Entry', 'count': marks_entry_clerks},
        {'type': 'School Users', 'count': school_users},
    ]
    
    # 8. Recent Activities
    recent_activities = UserActivityLog.objects.select_related('user').order_by('-timestamp')[:10]
    
    # 9. Recent Registrations
    recent_candidates = Candidate.objects.select_related(
        'school', 'education_level', 'academic_year'
    ).order_by('-registration_date')[:10]
    
    # 10. Pending Tasks
    pending_tasks = {
        'unverified_certificates': Candidate.objects.filter(
            is_birth_cert_verified=False,
            birth_certificate__isnull=False
        ).count(),
        'pending_results': pending_results,
        'unresolved_fraud': unresolved_fraud,
        'expired_accounts': User.objects.filter(
            is_account_expired=True,
            is_active=False
        ).count(),
    }
    
    context = {
        # Statistics
        'total_users': total_users,
        'total_schools': total_schools,
        'total_candidates': total_candidates,
        'current_year_candidates': current_year_candidates,
        'total_results': total_results,
        'released_results': released_results,
        'pending_results': pending_results,
        'total_payments': total_payments,
        'total_revenue': total_revenue,
        'recent_payments': recent_payments,
        'total_fraud_attempts': total_fraud_attempts,
        'unresolved_fraud': unresolved_fraud,
        'recent_fraud': recent_fraud,
        
        # Breakdown
        'admin_users': admin_users,
        'knec_staff': knec_staff,
        'marks_entry_clerks': marks_entry_clerks,
        'school_users': school_users,
        'primary_schools': primary_schools,
        'secondary_schools': secondary_schools,
        
        # Graph Data (JSON)
        'candidates_by_month_json': json.dumps(candidates_by_month),
        'results_by_level_json': json.dumps(results_by_level),
        'grades_data_json': json.dumps(grades_data),
        'top_schools_json': json.dumps(top_schools),
        'activity_by_day_json': json.dumps(activity_by_day),
        'payment_by_day_json': json.dumps(payment_by_day),
        'user_type_distribution_json': json.dumps(user_type_distribution),
        
        # Lists
        'recent_activities': recent_activities,
        'recent_candidates': recent_candidates,
        'pending_tasks': pending_tasks,
        
        # Other
        'active_year': active_year,
    }
    
    return render(request, 'dashboards/admin_dashboard.html', context)


# ============================================================
# OTHER DASHBOARDS (Placeholders - Implement as needed)
# ============================================================

@login_required
def knec_dashboard(request):
    """KNEC Staff Dashboard"""
    if not request.user.is_knec_staff:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect_to_dashboard(request.user)
    
    context = {
        'page_title': 'KNEC Staff Dashboard',
    }
    return render(request, 'dashboards/knec_dashboard.html', context)


@login_required
def marks_entry_dashboard(request):
    """Marks Entry Clerk Dashboard"""
    if not request.user.is_marks_entry:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect_to_dashboard(request.user)
    
    context = {
        'page_title': 'Marks Entry Dashboard',
    }
    return render(request, 'dashboards/marks_entry_dashboard.html', context)


@login_required
def school_admin_dashboard(request):
    """School Administrator Dashboard"""
    if not request.user.is_school_user:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect_to_dashboard(request.user)
    
    context = {
        'page_title': 'School Administrator Dashboard',
    }
    return render(request, 'dashboards/school_admin_dashboard.html', context)


@login_required
def school_staff_dashboard(request):
    """School Staff Dashboard"""
    if not request.user.is_school_user:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect_to_dashboard(request.user)
    
    context = {
        'page_title': 'School Staff Dashboard',
    }
    return render(request, 'dashboards/school_staff_dashboard.html', context)