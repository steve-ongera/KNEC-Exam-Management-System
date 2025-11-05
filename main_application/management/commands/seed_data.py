from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random

from main_application.models import (
    AcademicYear, EducationLevel, Subject, GradingScheme, GradeRange,
    SchoolCategory, School, BirthCertificateRegistry, Candidate,
    ExamResult, AggregateResult, SchoolAdministrator, MarksEntryPermission,
    SystemConfiguration
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds the database with initial data for Kenya Education System'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing data before seeding',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting data seeding...'))
        
        # Clear existing data if --clear flag is provided
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            self.clear_data()
        
        # Seed in order of dependencies
        self.seed_users()
        self.seed_academic_years()
        self.seed_education_levels()
        self.seed_subjects()
        self.seed_grading_schemes()
        self.seed_school_categories()
        self.seed_schools()
        self.seed_school_administrators()
        self.seed_birth_certificates()
        self.seed_candidates()
        self.seed_exam_results()
        self.seed_system_config()
        
        self.stdout.write(self.style.SUCCESS('✅ Data seeding completed successfully!'))

    def clear_data(self):
        """Clear existing data"""
        # Clear in reverse order of dependencies to avoid foreign key constraints
        ExamResult.objects.all().delete()
        AggregateResult.objects.all().delete()
        Candidate.objects.all().delete()
        BirthCertificateRegistry.objects.all().delete()
        SchoolAdministrator.objects.all().delete()
        MarksEntryPermission.objects.all().delete()
        School.objects.all().delete()
        SchoolCategory.objects.all().delete()
        GradeRange.objects.all().delete()
        GradingScheme.objects.all().delete()
        Subject.objects.all().delete()
        EducationLevel.objects.all().delete()
        AcademicYear.objects.all().delete()
        
        # Keep superusers, delete other users
        User.objects.filter(is_superuser=False).delete()
        
        # Reset system configuration
        SystemConfiguration.objects.all().delete()

    def seed_users(self):
        """Create system users"""
        self.stdout.write('Creating users...')
        
        # Check if admin already exists to avoid duplicate error
        if not User.objects.filter(email='admin@knec.ac.ke').exists():
            # Create superuser/admin
            admin = User.objects.create_superuser(
                email='admin@knec.ac.ke',
                password='admin123',
                first_name='System',
                last_name='Administrator',
                user_type='ADMIN',
                phone_number='0712000000'
            )
        else:
            admin = User.objects.get(email='admin@knec.ac.ke')
        
        # KNEC Staff
        knec_users = [
            {'email': 'john.kamau@knec.ac.ke', 'first_name': 'John', 'last_name': 'Kamau'},
            {'email': 'mary.wanjiru@knec.ac.ke', 'first_name': 'Mary', 'last_name': 'Wanjiru'},
        ]
        
        for user_data in knec_users:
            if not User.objects.filter(email=user_data['email']).exists():
                User.objects.create_user(
                    email=user_data['email'],
                    password='knec123',
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    user_type='KNEC_STAFF',
                    phone_number=f'071200000{random.randint(1,9)}'
                )
        
        # Marks Entry Clerks (with expiry)
        marks_clerks = [
            {'email': 'clerk1@knec.ac.ke', 'first_name': 'Peter', 'last_name': 'Omondi'},
            {'email': 'clerk2@knec.ac.ke', 'first_name': 'Grace', 'last_name': 'Akinyi'},
            {'email': 'clerk3@knec.ac.ke', 'first_name': 'David', 'last_name': 'Mwangi'},
        ]
        
        for clerk_data in marks_clerks:
            if not User.objects.filter(email=clerk_data['email']).exists():
                User.objects.create_user(
                    email=clerk_data['email'],
                    password='clerk123',
                    first_name=clerk_data['first_name'],
                    last_name=clerk_data['last_name'],
                    user_type='MARKS_ENTRY',
                    phone_number=f'072000000{random.randint(1,9)}',
                    account_expires_at=timezone.now() + timedelta(days=90)
                )
        
        # School Administrators
        school_admins = [
            {'email': 'principal.alliance@school.ke', 'first_name': 'James', 'last_name': 'Muthoni'},
            {'email': 'principal.starehe@school.ke', 'first_name': 'Susan', 'last_name': 'Njeri'},
            {'email': 'principal.mangu@school.ke', 'first_name': 'Patrick', 'last_name': 'Kimani'},
            {'email': 'principal.mang@school.ke', 'first_name': 'Elizabeth', 'last_name': 'Cherono'},
            {'email': 'head.kilimani@school.ke', 'first_name': 'George', 'last_name': 'Otieno'},
            {'email': 'head.ruaraka@school.ke', 'first_name': 'Jane', 'last_name': 'Wambui'},
        ]
        
        for admin_data in school_admins:
            if not User.objects.filter(email=admin_data['email']).exists():
                User.objects.create_user(
                    email=admin_data['email'],
                    password='school123',
                    first_name=admin_data['first_name'],
                    last_name=admin_data['last_name'],
                    user_type='SCHOOL_ADMIN',
                    phone_number=f'073000000{random.randint(1,9)}'
                )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created/verified {User.objects.count()} users'))

    def seed_academic_years(self):
        """Create academic years"""
        self.stdout.write('Creating academic years...')
        
        years = [
            {'year': '2021/2022', 'start': '2021-01-04', 'end': '2021-11-19', 'active': False},
            {'year': '2022/2023', 'start': '2022-01-03', 'end': '2022-11-18', 'active': False},
            {'year': '2023/2024', 'start': '2023-01-02', 'end': '2023-11-17', 'active': False},
            {'year': '2024/2025', 'start': '2024-01-02', 'end': '2024-11-22', 'active': True},
        ]
        
        admin = User.objects.filter(user_type='ADMIN').first()
        
        for year_data in years:
            if not AcademicYear.objects.filter(year=year_data['year']).exists():
                AcademicYear.objects.create(
                    year=year_data['year'],
                    start_date=year_data['start'],
                    end_date=year_data['end'],
                    is_active=year_data['active'],
                    created_by=admin
                )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {AcademicYear.objects.count()} academic years'))

    def seed_education_levels(self):
        """Create education levels"""
        self.stdout.write('Creating education levels...')
        
        levels = [
            {
                'name': 'KEPSEA',
                'description': 'Kenya Primary School Education Assessment - Grade 6 (CBC)',
                'max_score': 100
            },
            {
                'name': 'KCPE',
                'description': 'Kenya Certificate of Primary Education - Class 8 (8-4-4)',
                'max_score': 500
            },
            {
                'name': 'KCSE',
                'description': 'Kenya Certificate of Secondary Education - Form 4',
                'max_score': 84  # 12 points per subject × 7 subjects
            },
        ]
        
        for level_data in levels:
            if not EducationLevel.objects.filter(name=level_data['name']).exists():
                EducationLevel.objects.create(**level_data)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {EducationLevel.objects.count()} education levels'))

    def seed_subjects(self):
        """Create subjects for each education level"""
        self.stdout.write('Creating subjects...')
        
        kepsea = EducationLevel.objects.get(name='KEPSEA')
        kcpe = EducationLevel.objects.get(name='KCPE')
        kcse = EducationLevel.objects.get(name='KCSE')
        
        # KEPSEA Subjects (Grade 6 - CBC)
        kepsea_subjects = [
            {'code': 'ENG', 'name': 'English', 'compulsory': True},
            {'code': 'KIS', 'name': 'Kiswahili', 'compulsory': True},
            {'code': 'MAT', 'name': 'Mathematics', 'compulsory': True},
            {'code': 'SCI', 'name': 'Science and Technology', 'compulsory': True},
            {'code': 'SSS', 'name': 'Social Studies', 'compulsory': True},
            {'code': 'CRE', 'name': 'Christian Religious Education', 'compulsory': False},
            {'code': 'IRE', 'name': 'Islamic Religious Education', 'compulsory': False},
            {'code': 'HRE', 'name': 'Hindu Religious Education', 'compulsory': False},
        ]
        
        # KCPE Subjects (Class 8 - 8-4-4)
        kcpe_subjects = [
            {'code': 'ENG', 'name': 'English', 'compulsory': True},
            {'code': 'KIS', 'name': 'Kiswahili', 'compulsory': True},
            {'code': 'MAT', 'name': 'Mathematics', 'compulsory': True},
            {'code': 'SCI', 'name': 'Science', 'compulsory': True},
            {'code': 'SST', 'name': 'Social Studies', 'compulsory': True},
        ]
        
        # KCSE Subjects (Form 4)
        kcse_subjects = [
            {'code': 'ENG', 'name': 'English', 'compulsory': True},
            {'code': 'KIS', 'name': 'Kiswahili', 'compulsory': True},
            {'code': 'MAT', 'name': 'Mathematics', 'compulsory': True},
            {'code': 'BIO', 'name': 'Biology', 'compulsory': False},
            {'code': 'PHY', 'name': 'Physics', 'compulsory': False},
            {'code': 'CHE', 'name': 'Chemistry', 'compulsory': False},
            {'code': 'HIS', 'name': 'History', 'compulsory': False},
            {'code': 'GEO', 'name': 'Geography', 'compulsory': False},
            {'code': 'CRE', 'name': 'Christian Religious Education', 'compulsory': False},
            {'code': 'IRE', 'name': 'Islamic Religious Education', 'compulsory': False},
            {'code': 'BST', 'name': 'Business Studies', 'compulsory': False},
            {'code': 'AGR', 'name': 'Agriculture', 'compulsory': False},
        ]
        
        # Create subjects
        for subject_data in kepsea_subjects:
            code = f"KEPSEA-{subject_data['code']}"
            if not Subject.objects.filter(code=code).exists():
                Subject.objects.create(
                    education_level=kepsea,
                    code=code,
                    name=subject_data['name'],
                    is_compulsory=subject_data['compulsory']
                )
        
        for subject_data in kcpe_subjects:
            code = f"KCPE-{subject_data['code']}"
            if not Subject.objects.filter(code=code).exists():
                Subject.objects.create(
                    education_level=kcpe,
                    code=code,
                    name=subject_data['name'],
                    is_compulsory=subject_data['compulsory']
                )
        
        for subject_data in kcse_subjects:
            code = f"KCSE-{subject_data['code']}"
            if not Subject.objects.filter(code=code).exists():
                Subject.objects.create(
                    education_level=kcse,
                    code=code,
                    name=subject_data['name'],
                    is_compulsory=subject_data['compulsory']
                )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {Subject.objects.count()} subjects'))

    def seed_grading_schemes(self):
        """Create grading schemes for each education level and academic year"""
        self.stdout.write('Creating grading schemes...')
        
        academic_years = AcademicYear.objects.all()
        kepsea = EducationLevel.objects.get(name='KEPSEA')
        kcpe = EducationLevel.objects.get(name='KCPE')
        kcse = EducationLevel.objects.get(name='KCSE')
        admin = User.objects.filter(user_type='ADMIN').first()
        
        for year in academic_years:
            # KEPSEA Grading (Exceeding, Meeting, Approaching, Below)
            kepsea_scheme_name = f'KEPSEA Overall {year.year}'
            if not GradingScheme.objects.filter(name=kepsea_scheme_name).exists():
                kepsea_scheme = GradingScheme.objects.create(
                    name=kepsea_scheme_name,
                    education_level=kepsea,
                    academic_year=year,
                    is_overall=True,
                    created_by=admin,
                    description='CBC Grade 6 Assessment'
                )
                
                kepsea_grades = [
                    {'grade': 'EE', 'min': 80, 'max': 100, 'points': 4, 'desc': 'Exceeds Expectations', 'order': 1},
                    {'grade': 'ME', 'min': 60, 'max': 79, 'points': 3, 'desc': 'Meets Expectations', 'order': 2},
                    {'grade': 'AE', 'min': 40, 'max': 59, 'points': 2, 'desc': 'Approaches Expectations', 'order': 3},
                    {'grade': 'BE', 'min': 0, 'max': 39, 'points': 1, 'desc': 'Below Expectations', 'order': 4},
                ]
                
                for grade_data in kepsea_grades:
                    GradeRange.objects.create(
                        grading_scheme=kepsea_scheme,
                        grade=grade_data['grade'],
                        min_score=grade_data['min'],
                        max_score=grade_data['max'],
                        points=grade_data['points'],
                        description=grade_data['desc'],
                        order=grade_data['order']
                    )
            
            # KCPE Grading (A-E)
            kcpe_scheme_name = f'KCPE Overall {year.year}'
            if not GradingScheme.objects.filter(name=kcpe_scheme_name).exists():
                kcpe_scheme = GradingScheme.objects.create(
                    name=kcpe_scheme_name,
                    education_level=kcpe,
                    academic_year=year,
                    is_overall=True,
                    created_by=admin,
                    description='KCPE Grading System'
                )
                
                kcpe_grades = [
                    {'grade': 'A', 'min': 400, 'max': 500, 'points': 12, 'order': 1},
                    {'grade': 'B', 'min': 300, 'max': 399, 'points': 9, 'order': 2},
                    {'grade': 'C', 'min': 200, 'max': 299, 'points': 6, 'order': 3},
                    {'grade': 'D', 'min': 100, 'max': 199, 'points': 3, 'order': 4},
                    {'grade': 'E', 'min': 0, 'max': 99, 'points': 1, 'order': 5},
                ]
                
                for grade_data in kcpe_grades:
                    GradeRange.objects.create(
                        grading_scheme=kcpe_scheme,
                        grade=grade_data['grade'],
                        min_score=grade_data['min'],
                        max_score=grade_data['max'],
                        points=grade_data['points'],
                        order=grade_data['order']
                    )
            
            # KCSE Grading (A-E with +/-)
            kcse_scheme_name = f'KCSE Overall {year.year}'
            if not GradingScheme.objects.filter(name=kcse_scheme_name).exists():
                kcse_scheme = GradingScheme.objects.create(
                    name=kcse_scheme_name,
                    education_level=kcse,
                    academic_year=year,
                    is_overall=True,
                    created_by=admin,
                    description='KCSE Grading System'
                )
                
                kcse_grades = [
                    {'grade': 'A', 'min': 75, 'max': 84, 'order': 1},
                    {'grade': 'A-', 'min': 70, 'max': 74, 'order': 2},
                    {'grade': 'B+', 'min': 65, 'max': 69, 'order': 3},
                    {'grade': 'B', 'min': 60, 'max': 64, 'order': 4},
                    {'grade': 'B-', 'min': 55, 'max': 59, 'order': 5},
                    {'grade': 'C+', 'min': 50, 'max': 54, 'order': 6},
                    {'grade': 'C', 'min': 45, 'max': 49, 'order': 7},
                    {'grade': 'C-', 'min': 40, 'max': 44, 'order': 8},
                    {'grade': 'D+', 'min': 35, 'max': 39, 'order': 9},
                    {'grade': 'D', 'min': 30, 'max': 34, 'order': 10},
                    {'grade': 'D-', 'min': 25, 'max': 29, 'order': 11},
                    {'grade': 'E', 'min': 0, 'max': 24, 'order': 12},
                ]
                
                for grade_data in kcse_grades:
                    GradeRange.objects.create(
                        grading_scheme=kcse_scheme,
                        grade=grade_data['grade'],
                        min_score=grade_data['min'],
                        max_score=grade_data['max'],
                        order=grade_data['order']
                    )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {GradingScheme.objects.count()} grading schemes'))

    def seed_school_categories(self):
        """Create school categories"""
        self.stdout.write('Creating school categories...')
        
        kepsea = EducationLevel.objects.get(name='KEPSEA')
        kcpe = EducationLevel.objects.get(name='KCPE')
        kcse = EducationLevel.objects.get(name='KCSE')
        
        categories = [
            {
                'name': 'PRIMARY',
                'description': 'Primary schools offering education from Grade 1-6 (CBC) or Class 1-8 (8-4-4)',
                'levels': [kepsea, kcpe]
            },
            {
                'name': 'JSS',
                'description': 'Junior Secondary Schools (Grade 7-9)',
                'levels': []
            },
            {
                'name': 'SENIOR',
                'description': 'Senior Secondary/High Schools (Form 1-4 or Grade 10-12)',
                'levels': [kcse]
            },
            {
                'name': 'MIXED',
                'description': 'Mixed schools offering both primary and secondary education',
                'levels': [kepsea, kcpe, kcse]
            },
        ]
        
        for cat_data in categories:
            if not SchoolCategory.objects.filter(name=cat_data['name']).exists():
                category = SchoolCategory.objects.create(
                    name=cat_data['name'],
                    description=cat_data['description']
                )
                category.can_register_for.set(cat_data['levels'])
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {SchoolCategory.objects.count()} school categories'))

    def seed_schools(self):
        """Create schools from all regions of Kenya"""
        self.stdout.write('Creating schools...')
        
        primary_cat = SchoolCategory.objects.get(name='PRIMARY')
        senior_cat = SchoolCategory.objects.get(name='SENIOR')
        mixed_cat = SchoolCategory.objects.get(name='MIXED')
        
        schools_data = [
            # NAIROBI COUNTY - National Schools
            {'code': 'ALHS', 'name': 'Alliance High School', 'category': senior_cat, 'county': 'Nairobi', 'sub_county': 'Kiambu Road', 'contact_person': 'Principal Alliance', 'phone_number': '0712345001', 'email': 'info@alliance.sc.ke'},
            {'code': 'STBS', 'name': 'Starehe Boys Centre', 'category': senior_cat, 'county': 'Nairobi', 'sub_county': 'Starehe', 'contact_person': 'Principal Starehe', 'phone_number': '0712345002', 'email': 'info@starehe.sc.ke'},
            {'code': 'MGHS', 'name': 'Mangu High School', 'category': senior_cat, 'county': 'Nairobi', 'sub_county': 'Thika Road', 'contact_person': 'Principal Mangu', 'phone_number': '0712345003', 'email': 'info@mangu.sc.ke'},
            {'code': 'KLPS', 'name': 'Kilimani Primary School', 'category': primary_cat, 'county': 'Nairobi', 'sub_county': 'Dagoretti North', 'contact_person': 'Head Teacher', 'phone_number': '0712345004', 'email': 'info@kilimani.sc.ke'},
            {'code': 'RKPS', 'name': 'Ruaraka Primary School', 'category': primary_cat, 'county': 'Nairobi', 'sub_county': 'Kasarani', 'contact_person': 'Head Teacher', 'phone_number': '0712345005', 'email': 'info@ruaraka.sc.ke'},
            
            # KIAMBU COUNTY
            {'code': 'MNHS', 'name': "Mang'u High School", 'category': senior_cat, 'county': 'Kiambu', 'sub_county': 'Thika East', 'contact_person': 'Principal Mangu', 'phone_number': '0712345006', 'email': 'info@manguhigh.sc.ke'},
            {'code': 'LGHS', 'name': 'Loreto Girls Kiambu', 'category': senior_cat, 'county': 'Kiambu', 'sub_county': 'Kiambu Town', 'contact_person': 'Principal Loreto', 'phone_number': '0712345007', 'email': 'info@loretokiambu.sc.ke'},
            {'code': 'KKPS', 'name': 'Karuri Primary School', 'category': primary_cat, 'county': 'Kiambu', 'sub_county': 'Kikuyu', 'contact_person': 'Head Teacher', 'phone_number': '0712345008', 'email': 'info@karuri.sc.ke'},
            
            # MOMBASA COUNTY
            {'code': 'MBHS', 'name': 'Mombasa High School', 'category': senior_cat, 'county': 'Mombasa', 'sub_county': 'Mvita', 'contact_person': 'Principal Mombasa', 'phone_number': '0712345009', 'email': 'info@mombasahigh.sc.ke'},
            {'code': 'STGS', 'name': 'Serani Primary School', 'category': primary_cat, 'county': 'Mombasa', 'sub_county': 'Changamwe', 'contact_person': 'Head Teacher', 'phone_number': '0712345010', 'email': 'info@serani.sc.ke'},
            
            # KISUMU COUNTY
            {'code': 'KSHS', 'name': 'Kisumu Day Secondary School', 'category': senior_cat, 'county': 'Kisumu', 'sub_county': 'Kisumu Central', 'contact_person': 'Principal Kisumu', 'phone_number': '0712345011', 'email': 'info@kisumuhigh.sc.ke'},
            {'code': 'MMHS', 'name': 'Maseno School', 'category': senior_cat, 'county': 'Kisumu', 'sub_county': 'Maseno', 'contact_person': 'Principal Maseno', 'phone_number': '0712345012', 'email': 'info@maseno.sc.ke'},
            {'code': 'KPPS', 'name': 'Kondele Primary School', 'category': primary_cat, 'county': 'Kisumu', 'sub_county': 'Kisumu West', 'contact_person': 'Head Teacher', 'phone_number': '0712345013', 'email': 'info@kondele.sc.ke'},
            
            # NAKURU COUNTY
            {'code': 'MKHS', 'name': 'Menengai High School', 'category': senior_cat, 'county': 'Nakuru', 'sub_county': 'Nakuru East', 'contact_person': 'Principal Menengai', 'phone_number': '0712345014', 'email': 'info@menengai.sc.ke'},
            {'code': 'NKPS', 'name': 'Nakuru Primary School', 'category': primary_cat, 'county': 'Nakuru', 'sub_county': 'Nakuru Town', 'contact_person': 'Head Teacher', 'phone_number': '0712345015', 'email': 'info@nakuruprimary.sc.ke'},
            
            # UASIN GISHU COUNTY - Eldoret
            {'code': 'MMGS', 'name': 'Moi Girls Eldoret', 'category': senior_cat, 'county': 'Uasin Gishu', 'sub_county': 'Eldoret East', 'contact_person': 'Principal Moi Girls', 'phone_number': '0712345016', 'email': 'info@moigirlseldoret.sc.ke'},
            {'code': 'EDPS', 'name': 'Eldoret Primary School', 'category': primary_cat, 'county': 'Uasin Gishu', 'sub_county': 'Eldoret West', 'contact_person': 'Head Teacher', 'phone_number': '0712345017', 'email': 'info@eldoretprimary.sc.ke'},
            
            # MACHAKOS COUNTY
            {'code': 'MCHS', 'name': 'Machakos School', 'category': senior_cat, 'county': 'Machakos', 'sub_county': 'Machakos Town', 'contact_person': 'Principal Machakos', 'phone_number': '0712345018', 'email': 'info@machakos.sc.ke'},
            {'code': 'KTPS', 'name': 'Kathiani Primary School', 'category': primary_cat, 'county': 'Machakos', 'sub_county': 'Kathiani', 'contact_person': 'Head Teacher', 'phone_number': '0712345019', 'email': 'info@kathiani.sc.ke'},
            
            # NYERI COUNTY
            {'code': 'KRHS', 'name': 'Kagumo High School', 'category': senior_cat, 'county': 'Nyeri', 'sub_county': 'Nyeri Central', 'contact_person': 'Principal Kagumo', 'phone_number': '0712345020', 'email': 'info@kagumo.sc.ke'},
            {'code': 'NRPS', 'name': 'Nyeri Primary School', 'category': primary_cat, 'county': 'Nyeri', 'sub_county': 'Nyeri Town', 'contact_person': 'Head Teacher', 'phone_number': '0712345021', 'email': 'info@nyeriprimary.sc.ke'},
            
            # MERU COUNTY
            {'code': 'MWHS', 'name': 'Meru School', 'category': senior_cat, 'county': 'Meru', 'sub_county': 'Imenti North', 'contact_person': 'Principal Meru', 'phone_number': '0712345022', 'email': 'info@meruschool.sc.ke'},
            {'code': 'MRPS', 'name': 'Meru Township Primary', 'category': primary_cat, 'county': 'Meru', 'sub_county': 'Imenti Central', 'contact_person': 'Head Teacher', 'phone_number': '0712345023', 'email': 'info@merutownship.sc.ke'},
            
            # KAKAMEGA COUNTY
            {'code': 'KKHS', 'name': 'Kakamega High School', 'category': senior_cat, 'county': 'Kakamega', 'sub_county': 'Lurambi', 'contact_person': 'Principal Kakamega', 'phone_number': '0712345024', 'email': 'info@kakamegahigh.sc.ke'},
            {'code': 'MMPS', 'name': 'Mumias Primary School', 'category': primary_cat, 'county': 'Kakamega', 'sub_county': 'Mumias East', 'contact_person': 'Head Teacher', 'phone_number': '0712345025', 'email': 'info@mumias.sc.ke'},
            
            # GARISSA COUNTY
            {'code': 'GRHS', 'name': 'Garissa High School', 'category': senior_cat, 'county': 'Garissa', 'sub_county': 'Garissa Township', 'contact_person': 'Principal Garissa', 'phone_number': '0712345026', 'email': 'info@garissahigh.sc.ke'},
            {'code': 'GRPS', 'name': 'Garissa Primary School', 'category': primary_cat, 'county': 'Garissa', 'sub_county': 'Garissa Township', 'contact_person': 'Head Teacher', 'phone_number': '0712345027', 'email': 'info@garissaprimary.sc.ke'},
            
            # BUNGOMA COUNTY
            {'code': 'FHSS', 'name': 'Friends School Kamusinga', 'category': senior_cat, 'county': 'Bungoma', 'sub_county': 'Kanduyi', 'contact_person': 'Principal Kamusinga', 'phone_number': '0712345028', 'email': 'info@kamusinga.sc.ke'},
            {'code': 'BGPS', 'name': 'Bungoma DEB Primary', 'category': primary_cat, 'county': 'Bungoma', 'sub_county': 'Bungoma Central', 'contact_person': 'Head Teacher', 'phone_number': '0712345029', 'email': 'info@bungomadeb.sc.ke'},
            
            # KITUI COUNTY
            {'code': 'KTSH', 'name': 'Kitui School', 'category': senior_cat, 'county': 'Kitui', 'sub_county': 'Kitui Central', 'contact_person': 'Principal Kitui', 'phone_number': '0712345030', 'email': 'info@kituischool.sc.ke'},
            {'code': 'KIPS', 'name': 'Kitui Township Primary', 'category': primary_cat, 'county': 'Kitui', 'sub_county': 'Kitui Central', 'contact_person': 'Head Teacher', 'phone_number': '0712345031', 'email': 'info@kituitownship.sc.ke'},
            
            # KILIFI COUNTY
            {'code': 'MLHS', 'name': 'Malindi High School', 'category': senior_cat, 'county': 'Kilifi', 'sub_county': 'Malindi', 'contact_person': 'Principal Malindi', 'phone_number': '0712345032', 'email': 'info@malindihigh.sc.ke'},
            {'code': 'KLPS', 'name': 'Kilifi Primary School', 'category': primary_cat, 'county': 'Kilifi', 'sub_county': 'Kilifi North', 'contact_person': 'Head Teacher', 'phone_number': '0712345033', 'email': 'info@kilifiprimary.sc.ke'},
            
            # EMBU COUNTY
            {'code': 'EBHS', 'name': 'Embu High School', 'category': senior_cat, 'county': 'Embu', 'sub_county': 'Manyatta', 'contact_person': 'Principal Embu', 'phone_number': '0712345034', 'email': 'info@embuhigh.sc.ke'},
            {'code': 'EMPS', 'name': 'Embu Primary School', 'category': primary_cat, 'county': 'Embu', 'sub_county': 'Embu Town', 'contact_person': 'Head Teacher', 'phone_number': '0712345035', 'email': 'info@embuprimary.sc.ke'},
            
            # TRANS NZOIA COUNTY
            {'code': 'KTGS', 'name': 'Kitale Girls High School', 'category': senior_cat, 'county': 'Trans Nzoia', 'sub_county': 'Kiminini', 'contact_person': 'Principal Kitale', 'phone_number': '0712345036', 'email': 'info@kitalegirls.sc.ke'},
            {'code': 'TLPS', 'name': 'Kitale Primary School', 'category': primary_cat, 'county': 'Trans Nzoia', 'sub_county': 'Kitale West', 'contact_person': 'Head Teacher', 'phone_number': '0712345037', 'email': 'info@kitaleprimary.sc.ke'},
            
            # KERICHO COUNTY
            {'code': 'KRHS', 'name': 'Kericho High School', 'category': senior_cat, 'county': 'Kericho', 'sub_county': 'Ainamoi', 'contact_person': 'Principal Kericho', 'phone_number': '0712345038', 'email': 'info@kerichohigh.sc.ke'},
            {'code': 'KCPS', 'name': 'Kericho Township Primary', 'category': primary_cat, 'county': 'Kericho', 'sub_county': 'Kericho Town', 'contact_person': 'Head Teacher', 'phone_number': '0712345039', 'email': 'info@kerichoprimary.sc.ke'},
            
            # BOMET COUNTY
            {'code': 'BTSH', 'name': 'Bomet High School', 'category': senior_cat, 'county': 'Bomet', 'sub_county': 'Bomet Central', 'contact_person': 'Principal Bomet', 'phone_number': '0712345040', 'email': 'info@bomethigh.sc.ke'},
            {'code': 'BMPS', 'name': 'Bomet Primary School', 'category': primary_cat, 'county': 'Bomet', 'sub_county': 'Bomet Town', 'contact_person': 'Head Teacher', 'phone_number': '0712345041', 'email': 'info@bometprimary.sc.ke'},
        ]
        
        for school_data in schools_data:
            if not School.objects.filter(code=school_data['code']).exists():
                School.objects.create(**school_data)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {School.objects.count()} schools'))

    def seed_school_administrators(self):
        """Assign administrators to schools"""
        self.stdout.write('Assigning school administrators...')
        
        school_admins = User.objects.filter(user_type='SCHOOL_ADMIN')
        schools = School.objects.all()[:6]  # First 6 schools
        
        admin_school_pairs = [
            ('principal.alliance@school.ke', 'ALHS', 'PRINCIPAL'),
            ('principal.starehe@school.ke', 'STBS', 'PRINCIPAL'),
            ('principal.mangu@school.ke', 'MGHS', 'PRINCIPAL'),
            ('principal.mang@school.ke', 'MNHS', 'PRINCIPAL'),
            ('head.kilimani@school.ke', 'KLPS', 'PRINCIPAL'),
            ('head.ruaraka@school.ke', 'RKPS', 'PRINCIPAL'),
        ]
        
        knec_admin = User.objects.filter(user_type='ADMIN').first()
        
        for email, school_code, role in admin_school_pairs:
            try:
                user = User.objects.get(email=email)
                school = School.objects.get(code=school_code)
                if not SchoolAdministrator.objects.filter(user=user, school=school).exists():
                    SchoolAdministrator.objects.create(
                        user=user,
                        school=school,
                        role=role,
                        assigned_by=knec_admin
                    )
            except (User.DoesNotExist, School.DoesNotExist):
                continue
        
        self.stdout.write(self.style.SUCCESS(f'✓ Assigned {SchoolAdministrator.objects.count()} administrators'))

    def seed_birth_certificates(self):
        """Create birth certificate records"""
        self.stdout.write('Creating birth certificates...')
        
        # Kenyan names for realistic data
        first_names = [
            'James', 'Mary', 'John', 'Grace', 'Peter', 'Faith', 'David', 'Joy',
            'Michael', 'Elizabeth', 'Daniel', 'Sarah', 'Joseph', 'Ruth', 'Samuel',
            'Jane', 'Patrick', 'Ann', 'Paul', 'Lucy', 'Brian', 'Nancy', 'Kevin',
            'Christine', 'Stephen', 'Margaret', 'Anthony', 'Catherine', 'Moses', 'Rose'
        ]
        
        middle_names = [
            'Mwangi', 'Wanjiru', 'Otieno', 'Akinyi', 'Kimani', 'Njeri', 'Omondi',
            'Adhiambo', 'Kariuki', 'Wambui', 'Kipchoge', 'Chebet', 'Mutua', 'Muthoni',
            'Kamau', 'Wairimu', 'Kiplagat', 'Jepkorir', 'Odhiambo', 'Auma'
        ]
        
        last_names = [
            'Kamau', 'Njoroge', 'Otieno', 'Omondi', 'Kimani', 'Wanjiru', 'Mwangi',
            'Kipchoge', 'Mutua', 'Ochieng', 'Kariuki', 'Cheruiyot', 'Wafula', 'Kiptoo',
            'Nganga', 'Owino', 'Kemboi', 'Onyango', 'Gathoni', 'Kiprotich'
        ]
        
        counties = [
            'Nairobi', 'Kiambu', 'Mombasa', 'Kisumu', 'Nakuru', 'Uasin Gishu',
            'Machakos', 'Nyeri', 'Meru', 'Kakamega', 'Garissa', 'Bungoma',
            'Kitui', 'Kilifi', 'Embu', 'Trans Nzoia', 'Kericho', 'Bomet'
        ]
        
        # Create 150 birth certificates for candidates
        for i in range(150):
            cert_number = f"{random.randint(20000000, 30000000)}"
            birth_year = random.randint(2007, 2013)  # For students aged 11-17
            
            if not BirthCertificateRegistry.objects.filter(certificate_number=cert_number).exists():
                BirthCertificateRegistry.objects.create(
                    certificate_number=cert_number,
                    first_name=random.choice(first_names),
                    middle_name=random.choice(middle_names),
                    last_name=random.choice(last_names),
                    date_of_birth=datetime(birth_year, random.randint(1, 12), random.randint(1, 28)),
                    place_of_birth=random.choice(counties),
                    parent_guardian_name=f"{random.choice(first_names)} {random.choice(last_names)}",
                    is_verified=True
                )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {BirthCertificateRegistry.objects.count()} birth certificates'))

    def seed_candidates(self):
        """Register candidates for schools"""
        self.stdout.write('Registering candidates...')
        
        schools = School.objects.all()
        academic_years = AcademicYear.objects.all()
        birth_certs = list(BirthCertificateRegistry.objects.filter(is_used_for_exam=False))
        
        kcpe = EducationLevel.objects.get(name='KCPE')
        kcse = EducationLevel.objects.get(name='KCSE')
        kepsea = EducationLevel.objects.get(name='KEPSEA')
        
        school_admin = User.objects.filter(user_type='SCHOOL_ADMIN').first()
        
        cert_index = 0
        
        # Register candidates for each school
        for school in schools:
            # Determine which exams this school can register for
            can_register = school.category.can_register_for.all()
            
            # Register for most recent 2 academic years
            for year in academic_years[:2]:
                for edu_level in can_register:
                    # Number of candidates per school per level (10-30)
                    num_candidates = random.randint(10, 30)
                    
                    for _ in range(num_candidates):
                        if cert_index >= len(birth_certs):
                            break
                        
                        cert = birth_certs[cert_index]
                        cert_index += 1
                        
                        # Check if candidate already exists
                        if not Candidate.objects.filter(
                            birth_certificate=cert,
                            academic_year=year,
                            education_level=edu_level
                        ).exists():
                            
                            # Create candidate
                            candidate = Candidate.objects.create(
                                school=school,
                                education_level=edu_level,
                                academic_year=year,
                                first_name=cert.first_name,
                                middle_name=cert.middle_name,
                                last_name=cert.last_name,
                                gender=random.choice(['M', 'F']),
                                date_of_birth=cert.date_of_birth,
                                birth_certificate=cert,
                                is_birth_cert_verified=True,
                                phone_number=f'07{random.randint(10000000, 99999999)}',
                                parent_guardian_phone=f'07{random.randint(10000000, 99999999)}',
                                registered_by=school_admin
                            )
                            
                            # Mark birth cert as used
                            cert.is_used_for_exam = True
                            cert.used_exam_level = edu_level
                            cert.save()
        
        self.stdout.write(self.style.SUCCESS(f'✓ Registered {Candidate.objects.count()} candidates'))

    def seed_exam_results(self):
        """Generate exam results for candidates"""
        self.stdout.write('Generating exam results...')
        
        candidates = Candidate.objects.all()
        marks_entry_user = User.objects.filter(user_type='MARKS_ENTRY').first()
        
        for candidate in candidates:
            # Get subjects for this education level
            subjects = Subject.objects.filter(
                education_level=candidate.education_level,
                is_compulsory=True
            )
            
            # Get grading scheme
            grading_scheme = GradingScheme.objects.filter(
                education_level=candidate.education_level,
                academic_year=candidate.academic_year,
                is_overall=False
            ).first()
            
            if not grading_scheme:
                # Use overall grading scheme if no subject-specific one exists
                grading_scheme = GradingScheme.objects.filter(
                    education_level=candidate.education_level,
                    academic_year=candidate.academic_year,
                    is_overall=True
                ).first()
            
            if not grading_scheme:
                continue
            
            # Generate results for each subject
            for subject in subjects:
                # Check if result already exists
                if not ExamResult.objects.filter(candidate=candidate, subject=subject).exists():
                    # Generate realistic scores (bell curve distribution)
                    if candidate.education_level.name == 'KCPE':
                        # KCPE: 0-100 per subject
                        raw_score = min(100, max(0, random.gauss(60, 20)))
                    elif candidate.education_level.name == 'KCSE':
                        # KCSE: 0-12 points per subject
                        raw_score = min(12, max(1, random.gauss(7, 3)))
                    else:  # KEPSEA
                        # KEPSEA: 0-100
                        raw_score = min(100, max(0, random.gauss(65, 18)))
                    
                    # Create exam result
                    result = ExamResult.objects.create(
                        candidate=candidate,
                        subject=subject,
                        raw_score=Decimal(str(round(raw_score, 2))),
                        grading_scheme_used=grading_scheme,
                        entered_by=marks_entry_user
                    )
                    
                    # Calculate grade
                    result.calculate_grade()
            
            # Generate aggregate result if not exists
            if not AggregateResult.objects.filter(candidate=candidate).exists():
                self.create_aggregate_result(candidate)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Generated {ExamResult.objects.count()} exam results'))

    def create_aggregate_result(self, candidate):
        """Create aggregate result for a candidate"""
        # Get overall grading scheme
        overall_scheme = GradingScheme.objects.filter(
            education_level=candidate.education_level,
            academic_year=candidate.academic_year,
            is_overall=True
        ).first()
        
        if not overall_scheme:
            return
        
        knec_staff = User.objects.filter(user_type='KNEC_STAFF').first()
        
        # Create aggregate
        aggregate = AggregateResult.objects.create(
            candidate=candidate,
            grading_scheme_used=overall_scheme,
            is_released=True,  # Released for demo
            release_date=timezone.now(),
            released_by=knec_staff
        )
        
        # Calculate aggregate
        aggregate.calculate_aggregate()
        
        # Calculate positions (simplified - in real system would be more complex)
        self.calculate_positions(candidate, aggregate)

    def calculate_positions(self, candidate, aggregate):
        """Calculate candidate positions"""
        # Position in school
        school_candidates = AggregateResult.objects.filter(
            candidate__school=candidate.school,
            candidate__academic_year=candidate.academic_year,
            candidate__education_level=candidate.education_level,
            is_released=True
        ).order_by('-total_points')
        
        school_position = 1
        for idx, agg in enumerate(school_candidates, 1):
            if agg.id == aggregate.id:
                school_position = idx
                break
        
        aggregate.position_in_school = school_position
        
        # Position in county
        county_candidates = AggregateResult.objects.filter(
            candidate__school__county=candidate.school.county,
            candidate__academic_year=candidate.academic_year,
            candidate__education_level=candidate.education_level,
            is_released=True
        ).order_by('-total_points')
        
        county_position = 1
        for idx, agg in enumerate(county_candidates, 1):
            if agg.id == aggregate.id:
                county_position = idx
                break
        
        aggregate.position_in_county = county_position
        
        # Position nationally (random for demo)
        aggregate.position_nationally = random.randint(1, 100000)
        
        aggregate.save()

    def seed_system_config(self):
        """Create system configuration"""
        self.stdout.write('Creating system configuration...')
        
        admin = User.objects.filter(user_type='ADMIN').first()
        
        # Use get_or_create to avoid duplicates
        config, created = SystemConfiguration.objects.get_or_create(
            defaults={
                'result_access_fee': Decimal('50.00'),
                'results_release_enabled': True,
                'marks_entry_enabled': True,
                'marks_entry_deadline': timezone.now() + timedelta(days=60),
                'marks_entry_default_validity_days': 30,
                'updated_by': admin
            }
        )
        
        if not created:
            # Update existing config
            config.result_access_fee = Decimal('50.00')
            config.results_release_enabled = True
            config.marks_entry_enabled = True
            config.marks_entry_deadline = timezone.now() + timedelta(days=60)
            config.marks_entry_default_validity_days = 30
            config.updated_by = admin
            config.save()
        
        self.stdout.write(self.style.SUCCESS('✓ System configuration created'))