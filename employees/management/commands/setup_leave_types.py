from django.core.management.base import BaseCommand
from leave.models import LeaveType


class Command(BaseCommand):
    help = 'Create default leave types'

    def handle(self, *args, **options):
        types = [
            {
                'name': 'Annual Leave',
                'name_th': 'ลาพักร้อน',
                'default_days': 10,
                'days_per_year': 10,
                'annual_accrual': 1,
                'requires_advance_days': 3,
                'carry_over': True,
                'is_paid': True,
            },
            {
                'name': 'Personal Leave',
                'name_th': 'ลากิจ',
                'default_days': 3,
                'days_per_year': 3,
                'annual_accrual': 0,
                'requires_advance_days': 1,
                'carry_over': False,
                'is_paid': True,
            },
            {
                'name': 'Sick Leave',
                'name_th': 'ลาป่วย',
                'default_days': 30,
                'days_per_year': 30,
                'annual_accrual': 0,
                'requires_advance_days': 0,
                'carry_over': False,
                'is_paid': True,
            },
        ]
        for t in types:
            obj, created = LeaveType.objects.get_or_create(
                name=t['name'], defaults=t
            )
            status = 'created' if created else 'already exists'
            self.stdout.write(f"  {'✓' if created else '–'} {t['name']} ({status})")
        self.stdout.write(self.style.SUCCESS('Leave types ready.'))
