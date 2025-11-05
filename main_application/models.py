from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
from datetime import timedelta
import uuid


class CustomUserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_type', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom User Model with role-based access"""
    USER_TYPE_CHOICES = [
        ('ADMIN', 'System Administrator'),
        ('KNEC_STAFF', 'KNEC Staff'),
        ('MARKS_ENTRY', 'Marks Entry Clerk'),
        ('SCHOOL_ADMIN', 'School Administrator'),
        ('SCHOOL_STAFF', 'School Staff'),
    ]

    username = None  # Remove username field
    email = models.EmailField(unique=True, verbose_name='Email Address')
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    
    # Additional fields
    phone_number = models.CharField(max_length=15, blank=True)
    id_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    
    # Account expiry for temporary users (marks entry clerks)
    account_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Account will be disabled after this date"
    )
    is_account_expired = models.BooleanField(default=False)
    
    # Profile
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'user_type']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"

    def save(self, *args, **kwargs):
        # Check if account has expired
        if self.account_expires_at and timezone.now() > self.account_expires_at:
            self.is_account_expired = True
            self.is_active = False
        super().save(*args, **kwargs)

    def extend_account_expiry(self, days=30):
        """Extend account expiry by specified days"""
        if self.account_expires_at:
            self.account_expires_at += timedelta(days=days)
        else:
            self.account_expires_at = timezone.now() + timedelta(days=days)
        self.is_account_expired = False
        self.is_active = True
        self.save()

    @property
    def is_admin(self):
        return self.user_type == 'ADMIN'

    @property
    def is_knec_staff(self):
        return self.user_type == 'KNEC_STAFF'

    @property
    def is_marks_entry(self):
        return self.user_type == 'MARKS_ENTRY'

    @property
    def is_school_user(self):
        return self.user_type in ['SCHOOL_ADMIN', 'SCHOOL_STAFF']


class UserActivityLog(models.Model):
    """Track user activities for audit purposes"""
    ACTION_CHOICES = [
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('CREATE', 'Create Record'),
        ('UPDATE', 'Update Record'),
        ('DELETE', 'Delete Record'),
        ('VIEW', 'View Record'),
        ('EXPORT', 'Export Data'),
        ('MARKS_ENTRY', 'Marks Entry'),
        ('RESULT_RELEASE', 'Result Release'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activity_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Optional: Link to specific records
    content_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'User Activity Log'
        verbose_name_plural = 'User Activity Logs'
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.timestamp}"


class AcademicYear(models.Model):
    """Academic Year e.g., 2024/2025"""
    year = models.CharField(
        max_length=9, 
        unique=True,
        help_text="Format: 2024/2025"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_academic_years'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-year']
        verbose_name = "Academic Year"
        verbose_name_plural = "Academic Years"

    def __str__(self):
        return self.year

    def save(self, *args, **kwargs):
        # Ensure only one active academic year
        if self.is_active:
            AcademicYear.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class EducationLevel(models.Model):
    """Education Levels: KEPSEA Grade 6, KCPE, KCSE"""
    LEVEL_CHOICES = [
        ('KEPSEA', 'KEPSEA Grade 6 (CBC)'),
        ('KCPE', 'KCPE Class 8 (8-4-4)'),
        ('KCSE', 'KCSE Form 4'),
    ]
    
    name = models.CharField(max_length=50, choices=LEVEL_CHOICES, unique=True)
    description = models.TextField()
    max_score = models.IntegerField(default=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Education Level"
        verbose_name_plural = "Education Levels"

    def __str__(self):
        return self.get_name_display()


class Subject(models.Model):
    """Subjects for different education levels"""
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    education_level = models.ForeignKey(
        EducationLevel, 
        on_delete=models.CASCADE,
        related_name='subjects'
    )
    is_compulsory = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['education_level', 'code']
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"

    def __str__(self):
        return f"{self.code} - {self.name} ({self.education_level})"


class GradingScheme(models.Model):
    """Grading scheme per subject or overall, can change per academic year"""
    name = models.CharField(max_length=100)
    education_level = models.ForeignKey(
        EducationLevel,
        on_delete=models.CASCADE,
        related_name='grading_schemes'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='grading_schemes'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='grading_schemes',
        help_text="Leave blank for overall grading scheme"
    )
    is_overall = models.BooleanField(
        default=False,
        help_text="Is this for overall/aggregate grading?"
    )
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_grading_schemes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['academic_year', 'education_level', 'subject']
        verbose_name = "Grading Scheme"
        verbose_name_plural = "Grading Schemes"
        unique_together = ['education_level', 'academic_year', 'subject', 'is_overall']

    def __str__(self):
        subject_str = f" - {self.subject}" if self.subject else " (Overall)"
        return f"{self.name} - {self.education_level} {self.academic_year}{subject_str}"


class GradeRange(models.Model):
    """Grade ranges for a grading scheme"""
    grading_scheme = models.ForeignKey(
        GradingScheme,
        on_delete=models.CASCADE,
        related_name='grade_ranges'
    )
    grade = models.CharField(max_length=5, help_text="E.g., A, B+, E, etc.")
    min_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    max_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    points = models.IntegerField(
        null=True,
        blank=True,
        help_text="Grade points for aggregate calculation"
    )
    description = models.CharField(max_length=100, blank=True)
    order = models.IntegerField(default=0, help_text="Display order")

    class Meta:
        ordering = ['grading_scheme', 'order', '-min_score']
        verbose_name = "Grade Range"
        verbose_name_plural = "Grade Ranges"
        unique_together = ['grading_scheme', 'grade']

    def __str__(self):
        return f"{self.grade}: {self.min_score}-{self.max_score} ({self.grading_scheme})"


class SchoolCategory(models.Model):
    """School categories: Primary, JSS, Senior Secondary"""
    CATEGORY_CHOICES = [
        ('PRIMARY', 'Primary School'),
        ('JSS', 'Junior Secondary School'),
        ('SENIOR', 'Senior Secondary / High School'),
        ('MIXED', 'Mixed (Primary & Secondary)'),
    ]
    
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)
    description = models.TextField()
    can_register_for = models.ManyToManyField(
        EducationLevel,
        related_name='school_categories',
        help_text="Which exams can this school category register for?"
    )

    class Meta:
        verbose_name = "School Category"
        verbose_name_plural = "School Categories"

    def __str__(self):
        return self.get_name_display()


class School(models.Model):
    """Registered Schools"""
    code = models.CharField(
        max_length=20,
        unique=True,
        validators=[RegexValidator(r'^[A-Z0-9-]+$', 'Enter a valid school code')]
    )
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        SchoolCategory,
        on_delete=models.PROTECT,
        related_name='schools'
    )
    county = models.CharField(max_length=100)
    sub_county = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    
    # School users/administrators
    administrators = models.ManyToManyField(
        User,
        through='SchoolAdministrator',
        through_fields=('school', 'user')   
    )
    
    is_active = models.BooleanField(default=True)
    registration_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "School"
        verbose_name_plural = "Schools"

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_performance_summary(self, academic_year):
        """Get school performance summary for a given academic year"""
        candidates = self.candidates.filter(academic_year=academic_year)
        total_candidates = candidates.count()
        
        if total_candidates == 0:
            return None
        
        # Get aggregate results
        aggregates = AggregateResult.objects.filter(
            candidate__in=candidates,
            is_released=True
        )
        
        # Calculate statistics
        mean_grades = [agg.mean_grade for agg in aggregates if agg.mean_grade]
        
        return {
            'total_candidates': total_candidates,
            'results_released': aggregates.count(),
            'mean_grades': mean_grades,
            'top_candidate': aggregates.order_by('position_in_school').first(),
        }


class SchoolAdministrator(models.Model):
    """Link users to schools with roles"""
    ROLE_CHOICES = [
        ('PRINCIPAL', 'Principal'),
        ('DEPUTY', 'Deputy Principal'),
        ('ADMIN', 'Administrator'),
        ('TEACHER', 'Teacher'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='school_roles'
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='school_administrators'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    assigned_date = models.DateField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_school_admins'
    )

    class Meta:
        unique_together = ['user', 'school']
        verbose_name = "School Administrator"
        verbose_name_plural = "School Administrators"

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.school.name} ({self.get_role_display()})"


class MarksEntryPermission(models.Model):
    """Temporary permissions for marks entry clerks"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'MARKS_ENTRY'},
        related_name='marks_permissions'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE
    )
    education_level = models.ForeignKey(
        EducationLevel,
        on_delete=models.CASCADE
    )
    subjects = models.ManyToManyField(
        Subject,
        blank=True,
        help_text="Leave blank to allow all subjects"
    )
    schools = models.ManyToManyField(
        School,
        blank=True,
        help_text="Leave blank to allow all schools"
    )
    
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_marks_permissions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Marks Entry Permission"
        verbose_name_plural = "Marks Entry Permissions"
        unique_together = ['user', 'academic_year', 'education_level']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.education_level} ({self.academic_year})"

    def is_valid(self):
        """Check if permission is still valid"""
        now = timezone.now()
        return self.is_active and self.valid_from <= now <= self.valid_until

    def can_enter_marks_for(self, subject, school):
        """Check if user can enter marks for specific subject and school"""
        if not self.is_valid():
            return False
        
        # Check subject permission
        if self.subjects.exists() and subject not in self.subjects.all():
            return False
        
        # Check school permission
        if self.schools.exists() and school not in self.schools.all():
            return False
        
        return True


class BirthCertificateRegistry(models.Model):
    """Birth Certificate Registry (Government Database Simulation)"""
    certificate_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[RegexValidator(r'^[0-9]+$', 'Enter a valid birth certificate number')]
    )
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    place_of_birth = models.CharField(max_length=200)
    parent_guardian_name = models.CharField(max_length=200)
    is_verified = models.BooleanField(default=False)
    is_used_for_exam = models.BooleanField(
        default=False,
        help_text="Has this cert been used to register for an exam?"
    )
    used_exam_level = models.ForeignKey(
        EducationLevel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Which exam was this cert used for?"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Birth Certificate"
        verbose_name_plural = "Birth Certificate Registry"

    def __str__(self):
        full_name = f"{self.first_name} {self.middle_name} {self.last_name}".strip()
        return f"{self.certificate_number} - {full_name}"

    def get_full_name(self):
        return f"{self.first_name} {self.middle_name} {self.last_name}".strip()


class Candidate(models.Model):
    """Student/Candidate Registration"""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    index_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text="Auto-generated unique index number"
    )
    school = models.ForeignKey(
        School,
        on_delete=models.PROTECT,
        related_name='candidates'
    )
    education_level = models.ForeignKey(
        EducationLevel,
        on_delete=models.PROTECT
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name='candidates'
    )
    
    # Personal Information
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    
    # Birth Certificate Validation (Required for under 18)
    birth_certificate = models.ForeignKey(
        BirthCertificateRegistry,
        on_delete=models.PROTECT,
        related_name='candidates',
        null=True,
        blank=True
    )
    is_birth_cert_verified = models.BooleanField(default=False)
    
    # Contact
    phone_number = models.CharField(max_length=15, blank=True)
    parent_guardian_phone = models.CharField(max_length=15)
    
    # Registration tracking
    registered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='registered_candidates'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    registration_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['school', 'index_number']
        verbose_name = "Candidate"
        verbose_name_plural = "Candidates"
        unique_together = ['school', 'academic_year', 'birth_certificate']

    def __str__(self):
        return f"{self.index_number} - {self.get_full_name()}"

    def get_full_name(self):
        return f"{self.first_name} {self.middle_name} {self.last_name}".strip().upper()

    def save(self, *args, **kwargs):
        if not self.index_number:
            # Generate index number: SCHOOLCODE-YEAR-SEQUENCE
            year = self.academic_year.year.split('/')[0]
            last_candidate = Candidate.objects.filter(
                school=self.school,
                academic_year=self.academic_year
            ).order_by('-index_number').first()
            
            if last_candidate and last_candidate.index_number:
                try:
                    last_seq = int(last_candidate.index_number.split('-')[-1])
                    new_seq = last_seq + 1
                except:
                    new_seq = 1
            else:
                new_seq = 1
            
            self.index_number = f"{self.school.code}-{year}-{new_seq:04d}"
        
        super().save(*args, **kwargs)


class ExamResult(models.Model):
    """Individual subject exam results"""
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='exam_results'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT
    )
    raw_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    grade = models.CharField(max_length=5, blank=True)
    points = models.IntegerField(null=True, blank=True)
    remarks = models.CharField(max_length=100, blank=True)
    grading_scheme_used = models.ForeignKey(
        GradingScheme,
        on_delete=models.PROTECT,
        related_name='results'
    )
    
    # Track who entered the marks
    entered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='entered_results'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['candidate', 'subject']
        verbose_name = "Exam Result"
        verbose_name_plural = "Exam Results"
        unique_together = ['candidate', 'subject']

    def __str__(self):
        return f"{self.candidate.index_number} - {self.subject.code}: {self.grade}"

    def calculate_grade(self):
        """Calculate grade based on raw score and grading scheme"""
        grade_ranges = self.grading_scheme_used.grade_ranges.all()
        for grade_range in grade_ranges:
            if grade_range.min_score <= self.raw_score <= grade_range.max_score:
                self.grade = grade_range.grade
                self.points = grade_range.points
                break
        self.save()


class AggregateResult(models.Model):
    """Overall/Aggregate results for a candidate"""
    candidate = models.OneToOneField(
        Candidate,
        on_delete=models.CASCADE,
        related_name='aggregate_result'
    )
    total_points = models.IntegerField(default=0)
    mean_grade = models.CharField(max_length=5, blank=True)
    overall_grade = models.CharField(max_length=5, blank=True)
    position_in_school = models.IntegerField(null=True, blank=True)
    position_in_county = models.IntegerField(null=True, blank=True)
    position_nationally = models.IntegerField(null=True, blank=True)
    grading_scheme_used = models.ForeignKey(
        GradingScheme,
        on_delete=models.PROTECT,
        related_name='aggregate_results'
    )
    is_released = models.BooleanField(default=False)
    release_date = models.DateTimeField(null=True, blank=True)
    released_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='released_results'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Aggregate Result"
        verbose_name_plural = "Aggregate Results"

    def __str__(self):
        return f"{self.candidate.index_number} - {self.mean_grade}"

    def calculate_aggregate(self):
        """Calculate aggregate from individual subject results"""
        results = self.candidate.exam_results.all()
        total_points = sum(result.points or 0 for result in results)
        self.total_points = total_points
        
        # Calculate mean grade based on overall grading scheme
        grade_ranges = self.grading_scheme_used.grade_ranges.all()
        for grade_range in grade_ranges:
            if grade_range.min_score <= total_points <= grade_range.max_score:
                self.mean_grade = grade_range.grade
                break
        
        self.save()


class ResultAccessPayment(models.Model):
    """M-Pesa payments for result access"""
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.PROTECT,
        related_name='result_payments'
    )
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # M-Pesa Details
    mpesa_receipt_number = models.CharField(max_length=50, blank=True)
    merchant_request_id = models.CharField(max_length=100, blank=True)
    checkout_request_id = models.CharField(max_length=100, blank=True)
    
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    result_desc = models.TextField(blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    # Access Tracking
    result_accessed = models.BooleanField(default=False)
    access_date = models.DateTimeField(null=True, blank=True)
    access_ip = models.GenericIPAddressField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Result Access Payment"
        verbose_name_plural = "Result Access Payments"

    def __str__(self):
        return f"{self.transaction_id} - {self.candidate.index_number} - {self.status}"


class FraudAttemptLog(models.Model):
    """Log fraud attempts and suspicious activities"""
    ATTEMPT_TYPE = [
        ('DUPLICATE_BIRTH_CERT', 'Duplicate Birth Certificate Usage'),
        ('MULTIPLE_PAYMENT', 'Multiple Payment Attempts'),
        ('FAKE_INDEX', 'Fake Index Number'),
        ('UNAUTHORIZED_ACCESS', 'Unauthorized Access Attempt'),
        ('MARKS_TAMPERING', 'Marks Tampering Attempt'),
        ('OTHER', 'Other'),
    ]

    attempt_type = models.CharField(max_length=50, choices=ATTEMPT_TYPE)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fraud_attempts'
    )
    index_number = models.CharField(max_length=20, blank=True)
    birth_certificate_number = models.CharField(max_length=20, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    description = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_fraud_attempts'
    )
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Fraud Attempt Log"
        verbose_name_plural = "Fraud Attempt Logs"

    def __str__(self):
        return f"{self.get_attempt_type_display()} - {self.created_at}"


class SchoolPerformanceReport(models.Model):
    """Track school performance over different academic years"""
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='performance_reports'
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE
    )
    education_level = models.ForeignKey(
        EducationLevel,
        on_delete=models.CASCADE
    )
    
    # Statistics
    total_candidates = models.IntegerField(default=0)
    candidates_with_results = models.IntegerField(default=0)
    
    # Grade distribution
    grade_a = models.IntegerField(default=0)
    grade_a_minus = models.IntegerField(default=0)
    grade_b_plus = models.IntegerField(default=0)
    grade_b = models.IntegerField(default=0)
    grade_b_minus = models.IntegerField(default=0)
    grade_c_plus = models.IntegerField(default=0)
    grade_c = models.IntegerField(default=0)
    grade_c_minus = models.IntegerField(default=0)
    grade_d_plus = models.IntegerField(default=0)
    grade_d = models.IntegerField(default=0)
    grade_d_minus = models.IntegerField(default=0)
    grade_e = models.IntegerField(default=0)
    
    # Performance metrics
    mean_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    top_grade = models.CharField(max_length=5, blank=True)
    
    # Rankings
    rank_in_county = models.IntegerField(null=True, blank=True)
    rank_nationally = models.IntegerField(null=True, blank=True)
    
    generated_at = models.DateTimeField(auto_now=True)
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_reports'
    )

    class Meta:
        unique_together = ['school', 'academic_year', 'education_level']
        ordering = ['-academic_year', 'school']
        verbose_name = "School Performance Report"
        verbose_name_plural = "School Performance Reports"

    def __str__(self):
        return f"{self.school.name} - {self.academic_year} - {self.education_level}"

    def generate_report(self):
        """Generate or update performance report"""
        candidates = Candidate.objects.filter(
            school=self.school,
            academic_year=self.academic_year,
            education_level=self.education_level
        )
        
        self.total_candidates = candidates.count()
        
        # Get aggregate results
        aggregates = AggregateResult.objects.filter(
            candidate__in=candidates,
            is_released=True
        )
        
        self.candidates_with_results = aggregates.count()
        
        if self.candidates_with_results > 0:
            # Count grades
            grade_counts = {}
            for agg in aggregates:
                grade = agg.mean_grade
                grade_counts[grade] = grade_counts.get(grade, 0) + 1
            
            # Map to fields
            self.grade_a = grade_counts.get('A', 0)
            self.grade_a_minus = grade_counts.get('A-', 0)
            self.grade_b_plus = grade_counts.get('B+', 0)
            self.grade_b = grade_counts.get('B', 0)
            self.grade_b_minus = grade_counts.get('B-', 0)
            self.grade_c_plus = grade_counts.get('C+', 0)
            self.grade_c = grade_counts.get('C', 0)
            self.grade_c_minus = grade_counts.get('C-', 0)
            self.grade_d_plus = grade_counts.get('D+', 0)
            self.grade_d = grade_counts.get('D', 0)
            self.grade_d_minus = grade_counts.get('D-', 0)
            self.grade_e = grade_counts.get('E', 0)
            
            # Calculate mean score
            total_points = sum(agg.total_points for agg in aggregates)
            self.mean_score = total_points / self.candidates_with_results
            
            # Get top grade
            top_candidate = aggregates.order_by('position_in_school').first()
            if top_candidate:
                self.top_grade = top_candidate.mean_grade
        
        self.save()


class SystemConfiguration(models.Model):
    """System-wide configuration"""
    result_access_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=50.00,
        help_text="Fee for accessing results (KES)"
    )
    results_release_enabled = models.BooleanField(
        default=False,
        help_text="Enable/disable results access globally"
    )
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(blank=True)
    
    # Marks entry settings
    marks_entry_enabled = models.BooleanField(default=True)
    marks_entry_deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Deadline for entering marks"
    )
    
    # Account settings
    marks_entry_default_validity_days = models.IntegerField(
        default=30,
        help_text="Default validity period for marks entry accounts (days)"
    )
    
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='config_updates'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "System Configuration"
        verbose_name_plural = "System Configurations"

    def __str__(self):
        return "System Configuration"

    def save(self, *args, **kwargs):
        # Ensure only one configuration exists
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_config(cls):
        config, created = cls.objects.get_or_create(pk=1)
        return config


class Notification(models.Model):
    """System notifications for users"""
    NOTIFICATION_TYPE = [
        ('INFO', 'Information'),
        ('SUCCESS', 'Success'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('RESULT_RELEASE', 'Result Release'),
        ('ACCOUNT_EXPIRY', 'Account Expiry Warning'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.title}"


class SystemAnnouncement(models.Model):
    """System-wide announcements"""
    ANNOUNCEMENT_TYPE = [
        ('INFO', 'Information'),
        ('ALERT', 'Alert'),
        ('MAINTENANCE', 'Maintenance'),
        ('RESULT_RELEASE', 'Result Release'),
    ]

    title = models.CharField(max_length=200)
    content = models.TextField()
    announcement_type = models.CharField(max_length=20, choices=ANNOUNCEMENT_TYPE)
    target_user_types = models.CharField(
        max_length=200,
        blank=True,
        help_text="Comma-separated user types (e.g., ADMIN,KNEC_STAFF). Leave blank for all."
    )
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_announcements'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = "System Announcement"
        verbose_name_plural = "System Announcements"

    def __str__(self):
        return f"{self.title} ({self.get_announcement_type_display()})"

    def is_visible(self):
        """Check if announcement should be visible"""
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True