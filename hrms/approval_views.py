"""
Token-based email approval/rejection view.
Handles leave, OT, and recruitment (candidate) approvals via signed links.
"""
from django.shortcuts import render
from django.utils import timezone
from django.core.signing import BadSignature, SignatureExpired
from django.http import Http404

from hrms.email_utils import parse_approval_token


def handle_approval(request, token: str):
    """GET: verify the signed token and apply the action."""
    try:
        model_type, pk, action = parse_approval_token(token)
    except SignatureExpired:
        return render(request, 'emails/approval_result.html', {
            'success': False,
            'message': 'ลิงก์หมดอายุแล้ว (72 ชั่วโมง) — กรุณาเข้าสู่ระบบเพื่อดำเนินการด้วยตนเอง',
        })
    except (BadSignature, ValueError, TypeError):
        return render(request, 'emails/approval_result.html', {
            'success': False,
            'message': 'ลิงก์ไม่ถูกต้องหรือถูกดัดแปลง',
        })

    if action not in ('approve', 'reject'):
        raise Http404

    action_label = 'อนุมัติ' if action == 'approve' else 'ปฏิเสธ'

    if model_type == 'leave':
        return _handle_leave(request, pk, action, action_label)
    elif model_type == 'ot':
        return _handle_ot(request, pk, action, action_label)
    elif model_type == 'candidate':
        return _handle_candidate(request, pk, action, action_label)
    else:
        raise Http404


# ── Leave ────────────────────────────────────────────────────────────────────

def _handle_leave(request, pk: int, action: str, action_label: str):
    from leave.models import LeaveRequest
    try:
        leave = LeaveRequest.objects.select_related('employee', 'leave_type').get(pk=pk)
    except LeaveRequest.DoesNotExist:
        return render(request, 'emails/approval_result.html', {
            'success': False,
            'message': 'ไม่พบคำขอลาในระบบ',
        })

    if leave.status != 'pending':
        return _already_processed(request, 'ลา', leave.get_status_display(), leave.employee.get_full_name())

    now = timezone.now()
    leave.status = 'approved' if action == 'approve' else 'rejected'
    leave.approved_at = now
    leave.save(update_fields=['status', 'approved_at'])

    detail = (
        f"{leave.employee.get_full_name()} ขอลา {leave.leave_type.name} "
        f"วันที่ {leave.start_date} – {leave.end_date} ({leave.days} วัน)"
    )
    return render(request, 'emails/approval_result.html', {
        'success': True,
        'action_label': action_label,
        'detail': detail,
    })


# ── OT ──────────────────────────────────────────────────────────────────────

def _handle_ot(request, pk: int, action: str, action_label: str):
    from overtime.models import OTRequest
    try:
        ot = OTRequest.objects.select_related('employee').get(pk=pk)
    except OTRequest.DoesNotExist:
        return render(request, 'emails/approval_result.html', {
            'success': False,
            'message': 'ไม่พบคำขอ OT ในระบบ',
        })

    if ot.status != 'pending':
        return _already_processed(request, 'OT', ot.get_status_display(), ot.employee.get_full_name())

    now = timezone.now()
    ot.status = 'approved' if action == 'approve' else 'rejected'
    ot.reviewed_at = now
    ot.save(update_fields=['status', 'reviewed_at'])

    detail = (
        f"{ot.employee.get_full_name()} ขอทำ OT วันที่ {ot.date} "
        f"{ot.start_time:%H:%M}–{ot.end_time:%H:%M} ({ot.hours} ชั่วโมง)"
    )
    return render(request, 'emails/approval_result.html', {
        'success': True,
        'action_label': action_label,
        'detail': detail,
    })


# ── Candidate (Recruitment) ──────────────────────────────────────────────────

def _handle_candidate(request, pk: int, action: str, action_label: str):
    from recruitment.models import Candidate
    try:
        candidate = Candidate.objects.select_related('job_position').get(pk=pk)
    except Candidate.DoesNotExist:
        return render(request, 'emails/approval_result.html', {
            'success': False,
            'message': 'ไม่พบข้อมูลผู้สมัครในระบบ',
        })

    if candidate.status not in ('applied', 'screening'):
        return _already_processed(request, 'สมัครงาน', candidate.get_status_display(),
                                  f"{candidate.first_name} {candidate.last_name}")

    if action == 'approve':
        next_status = {'applied': 'screening', 'screening': 'interview'}.get(candidate.status, candidate.status)
        candidate.status = next_status
    else:
        candidate.status = 'rejected'
    candidate.save(update_fields=['status'])

    detail = (
        f"{candidate.first_name} {candidate.last_name} "
        f"ตำแหน่ง {candidate.job_position.title} → {candidate.get_status_display()}"
    )
    return render(request, 'emails/approval_result.html', {
        'success': True,
        'action_label': action_label,
        'detail': detail,
    })


# ── Helper ───────────────────────────────────────────────────────────────────

def _already_processed(request, req_type: str, status_display: str, name: str):
    return render(request, 'emails/approval_result.html', {
        'success': False,
        'message': (
            f"คำขอ{req_type}ของ {name} ได้รับการดำเนินการไปแล้ว (สถานะ: {status_display})"
        ),
    })
