"""
refresh_leave_balances — คำนวณวันลาตามอายุงานสำหรับปีที่กำหนด

สูตร (ต่อประเภทลาที่มี annual_accrual > 0):
    entitled = default_days + years_of_service * annual_accrual
    ถ้า max_days > 0: entitled = min(entitled, max_days)

ตัวอย่างใช้งาน:
    /opt/venv/bin/python manage.py refresh_leave_balances --year 2026
    /opt/venv/bin/python manage.py refresh_leave_balances --year 2026 --dry-run
    /opt/venv/bin/python manage.py refresh_leave_balances --year 2026 --employee EMP001
"""

from datetime import date
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from leave.models import LeaveType, LeaveBalance

User = get_user_model()


def _years_of_service(join_date, as_of=None):
    if not join_date:
        return 0
    ref = as_of or date.today()
    return (ref - join_date).days // 365


def calc_entitled(leave_type, years):
    entitled = leave_type.default_days + years * leave_type.annual_accrual
    if leave_type.max_days > 0:
        entitled = min(entitled, leave_type.max_days)
    return entitled


class Command(BaseCommand):
    help = 'คำนวณ/อัปเดต LeaveBalance ตามอายุงานของพนักงาน'

    def add_arguments(self, parser):
        parser.add_argument('--year', type=int, default=date.today().year)
        parser.add_argument('--employee', type=str, default=None)
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        year = options['year']
        emp_filter = options['employee']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('=== DRY-RUN ==='))

        leave_types = list(LeaveType.objects.all())

        users_qs = User.objects.filter(is_active=True).select_related('employee_profile')
        if emp_filter:
            users_qs = users_qs.filter(employee_profile__employee_id=emp_filter)

        updated = created = skipped = 0

        for user in users_qs:
            profile = getattr(user, 'employee_profile', None)
            if not profile:
                skipped += 1
                continue

            years = _years_of_service(profile.join_date)
            label = f'{profile.employee_id} / {user.username} ({years} ปี)'

            for lt in leave_types:
                if lt.is_lwp:
                    continue
                entitled = calc_entitled(lt, years) if lt.annual_accrual > 0 else lt.default_days

                try:
                    bal = LeaveBalance.objects.get(employee=user, leave_type=lt, year=year)
                    old = bal.entitled_days
                    if old != entitled:
                        self.stdout.write(f'  {label} | {lt.name}: {old} → {entitled}')
                        if not dry_run:
                            bal.entitled_days = entitled
                            bal.save(update_fields=['entitled_days'])
                        updated += 1
                except LeaveBalance.DoesNotExist:
                    self.stdout.write(f'  {label} | {lt.name}: สร้างใหม่ {entitled} วัน')
                    if not dry_run:
                        LeaveBalance.objects.create(
                            employee=user, leave_type=lt, year=year,
                            entitled_days=entitled, used_days=0,
                        )
                    created += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nเสร็จ: {updated} update, {created} create, {skipped} skip'
        ))
