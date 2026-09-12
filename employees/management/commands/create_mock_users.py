"""
Management command to create 10 mock users with org structure:
  - 1 Director (super_admin) overseeing all departments
  - 4 Managers: Finance, IT, HR, Operations
  - 5 Employees across departments

Usage:
    python manage.py create_mock_users

Password for all accounts: Makara2025!
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from employees.models import (
    EmployeeProfile, Division, Department, CostCenter, WorkLocation
)

User = get_user_model()
PASSWORD = 'Makara2025!'


class Command(BaseCommand):
    help = 'Create 10 mock users with org structure (Director + Managers + Employees)'

    def handle(self, *args, **options):
        self.stdout.write('Creating org structure (divisions, departments)...')
        self._create_org_structure()

        self.stdout.write('Creating users...')
        director = self._create_director()
        managers = self._create_managers(director)
        self._create_employees(managers)

        self.stdout.write(self.style.SUCCESS(
            '\n✓ Done! 10 mock users created (or already exist).'
        ))
        self.stdout.write(f'  Password for all accounts: {PASSWORD}')
        self.stdout.write('  Accounts:')
        self.stdout.write('    director01  → Super Admin / Director')
        self.stdout.write('    fin_mgr01   → Manager / Finance Manager')
        self.stdout.write('    it_mgr01    → Manager / IT Manager')
        self.stdout.write('    hr_mgr01    → HR Manager / HR Manager')
        self.stdout.write('    ops_mgr01   → Manager / Operations Manager')
        self.stdout.write('    fin_emp01   → Employee / Finance Analyst')
        self.stdout.write('    it_emp01    → Employee / Software Engineer')
        self.stdout.write('    it_emp02    → Employee / System Admin')
        self.stdout.write('    hr_emp01    → Employee / HR Officer')
        self.stdout.write('    ops_emp01   → Employee / Operations Coordinator')

    # ──────────────────────────────────────────────────────────────
    # Org structure
    # ──────────────────────────────────────────────────────────────
    def _create_org_structure(self):
        # Divisions
        div_corp, _ = Division.objects.get_or_create(
            code='DIV-CORP', defaults={'name': 'Corporate'}
        )
        div_ops, _ = Division.objects.get_or_create(
            code='DIV-OPS', defaults={'name': 'Operations'}
        )

        # Departments
        self.dept_finance, _ = Department.objects.get_or_create(
            code='DEPT-FIN', defaults={'name': 'Finance', 'division': div_corp}
        )
        self.dept_it, _ = Department.objects.get_or_create(
            code='DEPT-IT', defaults={'name': 'Information Technology', 'division': div_corp}
        )
        self.dept_hr, _ = Department.objects.get_or_create(
            code='DEPT-HR', defaults={'name': 'Human Resources', 'division': div_corp}
        )
        self.dept_ops, _ = Department.objects.get_or_create(
            code='DEPT-OPS', defaults={'name': 'Operations', 'division': div_ops}
        )

        # Cost Centers
        self.cc_corp, _ = CostCenter.objects.get_or_create(
            code='CC-CORP', defaults={'name': 'Corporate HQ'}
        )
        self.cc_ops, _ = CostCenter.objects.get_or_create(
            code='CC-OPS', defaults={'name': 'Operations'}
        )

        # Work Locations
        self.loc_bkk, _ = WorkLocation.objects.get_or_create(
            name='Bangkok HQ',
            defaults={'address': '123 Silom Road, Bang Rak, Bangkok 10500'}
        )
        self.loc_sp, _ = WorkLocation.objects.get_or_create(
            name='Samut Prakan',
            defaults={'address': '456 Bearing Road, Samut Prakan 10270'}
        )

    # ──────────────────────────────────────────────────────────────
    # Director
    # ──────────────────────────────────────────────────────────────
    def _create_director(self):
        user, created = User.objects.get_or_create(
            username='director01',
            defaults={
                'first_name': 'Wichai',
                'last_name': 'Pongsuwat',
                'email': 'director01@company.com',
                'role': 'super_admin',
                'is_staff': True,
            }
        )
        if created:
            user.set_password(PASSWORD)
            user.save()
            self.stdout.write(f'  + Created user: director01')
        else:
            self.stdout.write(f'  ~ Already exists: director01')

        profile, _ = EmployeeProfile.objects.get_or_create(
            user=user,
            defaults={
                'employee_id': 'EMP-D01',
                'first_name_en': 'Wichai',
                'last_name_en': 'Pongsuwat',
                'first_name_th': 'วิชัย',
                'last_name_th': 'พงษ์สุวรรณ',
                'job_title': 'Director',
                'employment_type': 'full_time',
                'department': self.dept_corp_or_first(),
                'cost_center': self.cc_corp,
                'work_location': self.loc_bkk,
            }
        )
        return profile

    def dept_corp_or_first(self):
        return self.dept_hr  # Director sits under HR dept for org purposes

    # ──────────────────────────────────────────────────────────────
    # Managers
    # ──────────────────────────────────────────────────────────────
    def _create_managers(self, director_profile):
        specs = [
            {
                'username': 'fin_mgr01',
                'first_name': 'Somsri',
                'last_name': 'Nakorn',
                'first_name_th': 'สมศรี',
                'last_name_th': 'นาคร',
                'email': 'fin_mgr01@company.com',
                'role': 'manager',
                'employee_id': 'EMP-FM1',
                'job_title': 'Finance Manager',
                'department': self.dept_finance,
                'cost_center': self.cc_corp,
                'work_location': self.loc_bkk,
            },
            {
                'username': 'it_mgr01',
                'first_name': 'Prasit',
                'last_name': 'Manakij',
                'first_name_th': 'ประสิทธิ์',
                'last_name_th': 'มานะกิจ',
                'email': 'it_mgr01@company.com',
                'role': 'manager',
                'employee_id': 'EMP-IM1',
                'job_title': 'IT Manager',
                'department': self.dept_it,
                'cost_center': self.cc_corp,
                'work_location': self.loc_bkk,
            },
            {
                'username': 'hr_mgr01',
                'first_name': 'Sunee',
                'last_name': 'Rakdi',
                'first_name_th': 'สุนีย์',
                'last_name_th': 'รักษ์ดี',
                'email': 'hr_mgr01@company.com',
                'role': 'hr_manager',
                'employee_id': 'EMP-HM1',
                'job_title': 'HR Manager',
                'department': self.dept_hr,
                'cost_center': self.cc_corp,
                'work_location': self.loc_bkk,
            },
            {
                'username': 'ops_mgr01',
                'first_name': 'Naphaporn',
                'last_name': 'Charoensuk',
                'first_name_th': 'นภาพร',
                'last_name_th': 'เจริญสุข',
                'email': 'ops_mgr01@company.com',
                'role': 'manager',
                'employee_id': 'EMP-OM1',
                'job_title': 'Operations Manager',
                'department': self.dept_ops,
                'cost_center': self.cc_ops,
                'work_location': self.loc_sp,
            },
        ]

        manager_profiles = {}
        for s in specs:
            user, created = User.objects.get_or_create(
                username=s['username'],
                defaults={
                    'first_name': s['first_name'],
                    'last_name': s['last_name'],
                    'email': s['email'],
                    'role': s['role'],
                }
            )
            if created:
                user.set_password(PASSWORD)
                user.save()
                self.stdout.write(f'  + Created user: {s["username"]}')
            else:
                self.stdout.write(f'  ~ Already exists: {s["username"]}')

            profile, _ = EmployeeProfile.objects.get_or_create(
                user=user,
                defaults={
                    'employee_id': s['employee_id'],
                    'first_name_en': s['first_name'],
                    'last_name_en': s['last_name'],
                    'first_name_th': s['first_name_th'],
                    'last_name_th': s['last_name_th'],
                    'job_title': s['job_title'],
                    'employment_type': 'full_time',
                    'department': s['department'],
                    'cost_center': s['cost_center'],
                    'work_location': s['work_location'],
                    'direct_manager': director_profile,
                }
            )
            manager_profiles[s['username']] = profile

        return manager_profiles

    # ──────────────────────────────────────────────────────────────
    # Employees
    # ──────────────────────────────────────────────────────────────
    def _create_employees(self, manager_profiles):
        specs = [
            {
                'username': 'fin_emp01',
                'first_name': 'Araya',
                'last_name': 'Siriwan',
                'first_name_th': 'อารยา',
                'last_name_th': 'ศิริวรรณ',
                'email': 'fin_emp01@company.com',
                'role': 'employee',
                'employee_id': 'EMP-FE1',
                'job_title': 'Finance Analyst',
                'department': self.dept_finance,
                'cost_center': self.cc_corp,
                'work_location': self.loc_bkk,
                'manager_key': 'fin_mgr01',
            },
            {
                'username': 'it_emp01',
                'first_name': 'Tanakorn',
                'last_name': 'Wattana',
                'first_name_th': 'ธนากร',
                'last_name_th': 'วัฒนา',
                'email': 'it_emp01@company.com',
                'role': 'employee',
                'employee_id': 'EMP-IE1',
                'job_title': 'Software Engineer',
                'department': self.dept_it,
                'cost_center': self.cc_corp,
                'work_location': self.loc_bkk,
                'manager_key': 'it_mgr01',
            },
            {
                'username': 'it_emp02',
                'first_name': 'Pattara',
                'last_name': 'Khemkhaeng',
                'first_name_th': 'พัทรา',
                'last_name_th': 'เข็มแข็ง',
                'email': 'it_emp02@company.com',
                'role': 'employee',
                'employee_id': 'EMP-IE2',
                'job_title': 'System Administrator',
                'department': self.dept_it,
                'cost_center': self.cc_corp,
                'work_location': self.loc_bkk,
                'manager_key': 'it_mgr01',
            },
            {
                'username': 'hr_emp01',
                'first_name': 'Wipawan',
                'last_name': 'Thamrong',
                'first_name_th': 'วิภาวัน',
                'last_name_th': 'ธำรง',
                'email': 'hr_emp01@company.com',
                'role': 'employee',
                'employee_id': 'EMP-HE1',
                'job_title': 'HR Officer',
                'department': self.dept_hr,
                'cost_center': self.cc_corp,
                'work_location': self.loc_bkk,
                'manager_key': 'hr_mgr01',
            },
            {
                'username': 'ops_emp01',
                'first_name': 'Chaiwat',
                'last_name': 'Boonmak',
                'first_name_th': 'ชัยวัฒน์',
                'last_name_th': 'บุญมาก',
                'email': 'ops_emp01@company.com',
                'role': 'employee',
                'employee_id': 'EMP-OE1',
                'job_title': 'Operations Coordinator',
                'department': self.dept_ops,
                'cost_center': self.cc_ops,
                'work_location': self.loc_sp,
                'manager_key': 'ops_mgr01',
            },
        ]

        for s in specs:
            user, created = User.objects.get_or_create(
                username=s['username'],
                defaults={
                    'first_name': s['first_name'],
                    'last_name': s['last_name'],
                    'email': s['email'],
                    'role': s['role'],
                }
            )
            if created:
                user.set_password(PASSWORD)
                user.save()
                self.stdout.write(f'  + Created user: {s["username"]}')
            else:
                self.stdout.write(f'  ~ Already exists: {s["username"]}')

            mgr_profile = manager_profiles.get(s['manager_key'])
            EmployeeProfile.objects.get_or_create(
                user=user,
                defaults={
                    'employee_id': s['employee_id'],
                    'first_name_en': s['first_name'],
                    'last_name_en': s['last_name'],
                    'first_name_th': s['first_name_th'],
                    'last_name_th': s['last_name_th'],
                    'job_title': s['job_title'],
                    'employment_type': 'full_time',
                    'department': s['department'],
                    'cost_center': s['cost_center'],
                    'work_location': s['work_location'],
                    'direct_manager': mgr_profile,
                }
            )
