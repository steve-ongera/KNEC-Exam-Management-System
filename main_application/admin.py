from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Avg
from .models import (
    User, UserActivityLog, AcademicYear, EducationLevel, Subject,
    GradingScheme, GradeRange, SchoolCategory, School, SchoolAdministrator,
    MarksEntryPermission, BirthCertificateRegistry, Candidate, ExamResult,
    AggregateResult, ResultAccessPayment, FraudAttemptLog, SchoolPerformanceReport,
    SystemConfiguration, Notification, SystemAnnouncement
)


# ============================================================
# USER MANAGEMENT
# ============================================================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'user_type', 'is_active', 'account_status', 'last_login']
    list_filter = ['user_type', 'is_active', 'is_staff', 'is_superuser', 'is_account_expired']
    search_fields = ['email', 'first_name', 'last_name', 'id_number', 'phone_number']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'id_number', 'profile_picture')}),
        ('Permissions', {'fields': ('user_type', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Account Expiry', {'fields': ('account_expires_at', 'is_account_expired')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined', 'last_login_ip')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'user_type', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['last_login', 'date_joined', 'last_login_ip']
    
    def account_status(self, obj):
        if obj.is_account_expired:
            return format_html('<span style="color: red;">Expired</span>')
        elif obj.account_expires_at:
            days_left = (obj.account_expires_at - timezone.now()).days
            if days_left <= 7:
                return format_html('<span style="color: orange;">Expires in {} days</span>', days_left)
            return format_html('<span style="color: green;">Active (Expires in {} days)</span>', days_left)
        return format_html('<span style="color: green;">Active</span>')
    account_status.short_description = 'Account Status'
    
    actions = ['extend_account_expiry_30_days', 'extend_account_expiry_60_days', 'deactivate_users']
    
    def extend_account_expiry_30_days(self, request, queryset):
        for user in queryset:
            user.extend_account_expiry(30)
        self.message_user(request, f"{queryset.count()} account(s) extended by 30 days")
    extend_account_expiry_30_days.short_description = "Extend account expiry by 30 days"
    
    def extend_account_expiry_60_days(self, request, queryset):
        for user in queryset:
            user.extend_account_expiry(60)
        self.message_user(request, f"{queryset.count()} account(s) extended by 60 days")
    extend_account_expiry_60_days.short_description = "Extend account expiry by 60 days"
    
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} user(s) deactivated")
    deactivate_users.short_description = "Deactivate selected users"


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'timestamp', 'ip_address', 'short_description']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__email', 'description', 'ip_address']
    readonly_fields = ['user', 'action', 'description', 'ip_address', 'user_agent', 'timestamp', 'content_type', 'object_id']
    date_hierarchy = 'timestamp'
    
    def short_description(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    short_description.short_description = 'Description'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# ============================================================
# ACADEMIC STRUCTURE
# ============================================================

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['year', 'start_date', 'end_date', 'is_active', 'created_by', 'candidate_count']
    list_filter = ['is_active']
    search_fields = ['year']
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    
    def candidate_count(self, obj):
        count = obj.candidates.count()
        return format_html('<a href="{}?academic_year__id__exact={}">{} candidates</a>',
                          reverse('admin:main_application_candidate_changelist'),
                          obj.id, count)
    candidate_count.short_description = 'Candidates'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(EducationLevel)
class EducationLevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'max_score', 'is_active', 'subject_count', 'created_at']
    list_filter = ['is_active', 'name']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    
    def subject_count(self, obj):
        return obj.subjects.count()
    subject_count.short_description = 'Subjects'


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'education_level', 'is_compulsory', 'is_active']
    list_filter = ['education_level', 'is_compulsory', 'is_active']
    search_fields = ['code', 'name']
    ordering = ['education_level', 'code']


# ============================================================
# GRADING
# ============================================================

class GradeRangeInline(admin.TabularInline):
    model = GradeRange
    extra = 1
    fields = ['grade', 'min_score', 'max_score', 'points', 'description', 'order']


@admin.register(GradingScheme)
class GradingSchemeAdmin(admin.ModelAdmin):
    list_display = ['name', 'education_level', 'academic_year', 'subject', 'is_overall', 'is_active', 'grade_ranges_count']
    list_filter = ['education_level', 'academic_year', 'is_overall', 'is_active']
    search_fields = ['name']
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    inlines = [GradeRangeInline]
    
    def grade_ranges_count(self, obj):
        return obj.grade_ranges.count()
    grade_ranges_count.short_description = 'Grade Ranges'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(GradeRange)
class GradeRangeAdmin(admin.ModelAdmin):
    list_display = ['grading_scheme', 'grade', 'min_score', 'max_score', 'points', 'order']
    list_filter = ['grading_scheme__education_level', 'grade']
    search_fields = ['grade', 'grading_scheme__name']
    ordering = ['grading_scheme', 'order', '-min_score']


# ============================================================
# SCHOOLS
# ============================================================

class SchoolAdministratorInline(admin.TabularInline):
    model = SchoolAdministrator
    extra = 1
    readonly_fields = ['assigned_date', 'assigned_by']
    fields = ['user', 'role', 'is_active', 'assigned_date']


@admin.register(SchoolCategory)
class SchoolCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'school_count']
    filter_horizontal = ['can_register_for']
    
    def school_count(self, obj):
        return obj.schools.count()
    school_count.short_description = 'Schools'


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'county', 'sub_county', 'is_active', 'candidate_count', 'registration_date']
    list_filter = ['category', 'county', 'is_active']
    search_fields = ['code', 'name', 'county', 'sub_county', 'email']
    readonly_fields = ['registration_date', 'created_at', 'updated_at']
    inlines = [SchoolAdministratorInline]
    
    fieldsets = (
        ('Basic Information', {'fields': ('code', 'name', 'category')}),
        ('Location', {'fields': ('county', 'sub_county')}),
        ('Contact Information', {'fields': ('contact_person', 'phone_number', 'email')}),
        ('Status', {'fields': ('is_active', 'registration_date')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def candidate_count(self, obj):
        count = obj.candidates.count()
        return format_html('<a href="{}?school__id__exact={}">{}</a>',
                          reverse('admin:main_application_candidate_changelist'),
                          obj.id, count)
    candidate_count.short_description = 'Candidates'


@admin.register(SchoolAdministrator)
class SchoolAdministratorAdmin(admin.ModelAdmin):
    list_display = ['user', 'school', 'role', 'is_active', 'assigned_date', 'assigned_by']
    list_filter = ['role', 'is_active', 'assigned_date']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'school__name']
    readonly_fields = ['assigned_date', 'assigned_by']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================
# PERMISSIONS
# ============================================================

@admin.register(MarksEntryPermission)
class MarksEntryPermissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'academic_year', 'education_level', 'is_active', 'validity_status', 'valid_from', 'valid_until']
    list_filter = ['is_active', 'academic_year', 'education_level', 'valid_from', 'valid_until']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    filter_horizontal = ['subjects', 'schools']
    readonly_fields = ['created_by', 'created_at']
    
    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Scope', {'fields': ('academic_year', 'education_level', 'subjects', 'schools')}),
        ('Validity', {'fields': ('is_active', 'valid_from', 'valid_until')}),
        ('Tracking', {'fields': ('created_by', 'created_at')}),
    )
    
    def validity_status(self, obj):
        if obj.is_valid():
            return format_html('<span style="color: green;">Valid</span>')
        return format_html('<span style="color: red;">Invalid/Expired</span>')
    validity_status.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================
# CANDIDATES & BIRTH CERTIFICATES
# ============================================================

@admin.register(BirthCertificateRegistry)
class BirthCertificateRegistryAdmin(admin.ModelAdmin):
    list_display = ['certificate_number', 'full_name', 'date_of_birth', 'is_verified', 'usage_status']
    list_filter = ['is_verified', 'is_used_for_exam', 'used_exam_level']
    search_fields = ['certificate_number', 'first_name', 'middle_name', 'last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    def full_name(self, obj):
        return obj.get_full_name()
    full_name.short_description = 'Full Name'
    
    def usage_status(self, obj):
        if obj.is_used_for_exam:
            return format_html('<span style="color: orange;">Used for {}</span>', obj.used_exam_level)
        return format_html('<span style="color: green;">Available</span>')
    usage_status.short_description = 'Usage Status'


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['index_number', 'full_name_display', 'school', 'education_level', 'academic_year', 'gender', 'birth_cert_status', 'is_active']
    list_filter = ['education_level', 'academic_year', 'school__county', 'gender', 'is_active', 'is_birth_cert_verified']
    search_fields = ['index_number', 'first_name', 'middle_name', 'last_name', 'birth_certificate__certificate_number']
    readonly_fields = ['index_number', 'registered_by', 'registration_date', 'created_at', 'updated_at']
    date_hierarchy = 'registration_date'
    
    fieldsets = (
        ('Registration', {'fields': ('index_number', 'school', 'education_level', 'academic_year')}),
        ('Personal Information', {'fields': ('first_name', 'middle_name', 'last_name', 'gender', 'date_of_birth')}),
        ('Birth Certificate', {'fields': ('birth_certificate', 'is_birth_cert_verified')}),
        ('Contact', {'fields': ('phone_number', 'parent_guardian_phone')}),
        ('Status & Tracking', {'fields': ('is_active', 'registered_by', 'registration_date')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def full_name_display(self, obj):
        return obj.get_full_name()
    full_name_display.short_description = 'Full Name'
    
    def birth_cert_status(self, obj):
        if obj.is_birth_cert_verified:
            return format_html('<span style="color: green;">✓ Verified</span>')
        elif obj.birth_certificate:
            return format_html('<span style="color: orange;">Pending</span>')
        return format_html('<span style="color: red;">Not Provided</span>')
    birth_cert_status.short_description = 'Birth Cert'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.registered_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================
# RESULTS
# ============================================================

@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'subject', 'raw_score', 'grade', 'points', 'entered_by', 'created_at']
    list_filter = ['subject', 'grade', 'candidate__education_level', 'candidate__academic_year']
    search_fields = ['candidate__index_number', 'candidate__first_name', 'candidate__last_name', 'subject__code']
    readonly_fields = ['entered_by', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.entered_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AggregateResult)
class AggregateResultAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'mean_grade', 'total_points', 'position_in_school', 'position_nationally', 'release_status', 'release_date']
    list_filter = ['is_released', 'candidate__education_level', 'candidate__academic_year', 'mean_grade']
    search_fields = ['candidate__index_number', 'candidate__first_name', 'candidate__last_name']
    readonly_fields = ['released_by', 'release_date', 'created_at', 'updated_at']
    date_hierarchy = 'release_date'
    
    actions = ['release_results', 'unrelease_results', 'recalculate_aggregates']
    
    def release_status(self, obj):
        if obj.is_released:
            return format_html('<span style="color: green;">Released</span>')
        return format_html('<span style="color: orange;">Pending</span>')
    release_status.short_description = 'Status'
    
    def release_results(self, request, queryset):
        for result in queryset:
            if not result.is_released:
                result.is_released = True
                result.release_date = timezone.now()
                result.released_by = request.user
                result.save()
        self.message_user(request, f"{queryset.count()} result(s) released")
    release_results.short_description = "Release selected results"
    
    def unrelease_results(self, request, queryset):
        queryset.update(is_released=False, release_date=None, released_by=None)
        self.message_user(request, f"{queryset.count()} result(s) unreleased")
    unrelease_results.short_description = "Unrelease selected results"
    
    def recalculate_aggregates(self, request, queryset):
        for result in queryset:
            result.calculate_aggregate()
        self.message_user(request, f"{queryset.count()} aggregate(s) recalculated")
    recalculate_aggregates.short_description = "Recalculate selected aggregates"


# ============================================================
# PAYMENTS
# ============================================================

@admin.register(ResultAccessPayment)
class ResultAccessPaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'candidate', 'amount', 'status', 'payment_status_display', 'access_status', 'payment_date']
    list_filter = ['status', 'result_accessed', 'payment_date']
    search_fields = ['transaction_id', 'candidate__index_number', 'phone_number', 'mpesa_receipt_number']
    readonly_fields = ['transaction_id', 'merchant_request_id', 'checkout_request_id', 'payment_date', 'access_date', 'created_at', 'updated_at']
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('Transaction', {'fields': ('transaction_id', 'candidate', 'phone_number', 'amount', 'status')}),
        ('M-Pesa Details', {'fields': ('mpesa_receipt_number', 'merchant_request_id', 'checkout_request_id', 'result_desc', 'payment_date')}),
        ('Access Tracking', {'fields': ('result_accessed', 'access_date', 'access_ip')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def payment_status_display(self, obj):
        colors = {'completed': 'green', 'pending': 'orange', 'failed': 'red', 'cancelled': 'gray'}
        return format_html('<span style="color: {};">{}</span>', 
                          colors.get(obj.status, 'black'), obj.get_status_display())
    payment_status_display.short_description = 'Payment Status'
    
    def access_status(self, obj):
        if obj.result_accessed:
            return format_html('<span style="color: green;">Accessed</span>')
        return format_html('<span style="color: gray;">Not Accessed</span>')
    access_status.short_description = 'Result Access'


# ============================================================
# SECURITY & FRAUD
# ============================================================

@admin.register(FraudAttemptLog)
class FraudAttemptLogAdmin(admin.ModelAdmin):
    list_display = ['attempt_type', 'user_or_anonymous', 'ip_address', 'resolution_status', 'created_at']
    list_filter = ['attempt_type', 'is_resolved', 'created_at']
    search_fields = ['index_number', 'birth_certificate_number', 'phone_number', 'ip_address', 'description']
    readonly_fields = ['user', 'ip_address', 'user_agent', 'created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Attempt Details', {'fields': ('attempt_type', 'user', 'description')}),
        ('Related Information', {'fields': ('index_number', 'birth_certificate_number', 'phone_number')}),
        ('Technical Details', {'fields': ('ip_address', 'user_agent')}),
        ('Resolution', {'fields': ('is_resolved', 'resolved_by', 'resolution_notes')}),
        ('Timestamp', {'fields': ('created_at',)}),
    )
    
    def user_or_anonymous(self, obj):
        if obj.user:
            return obj.user.email
        return 'Anonymous'
    user_or_anonymous.short_description = 'User'
    
    def resolution_status(self, obj):
        if obj.is_resolved:
            return format_html('<span style="color: green;">Resolved</span>')
        return format_html('<span style="color: red;">Unresolved</span>')
    resolution_status.short_description = 'Status'


# ============================================================
# REPORTS
# ============================================================

@admin.register(SchoolPerformanceReport)
class SchoolPerformanceReportAdmin(admin.ModelAdmin):
    list_display = ['school', 'academic_year', 'education_level', 'total_candidates', 'mean_score', 'top_grade', 'rank_nationally', 'generated_at']
    list_filter = ['academic_year', 'education_level', 'school__county']
    search_fields = ['school__name', 'school__code']
    readonly_fields = ['generated_by', 'generated_at']
    date_hierarchy = 'generated_at'
    
    fieldsets = (
        ('Report Information', {'fields': ('school', 'academic_year', 'education_level')}),
        ('Statistics', {'fields': ('total_candidates', 'candidates_with_results', 'mean_score', 'top_grade')}),
        ('Grade Distribution', {
            'fields': ('grade_a', 'grade_a_minus', 'grade_b_plus', 'grade_b', 'grade_b_minus',
                      'grade_c_plus', 'grade_c', 'grade_c_minus', 'grade_d_plus', 'grade_d', 
                      'grade_d_minus', 'grade_e')
        }),
        ('Rankings', {'fields': ('rank_in_county', 'rank_nationally')}),
        ('Generation Info', {'fields': ('generated_by', 'generated_at')}),
    )
    
    actions = ['regenerate_reports']
    
    def regenerate_reports(self, request, queryset):
        for report in queryset:
            report.generate_report()
        self.message_user(request, f"{queryset.count()} report(s) regenerated")
    regenerate_reports.short_description = "Regenerate selected reports"


# ============================================================
# SYSTEM CONFIGURATION
# ============================================================

@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = ['pk', 'result_access_fee', 'results_release_enabled', 'marks_entry_enabled', 'maintenance_mode', 'updated_at']
    readonly_fields = ['updated_by', 'updated_at']
    
    fieldsets = (
        ('Results Access', {'fields': ('result_access_fee', 'results_release_enabled')}),
        ('Marks Entry', {'fields': ('marks_entry_enabled', 'marks_entry_deadline', 'marks_entry_default_validity_days')}),
        ('Maintenance', {'fields': ('maintenance_mode', 'maintenance_message')}),
        ('Tracking', {'fields': ('updated_by', 'updated_at')}),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================
# NOTIFICATIONS
# ============================================================

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'read_status', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__email', 'title', 'message']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def read_status(self, obj):
        if obj.is_read:
            return format_html('<span style="color: gray;">Read</span>')
        return format_html('<span style="color: blue;">Unread</span>')
    read_status.short_description = 'Status'


@admin.register(SystemAnnouncement)
class SystemAnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'announcement_type', 'visibility_status', 'start_date', 'end_date', 'created_by']
    list_filter = ['announcement_type', 'is_active', 'start_date', 'end_date']
    search_fields = ['title', 'content']
    readonly_fields = ['created_by', 'created_at']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Announcement Details', {'fields': ('title', 'content', 'announcement_type')}),
        ('Targeting', {'fields': ('target_user_types',)}),
        ('Visibility', {'fields': ('is_active', 'start_date', 'end_date')}),
        ('Tracking', {'fields': ('created_by', 'created_at')}),
    )
    
    def visibility_status(self, obj):
        if obj.is_visible():
            return format_html('<span style="color: green;">Visible</span>')
        return format_html('<span style="color: gray;">Hidden</span>')
    visibility_status.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# ============================================================
# CUSTOM ADMIN SITE CONFIGURATION
# ============================================================

admin.site.site_header = "KNEC Exam Management System"
admin.site.site_title = "KNEC Admin"
admin.site.index_title = "Welcome to KNEC Exam Management System Administration"