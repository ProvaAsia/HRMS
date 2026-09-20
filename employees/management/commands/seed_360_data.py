"""
Management command to seed 360-profile mock data for all existing EmployeeProfiles.
Fills: title_prefix, nickname, gender, marital_status, province, employee_status,
       confirmed_date, job_level, salary, bank_name, bank_account
Creates: EmployeeDocument, LeaveBalance, TrainingProgram/Enrollment, AppraisalCycle/Appraisal

Usage:
    python manage.py seed_360_data
"""
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from employees.models import EmployeeProfile, EmployeeDocument

User = get_user_model()

# ── Static lookup tables ────────────────────────────────────────────────────

BANKS = ['kbank', 'scb', 'bbl', 'ktb', 'bay']

PROVINCES = ['กรุงเทพมหานคร', 'นนทบุรี', 'ปทุมธานี', 'สมุทรปราการ',
             'เชียงใหม่', 'ขอนแก่น', 'นครราชสีมา', 'ชลบุรี']

# Per-profile overrides keyed by employee_id (for ชุดเก่า)
# and by username (for ชุดใหม่)
PROFILE_DATA = {
    # ── ชุดเก่า ──────────────────────────────────────────────────────────────
    'EMP001': dict(
        title='mr', nickname='วิชัย', gender='male', marital='married',
        province='กรุงเทพมหานคร', status='active', level='Director',
        salary=150000, bank='kbank', account='123-4-56789-0',
        join=date(2020, 1, 15), confirmed=date(2020, 7, 15),
        birth=date(1970, 3, 22),
    ),
    'EMP002': dict(
        title='mr', nickname='ชาย', gender='male', marital='married',
        province='นนทบุรี', status='active', level='Manager',
        salary=85000, bank='scb', account='987-6-54321-0',
        join=date(2020, 3, 1), confirmed=date(2020, 9, 1),
        birth=date(1982, 7, 10),
    ),
    'EMP003': dict(
        title='ms', nickname='มาลี', gender='female', marital='single',
        province='ปทุมธานี', status='active', level='Senior',
        salary=55000, bank='kbank', account='456-7-89012-3',
        join=date(2021, 5, 10), confirmed=date(2021, 11, 10),
        birth=date(1994, 11, 5),
    ),
    'EMP004': dict(
        title='ms', nickname='นีย์', gender='female', marital='married',
        province='กรุงเทพมหานคร', status='active', level='Manager',
        salary=82000, bank='bbl', account='234-5-67890-1',
        join=date(2020, 3, 1), confirmed=date(2020, 9, 1),
        birth=date(1980, 9, 15),
    ),
    'EMP005': dict(
        title='mr', nickname='สิทธิ์', gender='male', marital='married',
        province='สมุทรปราการ', status='active', level='Manager',
        salary=88000, bank='ktb', account='345-6-78901-2',
        join=date(2020, 3, 1), confirmed=date(2020, 9, 1),
        birth=date(1978, 5, 20),
    ),
    'EMP006': dict(
        title='ms', nickname='นภา', gender='female', marital='single',
        province='ชลบุรี', status='active', level='Manager',
        salary=80000, bank='bay', account='567-8-90123-4',
        join=date(2020, 6, 1), confirmed=date(2020, 12, 1),
        birth=date(1985, 2, 28),
    ),
    'EMP007': dict(
        title='mr', nickname='กร', gender='male', marital='single',
        province='กรุงเทพมหานคร', status='active', level='Junior',
        salary=42000, bank='scb', account='678-9-01234-5',
        join=date(2022, 1, 17), confirmed=date(2022, 7, 17),
        birth=date(1998, 4, 12),
    ),
    'EMP008': dict(
        title='ms', nickname='จิรา', gender='female', marital='single',
        province='นนทบุรี', status='active', level='Mid',
        salary=50000, bank='kbank', account='789-0-12345-6',
        join=date(2021, 8, 2), confirmed=date(2022, 2, 2),
        birth=date(1996, 8, 30),
    ),
    'EMP009': dict(
        title='ms', nickname='อรทัย', gender='female', marital='married',
        province='ปทุมธานี', status='active', level='Senior',
        salary=52000, bank='bbl', account='890-1-23456-7',
        join=date(2021, 2, 15), confirmed=date(2021, 8, 15),
        birth=date(1992, 6, 18),
    ),
    'EMP010': dict(
        title='mr', nickname='ปิยะ', gender='male', marital='single',
        province='กรุงเทพมหานคร', status='active', level='Junior',
        salary=38000, bank='scb', account='901-2-34567-8',
        join=date(2023, 3, 6), confirmed=date(2023, 9, 6),
        birth=date(2000, 1, 7),
    ),
    'EMP011': dict(
        title='ms', nickname='ศิริ', gender='female', marital='married',
        province='สมุทรปราการ', status='active', level='Senior',
        salary=58000, bank='ktb', account='012-3-45678-9',
        join=date(2020, 9, 1), confirmed=date(2021, 3, 1),
        birth=date(1990, 12, 3),
    ),
    'EMP012': dict(
        title='mr', nickname='อนุ', gender='male', marital='single',
        province='ขอนแก่น', status='active', level='Junior',
        salary=40000, bank='bay', account='112-3-45678-0',
        join=date(2022, 6, 20), confirmed=date(2022, 12, 20),
        birth=date(1997, 7, 25),
    ),
    # ── ชุดใหม่ ─────────────────────────────────────────────────────────────
    'director01': dict(
        title='mr', nickname='ดิเรก', gender='male', marital='married',
        province='กรุงเทพมหานคร', status='active', level='Director',
        salary=150000, bank='kbank', account='111-1-11111-1',
        join=date(2020, 1, 2), confirmed=date(2020, 7, 2),
        birth=date(1968, 4, 10),
    ),
    'fin_mgr01': dict(
        title='mr', nickname='ฟิน', gender='male', marital='married',
        province='กรุงเทพมหานคร', status='active', level='Manager',
        salary=88000, bank='bbl', account='222-2-22222-2',
        join=date(2020, 2, 1), confirmed=date(2020, 8, 1),
        birth=date(1979, 8, 5),
    ),
    'it_mgr01': dict(
        title='mr', nickname='ไอที', gender='male', marital='single',
        province='นนทบุรี', status='active', level='Manager',
        salary=85000, bank='scb', account='333-3-33333-3',
        join=date(2020, 2, 1), confirmed=date(2020, 8, 1),
        birth=date(1983, 3, 20),
    ),
    'hr_mgr01': dict(
        title='ms', nickname='เฮชอาร์', gender='female', marital='married',
        province='ปทุมธานี', status='active', level='Manager',
        salary=82000, bank='ktb', account='444-4-44444-4',
        join=date(2020, 2, 1), confirmed=date(2020, 8, 1),
        birth=date(1981, 6, 15),
    ),
    'ops_mgr01': dict(
        title='ms', nickname='ออปส์', gender='female', marital='married',
        province='สมุทรปราการ', status='active', level='Manager',
        salary=80000, bank='bay', account='555-5-55555-5',
        join=date(2020, 4, 1), confirmed=date(2020, 10, 1),
        birth=date(1986, 11, 28),
    ),
    'fin_emp01': dict(
        title='ms', nickname='ฝน', gender='female', marital='single',
        province='กรุงเทพมหานคร', status='active', level='Senior',
        salary=55000, bank='kbank', account='666-6-66666-6',
        join=date(2021, 6, 1), confirmed=date(2021, 12, 1),
        birth=date(1995, 5, 14),
    ),
    'it_emp01': dict(
        title='mr', nickname='โจ', gender='male', marital='single',
        province='นนทบุรี', status='active', level='Mid',
        salary=50000, bank='scb', account='777-7-77777-7',
        join=date(2022, 3, 15), confirmed=date(2022, 9, 15),
        birth=date(1997, 9, 2),
    ),
    'it_emp02': dict(
        title='mr', nickname='เอ', gender='male', marital='single',
        province='ปทุมธานี', status='probation', level='Junior',
        salary=42000, bank='bbl', account='888-8-88888-8',
        join=date(2026, 7, 1), confirmed=None,
        birth=date(2001, 2, 18),
    ),
    'hr_emp01': dict(
        title='ms', nickname='นุ้ย', gender='female', marital='single',
        province='กรุงเทพมหานคร', status='active', level='Junior',
        salary=40000, bank='ktb', account='999-9-99999-9',
        join=date(2023, 1, 9), confirmed=date(2023, 7, 9),
        birth=date(1999, 12, 25),
    ),
    'ops_emp01': dict(
        title='mr', nickname='บอล', gender='male', marital='single',
        province='ชลบุรี', status='active', level='Mid',
        salary=45000, bank='bay', account='000-0-00000-0',
        join=date(2022, 9, 1), confirmed=date(2023, 3, 1),
        birth=date(1996, 3, 30),
    ),
}

# ── Documents per employee (sampled round-robin) ────────────────────────────
DOCUMENT_TEMPLATES = [
    dict(doc_type='id_card',       doc_name='บัตรประจำตัวประชาชน',    status='active',  expiry_offset=None),
    dict(doc_type='education_cert',doc_name='วุฒิการศึกษาปริญญาตรี',  status='active',  expiry_offset=None),
    dict(doc_type='transcript',    doc_name='ผลการเรียน (Transcript)',  status='active',  expiry_offset=None),
    dict(doc_type='medical_cert',  doc_name='ใบรับรองแพทย์ประจำปี',   status='active',  expiry_offset=365),
    dict(doc_type='driver_license',doc_name='ใบอนุญาตขับรถยนต์',      status='active',  expiry_offset=1825),
]

# ── Training programs ────────────────────────────────────────────────────────
TRAINING_PROGRAMS = [
    dict(
        title='Python & Django Web Development',
        description='เรียนรู้การพัฒนา Web Application ด้วย Django Framework',
        trainer='สถาบัน Digital Skills Academy',
        category='Technical',
        start_date=date(2025, 11, 18), end_date=date(2025, 11, 19),
        location='Siam Discovery, Bangkok',
    ),
    dict(
        title='Leadership & People Management',
        description='ทักษะการบริหารทีมงานและผู้นำองค์กร',
        trainer='วิทยากร: ดร. ชัยวัฒน์ สุวรรณ',
        category='Management',
        start_date=date(2025, 9, 22), end_date=date(2025, 9, 22),
        location='โรงแรม Centara Grand, Bangkok',
    ),
    dict(
        title='Financial Analysis & Excel Advanced',
        description='การวิเคราะห์ทางการเงินด้วย Excel ระดับสูง',
        trainer='CPA Training Center',
        category='Finance',
        start_date=date(2025, 12, 8), end_date=date(2025, 12, 9),
        location='อาคาร Bangkok Business Center',
    ),
    dict(
        title='ISO 9001:2015 Internal Auditor',
        description='หลักสูตรผู้ตรวจสอบภายใน ระบบบริหารคุณภาพ ISO 9001',
        trainer='TÜV Nord Thailand',
        category='Quality',
        start_date=date(2026, 1, 20), end_date=date(2026, 1, 21),
        location='TÜV Nord Office, Silom',
    ),
    dict(
        title='Cybersecurity Awareness 2026',
        description='การรับรู้และป้องกันภัยไซเบอร์สำหรับองค์กร',
        trainer='NECTEC Security Team',
        category='IT Security',
        start_date=date(2026, 3, 10), end_date=date(2026, 3, 10),
        location='Online (Zoom)',
    ),
    dict(
        title='HR for Non-HR Managers',
        description='พื้นฐานการบริหารทรัพยากรบุคคลสำหรับหัวหน้างาน',
        trainer='SHRM Thailand Chapter',
        category='HR',
        start_date=date(2026, 5, 5), end_date=date(2026, 5, 5),
        location='True Digital Park, Bangna',
    ),
]

# ── Appraisal cycle ──────────────────────────────────────────────────────────
APPRAISAL_CYCLE = dict(
    name='ประเมินผลงาน H1/2026 (Jan–Jun)',
    description='รอบการประเมินครึ่งปีแรก 2026',
    start_date=date(2026, 1, 1),
    end_date=date(2026, 6, 30),
    status='closed',
)


class Command(BaseCommand):
    help = 'Seed 360-profile mock data: profile fields, documents, leave, training, appraisals'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('=== Seed 360 Data ==='))

        self._update_profiles()
        self._create_documents()
        self._seed_leave_balances()
        self._seed_training()
        self._seed_appraisals()

        self.stdout.write(self.style.SUCCESS('\n✓ seed_360_data completed!'))

    # ── 1. Update EmployeeProfiles ──────────────────────────────────────────
    def _update_profiles(self):
        self.stdout.write('\n[1/5] Updating EmployeeProfiles...')
        profiles = list(EmployeeProfile.objects.select_related('user').all())
        updated = 0
        for profile in profiles:
            data = (
                PROFILE_DATA.get(profile.employee_id)
                or PROFILE_DATA.get(profile.user.username)
            )
            if not data:
                # Auto-fill based on role
                is_mgr = hasattr(profile.user, 'role') and profile.user.role in ('manager', 'hr_manager', 'super_admin')
                data = dict(
                    title='mr', nickname=profile.first_name_th or profile.first_name_en or '',
                    gender=random.choice(['male', 'female']),
                    marital=random.choice(['single', 'married']),
                    province=random.choice(PROVINCES),
                    status='active', level='Manager' if is_mgr else 'Mid',
                    salary=70000 if is_mgr else 45000,
                    bank=random.choice(BANKS), account='000-0-00000-0',
                    join=profile.join_date or date(2021, 1, 1),
                    confirmed=profile.confirmed_date,
                    birth=profile.date_of_birth,
                )

            profile.title_prefix    = data['title']
            profile.nickname        = data['nickname']
            profile.gender          = data['gender']
            profile.marital_status  = data['marital']
            profile.province        = data['province']
            profile.employee_status = data['status']
            profile.job_level       = data['level']
            profile.salary          = data['salary']
            profile.bank_name       = data['bank']
            profile.bank_account    = data['account']
            if data.get('join') and not profile.join_date:
                profile.join_date = data['join']
            if data.get('confirmed'):
                profile.confirmed_date = data['confirmed']
            if data.get('birth') and not profile.date_of_birth:
                profile.date_of_birth = data['birth']
            profile.save()
            updated += 1

        self.stdout.write(f'  → {updated} profile(s) updated')

    # ── 2. EmployeeDocument ─────────────────────────────────────────────────
    def _create_documents(self):
        self.stdout.write('\n[2/5] Creating EmployeeDocuments...')
        profiles = list(EmployeeProfile.objects.all())
        created = 0
        for i, profile in enumerate(profiles):
            # Give each employee 2-3 document types (cycled so they differ)
            templates = DOCUMENT_TEMPLATES[i % 3: i % 3 + 3] or DOCUMENT_TEMPLATES[:2]
            issue = (profile.join_date or date(2020, 1, 1))
            for tmpl in templates:
                expiry = None
                if tmpl['expiry_offset']:
                    expiry = issue + timedelta(days=tmpl['expiry_offset'])
                _, was_created = EmployeeDocument.objects.get_or_create(
                    employee=profile,
                    doc_type=tmpl['doc_type'],
                    defaults=dict(
                        doc_name=tmpl['doc_name'],
                        doc_number=f"DOC{profile.employee_id[-3:] if profile.employee_id else '000'}{i:02d}",
                        issue_date=issue,
                        expiry_date=expiry,
                        status=tmpl['status'],
                    )
                )
                if was_created:
                    created += 1
        self.stdout.write(f'  → {created} document(s) created')

    # ── 3. LeaveBalance ─────────────────────────────────────────────────────
    def _seed_leave_balances(self):
        self.stdout.write('\n[3/5] Seeding LeaveBalances...')
        try:
            from leave.models import LeaveType, LeaveBalance, LeaveRequest
        except ImportError:
            self.stdout.write(self.style.WARNING('  ⚠ leave app not available, skip'))
            return

        # Ensure base leave types exist
        annual, _ = LeaveType.objects.get_or_create(
            name='Annual Leave',
            defaults=dict(name_th='ลาพักร้อน', default_days=10, days_per_year=10, is_paid=True)
        )
        sick, _ = LeaveType.objects.get_or_create(
            name='Sick Leave',
            defaults=dict(name_th='ลาป่วย', default_days=30, days_per_year=30, is_paid=True)
        )
        personal, _ = LeaveType.objects.get_or_create(
            name='Personal Leave',
            defaults=dict(name_th='ลากิจ', default_days=3, days_per_year=3, is_paid=True)
        )

        year = 2026
        created = 0
        for profile in EmployeeProfile.objects.select_related('user').all():
            user = profile.user
            # Annual — used_days based on seniority
            svc = profile.years_of_service()
            entitled_annual = min(10 + svc, 15)
            used_annual = random.choice([0, 1, 2, 3, 4, 5])

            for lt, entitled, used in [
                (annual,   entitled_annual, used_annual),
                (sick,     30,              random.choice([0, 1, 2, 3])),
                (personal, 3,               random.choice([0, 1])),
            ]:
                _, was_created = LeaveBalance.objects.get_or_create(
                    employee=user, leave_type=lt, year=year,
                    defaults=dict(entitled_days=entitled, used_days=used)
                )
                if was_created:
                    created += 1

            # 1 pending leave request per 3 employees
            if profile.pk % 3 == 0:
                start = date.today() + timedelta(days=7)
                LeaveRequest.objects.get_or_create(
                    employee=user, leave_type=annual,
                    start_date=start,
                    defaults=dict(end_date=start + timedelta(days=1), days=2,
                                  reason='ธุระส่วนตัว', status='pending')
                )

        self.stdout.write(f'  → {created} leave balance(s) created')

    # ── 4. Training ─────────────────────────────────────────────────────────
    def _seed_training(self):
        self.stdout.write('\n[4/5] Seeding Training...')
        try:
            from training.models import TrainingProgram, TrainingEnrollment
        except ImportError:
            self.stdout.write(self.style.WARNING('  ⚠ training app not available, skip'))
            return

        admin_user = User.objects.filter(
            role='super_admin'
        ).first() or User.objects.filter(is_superuser=True).first() or User.objects.first()

        programs = []
        for t in TRAINING_PROGRAMS:
            prog, _ = TrainingProgram.objects.get_or_create(
                title=t['title'],
                defaults=dict(
                    description=t['description'],
                    trainer=t['trainer'],
                    category=t['category'],
                    start_date=t['start_date'],
                    end_date=t['end_date'],
                    location=t['location'],
                    max_participants=30,
                    status='completed' if t['end_date'] < date.today() else 'upcoming',
                    created_by=admin_user,
                )
            )
            programs.append(prog)

        created = 0
        profiles = list(EmployeeProfile.objects.select_related('user').all())
        for i, profile in enumerate(profiles):
            # Each employee gets 2-4 trainings
            assigned = programs[i % len(programs): i % len(programs) + 3]
            for prog in assigned:
                is_past = prog.end_date < date.today()
                score = round(random.uniform(65, 98), 1) if is_past else None
                status = 'completed' if is_past else 'enrolled'
                _, was_created = TrainingEnrollment.objects.get_or_create(
                    training=prog, employee=profile.user,
                    defaults=dict(
                        status=status,
                        completion_date=prog.end_date if is_past else None,
                        score=score,
                    )
                )
                if was_created:
                    created += 1

        self.stdout.write(f'  → {created} enrollment(s) created')

    # ── 5. Appraisals ───────────────────────────────────────────────────────
    def _seed_appraisals(self):
        self.stdout.write('\n[5/5] Seeding Appraisals...')
        try:
            from appraisals.models import AppraisalCycle, Appraisal, Goal
        except ImportError:
            self.stdout.write(self.style.WARNING('  ⚠ appraisals app not available, skip'))
            return

        admin_user = User.objects.filter(
            role='super_admin'
        ).first() or User.objects.filter(is_superuser=True).first() or User.objects.first()

        cycle, _ = AppraisalCycle.objects.get_or_create(
            name=APPRAISAL_CYCLE['name'],
            defaults=dict(
                description=APPRAISAL_CYCLE['description'],
                start_date=APPRAISAL_CYCLE['start_date'],
                end_date=APPRAISAL_CYCLE['end_date'],
                status=APPRAISAL_CYCLE['status'],
                created_by=admin_user,
            )
        )

        SELF_COMMENTS = [
            'ผมตั้งใจทำงานและพัฒนาตนเองอย่างสม่ำเสมอ สามารถส่งงานได้ตรงเวลาทุกครั้ง',
            'ดิฉันมุ่งมั่นในการทำงานและพร้อมรับผิดชอบงานใหม่ๆ เพื่อพัฒนาองค์กร',
            'ทำงานด้วยความรับผิดชอบ มีการพัฒนาทักษะอย่างต่อเนื่อง และสื่อสารกับทีมได้ดี',
        ]
        MGR_COMMENTS = [
            'พนักงานมีผลงานดีและสามารถส่งงานได้ตามกำหนด ควรพัฒนาทักษะด้าน Leadership เพิ่มเติม',
            'ทำงานได้ดี มีความรับผิดชอบสูง ผลงานเป็นที่น่าพอใจ',
            'มีศักยภาพสูง สามารถรับมือกับงานที่หลากหลาย แนะนำให้พัฒนาทักษะการนำเสนอ',
        ]
        GOALS = [
            ('ปรับปรุงกระบวนการทำงาน', 'ลดขั้นตอนที่ซ้ำซ้อนด้วย Automation', 30),
            ('พัฒนาทักษะด้านเทคนิค', 'ผ่านการรับรองด้าน Cloud Computing ภายใน Q3', 25),
            ('บริหารโครงการ', 'นำส่งโครงการหลักได้ตามไทม์ไลน์และงบประมาณ', 30),
            ('พัฒนาทีมงาน', 'จัด Knowledge Sharing ทุกเดือน', 15),
        ]

        created = 0
        for profile in EmployeeProfile.objects.select_related('user').all():
            user = profile.user
            # Find manager user
            mgr_user = None
            if profile.direct_manager:
                mgr_user = profile.direct_manager.user
            if not mgr_user:
                mgr_user = admin_user

            self_r = random.randint(3, 5)
            mgr_r = random.choice([self_r - 1, self_r, self_r]) if self_r > 1 else self_r

            appraisal, was_created = Appraisal.objects.get_or_create(
                cycle=cycle, employee=user,
                defaults=dict(
                    manager=mgr_user,
                    status='completed',
                    self_rating=self_r,
                    manager_rating=max(1, min(5, mgr_r)),
                    self_comments=random.choice(SELF_COMMENTS),
                    manager_comments=random.choice(MGR_COMMENTS),
                )
            )
            if was_created:
                created += 1
                # Add goals
                for gtitle, gdesc, gweight in GOALS:
                    ach = random.randint(60, 100)
                    Goal.objects.get_or_create(
                        appraisal=appraisal, title=gtitle,
                        defaults=dict(
                            description=gdesc, weight=gweight,
                            status='completed', achievement=ach,
                            target_date=date(2026, 6, 30),
                        )
                    )

        self.stdout.write(f'  → {created} appraisal(s) created')
