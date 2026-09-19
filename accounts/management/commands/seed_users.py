"""
Management command: seed_users
Usage: python manage.py seed_users

สร้าง initial users ทั้งหมดสำหรับ HRMS หลัง database reset
วาง file นี้ที่: accounts/management/commands/seed_users.py
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()
from django.db import transaction


DEFAULT_PASSWORD = "Makara2025!"

USERS = [
    # ── Super Admin ─────────────────────────────────────────────────
    {
        "username": "director01",
        "first_name": "วิชัย",
        "last_name": "พงษ์สุวรรณ",
        "email": "director01@makara.co.th",
        "role": "superadmin",
        "is_staff": True,
        "is_superuser": True,
    },
    # ── Managers ─────────────────────────────────────────────────────
    {
        "username": "fin_mgr01",
        "first_name": "ประสิทธิ์",
        "last_name": "มานะกิจ",
        "email": "fin_mgr01@makara.co.th",
        "role": "manager",
        "department": "Finance",
    },
    {
        "username": "it_mgr01",
        "first_name": "สมชาย",
        "last_name": "ใจดี",
        "email": "it_mgr01@makara.co.th",
        "role": "manager",
        "department": "IT",
    },
    {
        "username": "hr_mgr01",
        "first_name": "สุนีย์",
        "last_name": "รักษ์ดี",
        "email": "hr_mgr01@makara.co.th",
        "role": "hr_manager",
        "department": "HR",
    },
    {
        "username": "ops_mgr01",
        "first_name": "นภาพร",
        "last_name": "เจริญสุข",
        "email": "ops_mgr01@makara.co.th",
        "role": "manager",
        "department": "Operations",
    },
    # ── Employees ─────────────────────────────────────────────────────
    {
        "username": "fin_emp01",
        "first_name": "ศิริพร",
        "last_name": "ดีใจ",
        "email": "fin_emp01@makara.co.th",
        "role": "employee",
        "department": "Finance",
    },
    {
        "username": "it_emp01",
        "first_name": "มาลี",
        "last_name": "ศรีวรรณ",
        "email": "it_emp01@makara.co.th",
        "role": "employee",
        "department": "IT",
    },
    {
        "username": "it_emp02",
        "first_name": "ธนกร",
        "last_name": "บุญมา",
        "email": "it_emp02@makara.co.th",
        "role": "employee",
        "department": "IT",
    },
    {
        "username": "hr_emp01",
        "first_name": "อรทัย",
        "last_name": "แก้วมณี",
        "email": "hr_emp01@makara.co.th",
        "role": "employee",
        "department": "HR",
    },
    {
        "username": "ops_emp01",
        "first_name": "อนุชา",
        "last_name": "พิมพ์ทอง",
        "email": "ops_emp01@makara.co.th",
        "role": "employee",
        "department": "Operations",
    },
]


class Command(BaseCommand):
    help = "Seed initial users for HRMS after database reset"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing users before seeding (except superusers created outside this command)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            usernames = [u["username"] for u in USERS]
            deleted, _ = User.objects.filter(username__in=usernames).delete()
            self.stdout.write(self.style.WARNING(f"  Deleted {deleted} existing users"))

        # Ensure groups exist
        group_names = ["Super Admin", "Manager", "HR Manager", "Employee"]
        groups = {}
        for name in group_names:
            group, created = Group.objects.get_or_create(name=name)
            groups[name] = group
            if created:
                self.stdout.write(f"  Created group: {name}")

        role_to_group = {
            "superadmin": "Super Admin",
            "manager":    "Manager",
            "hr_manager": "HR Manager",
            "employee":   "Employee",
        }

        created_count = 0
        skipped_count = 0

        for data in USERS:
            username = data["username"]

            if User.objects.filter(username=username).exists():
                self.stdout.write(f"  Skipped (exists): {username}")
                skipped_count += 1
                continue

            user = User.objects.create_user(
                username=username,
                password=DEFAULT_PASSWORD,
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", ""),
                email=data.get("email", ""),
                is_staff=data.get("is_staff", False),
                is_superuser=data.get("is_superuser", False),
            )

            # Assign group
            role = data.get("role", "employee")
            group_name = role_to_group.get(role, "Employee")
            user.groups.add(groups[group_name])

            # Try to create Employee profile if model exists
            try:
                from employees.models import Employee
                Employee.objects.get_or_create(
                    user=user,
                    defaults={
                        "first_name": data.get("first_name", ""),
                        "last_name": data.get("last_name", ""),
                        "email": data.get("email", ""),
                        "department": data.get("department", ""),
                        "position": group_name,
                        "is_active": True,
                    },
                )
            except (ImportError, Exception):
                pass  # Employee model ต่างกันแต่ละ project — ข้ามได้

            self.stdout.write(
                self.style.SUCCESS(f"  ✓ Created: {username} ({group_name})")
            )
            created_count += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Done — Created: {created_count}, Skipped: {skipped_count}"
        ))
        self.stdout.write(f"Default password: {DEFAULT_PASSWORD}")
