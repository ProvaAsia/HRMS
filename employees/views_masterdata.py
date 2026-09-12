import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse

from .models import Division, Department, CostCenter, WorkLocation


def _require_super_admin(user):
    return user.is_authenticated and user.role == 'super_admin'


# ─── Overview ────────────────────────────────────────────────
@login_required
def masterdata_overview(request):
    if not _require_super_admin(request.user):
        messages.error(request, 'เฉพาะ Super Admin เท่านั้น')
        return redirect('dashboard')

    tab = request.GET.get('tab', 'division')
    context = {
        'tab': tab,
        'divisions': Division.objects.all().order_by('code'),
        'departments': Department.objects.select_related('division').order_by('code'),
        'cost_centers': CostCenter.objects.all().order_by('code'),
        'work_locations': WorkLocation.objects.all().order_by('name'),
    }
    return render(request, 'employees/masterdata/overview.html', context)


# ─── Division ────────────────────────────────────────────────
@login_required
def division_create(request):
    if not _require_super_admin(request.user):
        return redirect('dashboard')
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        name = request.POST.get('name', '').strip()
        if not code or not name:
            messages.error(request, 'กรุณากรอก Code และ Name')
        elif Division.objects.filter(code=code).exists():
            messages.error(request, f'Code "{code}" มีอยู่แล้ว')
        else:
            Division.objects.create(code=code, name=name)
            messages.success(request, f'เพิ่ม Division "{name}" เรียบร้อย')
    return redirect('masterdata_overview')


@login_required
def division_edit(request, pk):
    if not _require_super_admin(request.user):
        return redirect('dashboard')
    obj = get_object_or_404(Division, pk=pk)
    if request.method == 'POST':
        obj.code = request.POST.get('code', '').strip()
        obj.name = request.POST.get('name', '').strip()
        obj.save()
        messages.success(request, 'แก้ไข Division เรียบร้อย')
        return redirect('masterdata_overview')
    return render(request, 'employees/masterdata/edit_form.html', {
        'obj': obj, 'type': 'division', 'fields': [
            {'name': 'code', 'label': 'Code', 'value': obj.code},
            {'name': 'name', 'label': 'Name', 'value': obj.name},
        ]
    })


@login_required
def division_delete(request, pk):
    if not _require_super_admin(request.user):
        return redirect('dashboard')
    obj = get_object_or_404(Division, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'ลบ Division เรียบร้อย')
    return redirect('masterdata_overview')


# ─── Department ──────────────────────────────────────────────
@login_required
def department_create(request):
    if not _require_super_admin(request.user):
        return redirect('dashboard')
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        name = request.POST.get('name', '').strip()
        division_id = request.POST.get('division') or None
        if not code or not name:
            messages.error(request, 'กรุณากรอก Code และ Name')
        elif Department.objects.filter(code=code).exists():
            messages.error(request, f'Code "{code}" มีอยู่แล้ว')
        else:
            Department.objects.create(code=code, name=name, division_id=division_id)
            messages.success(request, f'เพิ่ม Department "{name}" เรียบร้อย')
    return redirect('/employees/masterdata/?tab=department')


@login_required
def department_edit(request, pk):
    if not _require_super_admin(request.user):
        return redirect('dashboard')
    obj = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        obj.code = request.POST.get('code', '').strip()
        obj.name = request.POST.get('name', '').strip()
        obj.division_id = request.POST.get('division') or None
        obj.save()
        messages.success(request, 'แก้ไข Department เรียบร้อย')
        return redirect('masterdata_overview')
    return render(request, 'employees/masterdata/edit_form.html', {
        'obj': obj, 'type': 'department',
        'divisions': Division.objects.all().order_by('code'),
        'fields': [
            {'name': 'code', 'label': 'Code', 'value': obj.code},
            {'name': 'name', 'label': 'Name', 'value': obj.name},
        ]
    })


@login_required
def department_delete(request, pk):
    if not _require_super_admin(request.user):
        return redirect('dashboard')
    obj = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'ลบ Department เรียบร้อย')
    return redirect('masterdata_overview')


# ─── Cost Center ─────────────────────────────────────────────
@login_required
def costcenter_create(request):
    if not _require_super_admin(request.user):
        return redirect('dashboard')
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        name = request.POST.get('name', '').strip()
        if not code or not name:
            messages.error(request, 'กรุณากรอก Code และ Name')
        elif CostCenter.objects.filter(code=code).exists():
            messages.error(request, f'Code "{code}" มีอยู่แล้ว')
        else:
            CostCenter.objects.create(code=code, name=name)
            messages.success(request, f'เพิ่ม Cost Center "{name}" เรียบร้อย')
    return redirect('/employees/masterdata/?tab=costcenter')


@login_required
def costcenter_edit(request, pk):
    if not _require_super_admin(request.user):
        return redirect('dashboard')
    obj = get_object_or_404(CostCenter, pk=pk)
    if request.method == 'POST':
        obj.code = request.POST.get('code', '').strip()
        obj.name = request.POST.get('name', '').strip()
        obj.save()
        messages.success(request, 'แก้ไข Cost Center เรียบร้อย')
        return redirect('masterdata_overview')
    return render(request, 'employees/masterdata/edit_form.html', {
        'obj': obj, 'type': 'costcenter', 'fields': [
            {'name': 'code', 'label': 'Code', 'value': obj.code},
            {'name': 'name', 'label': 'Name', 'value': obj.name},
        ]
    })


@login_required
def costcenter_delete(request, pk):
    if not _require_super_admin(request.user):
        return redirect('dashboard')
    obj = get_object_or_404(CostCenter, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'ลบ Cost Center เรียบร้อย')
    return redirect('masterdata_overview')


# ─── Work Location ───────────────────────────────────────────
@login_required
def worklocation_create(request):
    if not _require_super_admin(request.user):
        return redirect('dashboard')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        address = request.POST.get('address', '').strip()
        if not name:
            messages.error(request, 'กรุณากรอก Name')
        else:
            WorkLocation.objects.create(name=name, address=address)
            messages.success(request, f'เพิ่ม Work Location "{name}" เรียบร้อย')
    return redirect('/employees/masterdata/?tab=worklocation')


@login_required
def worklocation_edit(request, pk):
    if not _require_super_admin(request.user):
        return redirect('dashboard')
    obj = get_object_or_404(WorkLocation, pk=pk)
    if request.method == 'POST':
        obj.name = request.POST.get('name', '').strip()
        obj.address = request.POST.get('address', '').strip()
        obj.save()
        messages.success(request, 'แก้ไข Work Location เรียบร้อย')
        return redirect('masterdata_overview')
    return render(request, 'employees/masterdata/edit_form.html', {
        'obj': obj, 'type': 'worklocation', 'fields': [
            {'name': 'name', 'label': 'Name', 'value': obj.name},
            {'name': 'address', 'label': 'Address', 'value': obj.address},
        ]
    })


@login_required
def worklocation_delete(request, pk):
    if not _require_super_admin(request.user):
        return redirect('dashboard')
    obj = get_object_or_404(WorkLocation, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'ลบ Work Location เรียบร้อย')
    return redirect('masterdata_overview')


# ─── Excel Template Download ─────────────────────────────────
@login_required
def masterdata_excel_template(request):
    if not _require_super_admin(request.user):
        return redirect('dashboard')

    wb = openpyxl.Workbook()

    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(fill_type='solid', fgColor='152057')

    def make_sheet(wb, title, headers, examples):
        ws = wb.create_sheet(title=title)
        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
            ws.column_dimensions[cell.column_letter].width = 24
        for row_idx, row in enumerate(examples, 2):
            for col_idx, val in enumerate(row, 1):
                ws.cell(row=row_idx, column=col_idx, value=val)
        return ws

    # Remove default sheet
    wb.remove(wb.active)

    make_sheet(wb, 'Division',
        ['code', 'name'],
        [['DIV001', 'Operations'], ['DIV002', 'Finance']])

    make_sheet(wb, 'Department',
        ['code', 'name', 'division_code'],
        [['DEPT001', 'Accounting', 'DIV002'], ['DEPT002', 'Logistics', 'DIV001']])

    make_sheet(wb, 'CostCenter',
        ['code', 'name'],
        [['CC001', 'Head Office'], ['CC002', 'Warehouse']])

    make_sheet(wb, 'WorkLocation',
        ['name', 'address'],
        [['Bangkok HQ', '123 Sathorn Rd, Bangkok'],
         ['Samut Prakan', '456 Factory Rd, SP']])

    # Instructions sheet
    ws_info = wb.create_sheet(title='Instructions', index=0)
    ws_info['A1'] = 'HRMS Master Data Upload Template'
    ws_info['A1'].font = Font(bold=True, size=14)
    instructions = [
        ('', ''),
        ('Sheet', 'Description'),
        ('Division', 'code (unique), name'),
        ('Department', 'code (unique), name, division_code (must match Division.code)'),
        ('CostCenter', 'code (unique), name'),
        ('WorkLocation', 'name, address (optional)'),
        ('', ''),
        ('Note', 'Row 1 = headers (do not change). Data starts row 2.'),
        ('Note', 'Existing records with same code will be UPDATED (not duplicated).'),
    ]
    for r, (a, b) in enumerate(instructions, 2):
        ws_info.cell(row=r, column=1, value=a).font = Font(bold=True) if a == 'Sheet' else Font()
        ws_info.cell(row=r, column=2, value=b)
    ws_info.column_dimensions['A'].width = 20
    ws_info.column_dimensions['B'].width = 60

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="masterdata_template.xlsx"'
    return response


# ─── Excel Upload ─────────────────────────────────────────────
@login_required
def masterdata_excel_upload(request):
    if not _require_super_admin(request.user):
        return redirect('dashboard')

    if request.method != 'POST':
        return redirect('masterdata_overview')

    file = request.FILES.get('excel_file')
    if not file:
        messages.error(request, 'กรุณาเลือกไฟล์ Excel')
        return redirect('masterdata_overview')

    try:
        wb = openpyxl.load_workbook(file, data_only=True)
    except Exception:
        messages.error(request, 'ไฟล์ไม่ถูกต้อง กรุณาใช้ไฟล์ .xlsx')
        return redirect('masterdata_overview')

    results = []
    errors = []

    # Division
    if 'Division' in wb.sheetnames:
        ws = wb['Division']
        added = updated = 0
        for row in ws.iter_rows(min_row=2, values_only=True):
            code, name = (str(row[0]).strip() if row[0] else ''), (str(row[1]).strip() if row[1] else '')
            if not code or not name:
                continue
            obj, created = Division.objects.update_or_create(code=code, defaults={'name': name})
            if created: added += 1
            else: updated += 1
        results.append(f'Division: เพิ่ม {added}, อัปเดต {updated}')

    # Department
    if 'Department' in wb.sheetnames:
        ws = wb['Department']
        added = updated = skipped = 0
        for row in ws.iter_rows(min_row=2, values_only=True):
            code = str(row[0]).strip() if row[0] else ''
            name = str(row[1]).strip() if row[1] else ''
            div_code = str(row[2]).strip() if len(row) > 2 and row[2] else ''
            if not code or not name:
                continue
            division = Division.objects.filter(code=div_code).first() if div_code else None
            obj, created = Department.objects.update_or_create(
                code=code, defaults={'name': name, 'division': division}
            )
            if created: added += 1
            else: updated += 1
        results.append(f'Department: เพิ่ม {added}, อัปเดต {updated}')

    # CostCenter
    if 'CostCenter' in wb.sheetnames:
        ws = wb['CostCenter']
        added = updated = 0
        for row in ws.iter_rows(min_row=2, values_only=True):
            code = str(row[0]).strip() if row[0] else ''
            name = str(row[1]).strip() if row[1] else ''
            if not code or not name:
                continue
            obj, created = CostCenter.objects.update_or_create(code=code, defaults={'name': name})
            if created: added += 1
            else: updated += 1
        results.append(f'Cost Center: เพิ่ม {added}, อัปเดต {updated}')

    # WorkLocation
    if 'WorkLocation' in wb.sheetnames:
        ws = wb['WorkLocation']
        added = 0
        for row in ws.iter_rows(min_row=2, values_only=True):
            name = str(row[0]).strip() if row[0] else ''
            address = str(row[1]).strip() if len(row) > 1 and row[1] else ''
            if not name:
                continue
            WorkLocation.objects.get_or_create(name=name, defaults={'address': address})
            added += 1
        results.append(f'Work Location: นำเข้า {added}')

    if results:
        messages.success(request, 'นำเข้าข้อมูลสำเร็จ — ' + ' | '.join(results))
    if errors:
        for e in errors:
            messages.error(request, e)

    return redirect('masterdata_overview')
