from django.urls import path
from . import views

urlpatterns = [
    path('', views.attendance_dashboard, name='attendance_dashboard'),
    path('checkin/', views.attendance_checkin, name='attendance_checkin'),
    path('my-report/', views.attendance_my_report, name='attendance_my_report'),
    path('list/', views.attendance_list, name='attendance_list'),
    path('import/', views.import_excel, name='attendance_import_excel'),
    path('<int:pk>/edit/', views.attendance_edit, name='attendance_edit'),
]
