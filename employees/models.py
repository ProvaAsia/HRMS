from django.db import models
from django.conf import settings


class Division(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    division = models.ForeignKey(Division, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name


class CostCenter(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class WorkLocation(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name


class EmployeeProfile(models.Model):
    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('contract', 'Contract'),
        ('intern', 'Intern'),
        ('probation', 'Probation'),
    ]

    TITLE_CHOICES = [
        ('mr', 'นาย'),
        ('mrs', 'นาง'),
        ('ms', 'นางสาว'),
        ('dr', 'ดร.'),
        ('other', 'อื่นๆ'),
    ]

    GENDER_CHOICES = [
        ('male', 'ชาย'),
        ('female', 'หญิง'),
        ('other', 'ไม่ระบุ'),
    ]

    MARITAL_STATUS_CHOICES = [
        ('single', 'โสด'),
        ('married', 'สมรส'),
        ('divorced', 'หย่าร้าง'),
        ('widowed', 'หม้าย'),
    ]

    EMPLOYEE_STATUS_CHOICES = [
        ('active', 'ทำงานอยู่'),
        ('probation', 'ทดลองงาน'),
        ('resigned', 'ลาออก'),
        ('terminated', 'ถูกเลิกจ้าง'),
        ('retired', 'เกษียณ'),
    ]

    BANK_CHOICES = [
        ('kbank', 'กสิกรไทย (KBank)'),
        ('scb', 'ไทยพาณิชย์ (SCB)'),
        ('bbl', 'กรุงเทพ (BBL)'),
        ('ktb', 'กรุงไทย (KTB)'),
        ('bay', 'กรุงศรีอยุธยา (BAY)'),
        ('tmb', 'ทหารไทย (TTB)'),
        ('gsb', 'ออมสิน (GSB)'),
        ('baac', 'ธกส. (BAAC)'),
        ('other', 'อื่นๆ'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee_profile'
    )

    # Personal Identity
    employee_id = models.CharField(max_length=20, unique=True)
    title_prefix = models.CharField(max_length=10, choices=TITLE_CHOICES, blank=True)
    first_name_th = models.CharField(max_length=100, blank=True)
    last_name_th = models.CharField(max_length=100, blank=True)
    first_name_en = models.CharField(max_length=100, blank=True)
    last_name_en = models.CharField(max_length=100, blank=True)
    nickname = models.CharField(max_length=50, blank=True)
    national_id = models.CharField(max_length=13, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, blank=True)

    # Contact
    company_email = models.EmailField(blank=True)
    personal_email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    registered_address = models.TextField(blank=True)
    current_address = models.TextField(blank=True)
    province = models.CharField(max_length=100, blank=True)

    # Employment
    employee_status = models.CharField(
        max_length=20, choices=EMPLOYEE_STATUS_CHOICES, default='active'
    )
    join_date = models.DateField(null=True, blank=True)
    probation_end_date = models.DateField(null=True, blank=True)
    confirmed_date = models.DateField(null=True, blank=True)
    employment_type = models.CharField(
        max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, default='full_time'
    )

    # Position & Org
    job_title = models.CharField(max_length=100, blank=True)
    job_level = models.CharField(max_length=50, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    division = models.ForeignKey(Division, on_delete=models.SET_NULL, null=True, blank=True)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True)
    work_location = models.ForeignKey(WorkLocation, on_delete=models.SET_NULL, null=True, blank=True)

    # Reporting
    direct_manager = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='direct_reports'
    )
    dotted_line_manager = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='dotted_reports'
    )

    # Compensation (sensitive — visible to admin/HR only in views)
    salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    bank_name = models.CharField(max_length=20, choices=BANK_CHOICES, blank=True)
    bank_account = models.CharField(max_length=20, blank=True)

    # Photo
    photo = models.ImageField(upload_to='employee_photos/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee_id} - {self.first_name_en} {self.last_name_en}"

    def full_name_en(self):
        return f"{self.first_name_en} {self.last_name_en}".strip()

    def full_name_th(self):
        return f"{self.first_name_th} {self.last_name_th}".strip()

    def years_of_service(self):
        if not self.join_date:
            return 0
        from datetime import date
        delta = date.today() - self.join_date
        return delta.days // 365

    def age(self):
        if not self.date_of_birth:
            return None
        from datetime import date
        delta = date.today() - self.date_of_birth
        return delta.days // 365

    def get_status_color(self):
        colors = {
            'active': 'green',
            'probation': 'yellow',
            'resigned': 'red',
            'terminated': 'red',
            'retired': 'gray',
        }
        return colors.get(self.employee_status, 'gray')


class EmergencyContact(models.Model):
    employee = models.ForeignKey(
        EmployeeProfile, on_delete=models.CASCADE, related_name='emergency_contacts'
    )
    name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.name} ({self.relationship})"


class Dependent(models.Model):
    RELATIONSHIP_CHOICES = [
        ('spouse', 'คู่สมรส / Spouse'),
        ('child', 'บุตร / Child'),
        ('parent', 'บิดา-มารดา / Parent'),
        ('other', 'อื่นๆ / Other'),
    ]

    employee = models.ForeignKey(
        EmployeeProfile, on_delete=models.CASCADE, related_name='dependents'
    )
    name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    national_id = models.CharField(max_length=13, blank=True)
    is_tax_deductible = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.get_relationship_display()})"


class EmployeeDocument(models.Model):
    DOC_TYPE_CHOICES = [
        ('id_card', 'บัตรประชาชน'),
        ('passport', 'หนังสือเดินทาง'),
        ('driver_license', 'ใบอนุญาตขับขี่'),
        ('medical_cert', 'ใบรับรองแพทย์'),
        ('education_cert', 'วุฒิการศึกษา'),
        ('transcript', 'ผลการเรียน'),
        ('work_permit', 'ใบอนุญาตทำงาน'),
        ('other', 'อื่นๆ'),
    ]

    STATUS_CHOICES = [
        ('active', 'ปกติ'),
        ('expired', 'หมดอายุ'),
        ('pending', 'รอดำเนินการ'),
    ]

    employee = models.ForeignKey(
        EmployeeProfile, on_delete=models.CASCADE, related_name='employee_documents'
    )
    doc_type = models.CharField(max_length=30, choices=DOC_TYPE_CHOICES)
    doc_name = models.CharField(max_length=200, blank=True)
    doc_number = models.CharField(max_length=50, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    file = models.FileField(upload_to='employee_documents/%Y/', null=True, blank=True)
    note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-issue_date']

    def __str__(self):
        return f"{self.employee.employee_id} — {self.get_doc_type_display()}"

    def is_expired(self):
        if not self.expiry_date:
            return False
        from datetime import date
        return self.expiry_date < date.today()
