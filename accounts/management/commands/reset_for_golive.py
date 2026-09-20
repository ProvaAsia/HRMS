"""
python manage.py reset_for_golive

ลบ user ทั้งหมดและ EmployeeProfile ที่เชื่อมอยู่
แล้วสร้าง admin / admin ใหม่สะอาด พร้อม go-live
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'ลบ user ทั้งหมดแล้วสร้าง admin/admin ใหม่เพื่อ go-live'

    def add_arguments(self, parser):
        parser.add_argument(
            '--yes',
            action='store_true',
            help='ข้ามขั้นตอนยืนยัน (ใช้ใน script อัตโนมัติ)',
        )

    def handle(self, *args, **options):
        total = User.objects.count()
        self.stdout.write(f'\nพบ user ทั้งหมด {total} คน:')
        for u in User.objects.all().order_by('role', 'username'):
            self.stdout.write(f'  [{u.role:<10}] {u.username}')

        self.stdout.write('')

        if not options['yes']:
            confirm = input('ยืนยันลบทั้งหมดและสร้าง admin/admin ใหม่? (yes/no): ')
            if confirm.strip().lower() != 'yes':
                self.stdout.write(self.style.WARNING('ยกเลิก — ไม่มีการเปลี่ยนแปลง'))
                return

        with transaction.atomic():
            # ลบ EmployeeProfile ก่อน (เพราะ CASCADE จะลบด้วย แต่ explicit ปลอดภัยกว่า)
            try:
                from employees.models import EmployeeProfile
                deleted_profiles = EmployeeProfile.objects.count()
                EmployeeProfile.objects.all().delete()
                self.stdout.write(f'  ลบ EmployeeProfile {deleted_profiles} รายการ')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  EmployeeProfile: {e}'))

            # ลบ user ทั้งหมด
            deleted_users = User.objects.count()
            User.objects.all().delete()
            self.stdout.write(f'  ลบ User {deleted_users} รายการ')

            # สร้าง admin ใหม่
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@local.dev',
                password='admin',
            )
            # set role ถ้ามี field นี้
            if hasattr(admin, 'role'):
                admin.role = 'admin'
                admin.save(update_fields=['role'])

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('✓ สร้าง admin/admin เรียบร้อยแล้ว'))
            self.stdout.write(self.style.SUCCESS('  username : admin'))
            self.stdout.write(self.style.SUCCESS('  password : admin'))
            self.stdout.write('')
