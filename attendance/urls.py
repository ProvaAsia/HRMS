from django.urls import path
from . import views

urlpatterns = [
    path('', views.attendance_dashboard, name='attendance_dashboard'),
    path('checkin/', views.attendance_checkin, name='attendance_checkin'),
    path('my-report/', views.attendance_my_report, name='attendance_my_report'),
    path('list/', views.attendance_list, name='attendance_list'),
    path('import/', views.import_excel, name='attendance_import_excel'),
    path('<int:pk>/edit/', views.attendance_edit, name='attendance_edit'),

    # Manager team timesheet
    path('team/', views.team_timesheet, name='team_timesheet'),

    # Correction requests
    path('correction/new/', views.correction_request_create, name='correction_request_create'),
    path('correction/new/<int:record_pk>/', views.correction_request_create, name='correction_request_create_for_record'),
    path('correction/mine/', views.my_correction_requests, name='my_correction_requests'),
    path('correction/team/', views.team_correction_requests, name='team_correction_requests'),
    path('correction/<int:pk>/review/', views.correction_request_review, name='correction_request_review'),

    # Payroll summary
    path('payroll/', views.payroll_summary, name='payroll_summary'),
]
